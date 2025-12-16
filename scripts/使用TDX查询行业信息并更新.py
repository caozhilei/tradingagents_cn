#!/usr/bin/env python3
"""
使用TDX接口查询已有股票数据所属行业，并更新到数据库

功能：
1. 查询 stock_basic_info 集合中已有股票数据（或缺少行业信息的股票）
2. 使用 TDX 接口尝试获取行业信息
3. 如果TDX无法提供行业信息，依次使用AKShare和Tushare作为备用方案
4. 更新数据库中的 industry 和 area 字段

数据源优先级：
  TDX -> AKShare -> Tushare

使用方法：
    python scripts/使用TDX查询行业信息并更新.py
    python scripts/使用TDX查询行业信息并更新.py --limit 100  # 只处理前100只股票
    python scripts/使用TDX查询行业信息并更新.py --source tdx  # 只处理TDX数据源的股票
    python scripts/使用TDX查询行业信息并更新.py --missing-only  # 只处理缺少行业信息的股票
    python scripts/使用TDX查询行业信息并更新.py --no-tushare-fallback  # 不使用Tushare备用方案
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
import argparse

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import pandas as pd

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# 在脚本开始时设置代理环境变量（从.env文件读取）
def setup_proxy_from_env():
    """从.env文件读取代理配置并设置到环境变量"""
    env_file = project_root / ".env"
    if env_file.exists():
        try:
            import re
            with open(env_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 提取HTTP_PROXY
            http_match = re.search(r'HTTP_PROXY=(.+)', content, re.MULTILINE)
            if http_match:
                http_proxy = http_match.group(1).strip().strip('"\'')
                os.environ['HTTP_PROXY'] = http_proxy
                os.environ['http_proxy'] = http_proxy
            
            # 提取HTTPS_PROXY
            https_match = re.search(r'HTTPS_PROXY=(.+)', content, re.MULTILINE)
            if https_match:
                https_proxy = https_match.group(1).strip().strip('"\'')
                os.environ['HTTPS_PROXY'] = https_proxy
                os.environ['https_proxy'] = https_proxy
            
            # 提取NO_PROXY
            no_proxy_match = re.search(r'NO_PROXY=(.+)', content, re.MULTILINE)
            if no_proxy_match:
                no_proxy = no_proxy_match.group(1).strip().strip('"\'')
                os.environ['NO_PROXY'] = no_proxy
                os.environ['no_proxy'] = no_proxy
                logger.debug(f"🔧 已设置NO_PROXY: {no_proxy}")
        except Exception as e:
            logger.debug(f"⚠️  读取代理配置失败: {e}")

# 设置代理环境变量
setup_proxy_from_env()

# 尝试导入配置，如果失败则使用环境变量
try:
    from app.core.config import settings
    MONGO_URI = settings.MONGO_URI
    MONGO_DB = settings.MONGO_DB
    # 如果MONGO_URI包含'mongodb'主机名（Docker容器名），替换为'localhost'
    if 'mongodb://' in MONGO_URI and '@mongodb:' in MONGO_URI:
        MONGO_URI = MONGO_URI.replace('@mongodb:', '@localhost:')
        logger.debug(f"🔧 已将MongoDB主机名从'mongodb'改为'localhost'")
except Exception as e:
    logger.warning(f"⚠️ 无法加载配置，使用环境变量: {e}")
    # 从环境变量读取MongoDB配置
    # 注意：如果从环境变量读取到的是'mongodb'（Docker容器名），需要改为'localhost'
    raw_host = os.getenv('MONGODB_HOST', 'localhost')
    MONGODB_HOST = 'localhost' if raw_host == 'mongodb' else raw_host
    MONGODB_PORT = int(os.getenv('MONGODB_PORT', '27017'))
    MONGODB_USERNAME = os.getenv('MONGODB_USERNAME') or os.getenv('TRADINGAGENTS_MONGODB_USERNAME', 'admin')
    MONGODB_PASSWORD = os.getenv('MONGODB_PASSWORD') or os.getenv('TRADINGAGENTS_MONGODB_PASSWORD', 'tradingagents123')
    MONGODB_DATABASE = os.getenv('MONGODB_DATABASE', 'tradingagents')
    MONGODB_AUTH_SOURCE = os.getenv('MONGODB_AUTH_SOURCE', 'admin')
    
    # 构建MongoDB URI
    # 确保主机名正确（将Docker容器名'mongodb'替换为'localhost'）
    if MONGODB_HOST == 'mongodb':
        MONGODB_HOST = 'localhost'
    
    # 确保主机名正确（将Docker容器名'mongodb'替换为'localhost'）
    final_host = 'localhost' if MONGODB_HOST == 'mongodb' else MONGODB_HOST
    
    if MONGODB_USERNAME and MONGODB_PASSWORD:
        MONGO_URI = f"mongodb://{MONGODB_USERNAME}:{MONGODB_PASSWORD}@{final_host}:{MONGODB_PORT}/{MONGODB_DATABASE}?authSource={MONGODB_AUTH_SOURCE}"
    else:
        MONGO_URI = f"mongodb://{final_host}:{MONGODB_PORT}/{MONGODB_DATABASE}"
    MONGO_DB = MONGODB_DATABASE


async def get_stock_industry_from_tdx(code: str) -> Dict[str, str]:
    """
    使用 TDX 接口尝试获取股票的行业信息
    
    Args:
        code: 6位股票代码
        
    Returns:
        包含 industry 和 area 的字典
    """
    try:
        # 忽略编码错误，避免.env文件编码问题影响TDX连接
        import warnings
        warnings.filterwarnings('ignore', category=UnicodeDecodeError)
        
        from data.tdx_utils import get_tdx_provider
        
        provider = get_tdx_provider()
        if not provider:
            logger.warning(f"⚠️ 无法获取TDX提供器: {code}")
            return {"industry": "未知", "area": "未知", "source": "tdx_failed"}
        
        if not provider.connected:
            logger.info(f"🔌 尝试连接TDX服务器...")
            if not provider.connect():
                logger.warning(f"⚠️ TDX连接失败: {code}")
                return {"industry": "未知", "area": "未知", "source": "tdx_failed"}
        
        # TDX API主要提供实时行情和历史数据，不直接提供行业信息
        # 尝试从股票列表中获取信息（如果包含行业信息）
        market = 0 if code.startswith(('000', '002', '003', '300')) else 1
        
        # 尝试获取股票列表（仅深圳市场支持）
        if market == 0:  # 深圳市场
            try:
                stock_list = provider.api.get_security_list(market, 0)
                if stock_list:
                    for stock_info in stock_list:
                        if stock_info.get('code') == code:
                            # TDX的get_security_list通常只返回code和name，不包含行业信息
                            # 但我们可以获取到名称等信息
                            name = stock_info.get('name', '')
                            logger.debug(f"📊 TDX获取到股票信息: {code} - {name}")
                            # TDX无法直接提供行业信息，返回未知
                            return {
                                "industry": "未知",
                                "area": "未知",
                                "source": "tdx_no_industry",
                                "name": name
                            }
            except Exception as e:
                logger.debug(f"⚠️ TDX获取股票列表失败: {e}")
        
        # TDX无法直接提供行业信息
        return {"industry": "未知", "area": "未知", "source": "tdx_no_industry"}
        
    except Exception as e:
        logger.error(f"❌ TDX获取 {code} 行业信息失败: {e}")
        return {"industry": "未知", "area": "未知", "source": "tdx_error"}


async def get_stock_industry_from_akshare(code: str) -> Dict[str, str]:
    """
    使用 AKShare 作为备用方案获取股票的行业和地区信息
    
    Args:
        code: 6位股票代码
        
    Returns:
        包含 industry 和 area 的字典
    """
    try:
        import akshare as ak
        import os
        
        # 确保代理设置正确（AKShare需要访问国内API）
        # 如果设置了代理，确保NO_PROXY包含eastmoney.com等域名
        no_proxy = os.getenv('NO_PROXY', '') or os.getenv('no_proxy', '')
        if no_proxy and 'eastmoney.com' not in no_proxy.lower():
            logger.debug(f"⚠️  NO_PROXY可能缺少eastmoney.com，可能导致连接失败")
        
        def fetch_info():
            return ak.stock_individual_info_em(symbol=code)
        
        # 异步执行
        stock_info = await asyncio.to_thread(fetch_info)
        
        if stock_info is None or stock_info.empty:
            return {"industry": "未知", "area": "未知", "source": "akshare_empty"}
        
        result = {"industry": "未知", "area": "未知", "source": "akshare"}
        
        # 提取行业信息
        industry_row = stock_info[stock_info['item'] == '所属行业']
        if not industry_row.empty:
            result['industry'] = str(industry_row['value'].iloc[0])
        
        # 提取地区信息
        area_row = stock_info[stock_info['item'] == '所属地区']
        if not area_row.empty:
            result['area'] = str(area_row['value'].iloc[0])
        
        return result
        
    except Exception as e:
        logger.error(f"❌ AKShare获取 {code} 行业信息失败: {e}")
        return {"industry": "未知", "area": "未知", "source": "akshare_error"}


async def get_stock_industry_from_tushare(code: str) -> Dict[str, str]:
    """
    使用 Tushare 作为备用方案获取股票的行业和地区信息
    
    Args:
        code: 6位股票代码
        
    Returns:
        包含 industry 和 area 的字典
    """
    try:
        import tushare as ts
        import os
        import re
        
        # 获取 Tushare Token
        token = None
        
        # 优先从配置读取
        try:
            from app.core.config import settings
            token = settings.TUSHARE_TOKEN
        except:
            pass
        
        # 从环境变量读取
        if not token or token == "" or token.startswith('your_'):
            token = os.getenv('TUSHARE_TOKEN')
        
        # 从.env文件读取（如果上述方法都失败）
        if not token or token == "" or token.startswith('your_'):
            env_file = project_root / ".env"
            if env_file.exists():
                try:
                    with open(env_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        match = re.search(r'TUSHARE_TOKEN\s*=\s*(.+)', content, re.MULTILINE)
                        if match:
                            token = match.group(1).strip().strip('"\'')
                except:
                    pass
        
        if not token or token == "" or token.startswith('your_'):
            logger.debug(f"⚠️  未找到有效的Tushare Token")
            return {"industry": "未知", "area": "未知", "source": "tushare_no_token"}
        
        # 设置Token（只设置一次）
        try:
            ts.set_token(token)
        except:
            pass  # Token可能已经设置过
        
        pro = ts.pro_api()
        
        # 判断市场代码（转换为Tushare的ts_code格式）
        # 上海: 600xxx, 601xxx, 603xxx, 605xxx -> .SH
        # 深圳: 000xxx, 001xxx, 002xxx, 003xxx, 300xxx -> .SZ
        if code.startswith(('600', '601', '603', '605', '688', '689')):
            ts_code = f"{code}.SH"
        elif code.startswith(('000', '001', '002', '003', '300')):
            ts_code = f"{code}.SZ"
        else:
            # 尝试使用symbol查询
            ts_code = code
        
        def fetch_info():
            # 使用stock_basic API查询
            df = pro.stock_basic(
                exchange='',
                list_status='L',
                fields='ts_code,symbol,name,area,industry'
            )
            
            # 查找匹配的股票（优先使用symbol，因为ts_code可能格式不对）
            stock = df[df['symbol'] == code]
            if stock.empty:
                # 如果symbol匹配失败，尝试ts_code
                stock = df[df['ts_code'] == ts_code]
            
            return stock
        
        # 异步执行
        stock_info = await asyncio.to_thread(fetch_info)
        
        if stock_info is None or stock_info.empty:
            return {"industry": "未知", "area": "未知", "source": "tushare_empty"}
        
        row = stock_info.iloc[0]
        result = {
            "industry": str(row.get('industry', '未知')) if pd.notna(row.get('industry')) else "未知",
            "area": str(row.get('area', '未知')) if pd.notna(row.get('area')) else "未知",
            "source": "tushare"
        }
        
        # 如果行业信息为空或NaN，返回未知
        if result['industry'] == 'nan' or result['industry'] == '':
            result['industry'] = "未知"
        if result['area'] == 'nan' or result['area'] == '':
            result['area'] = "未知"
        
        return result
        
    except ImportError:
        logger.debug(f"⚠️  Tushare库未安装")
        return {"industry": "未知", "area": "未知", "source": "tushare_not_installed"}
    except Exception as e:
        error_msg = str(e)
        if "token" in error_msg.lower() or "您的token不对" in error_msg:
            logger.debug(f"⚠️  Tushare Token无效: {error_msg[:100]}")
        else:
            logger.debug(f"⚠️  Tushare获取 {code} 行业信息失败: {error_msg[:100]}")
        return {"industry": "未知", "area": "未知", "source": "tushare_error"}


async def get_stock_industry_with_fallback(
    code: str, 
    use_akshare_fallback: bool = True,
    use_tushare_fallback: bool = True
) -> Dict[str, str]:
    """
    获取股票行业信息，优先使用TDX，如果TDX无法提供则使用AKShare和Tushare备用方案
    
    Args:
        code: 6位股票代码
        use_akshare_fallback: 是否使用AKShare作为备用方案
        use_tushare_fallback: 是否使用Tushare作为备用方案
        
    Returns:
        包含 industry、area 和 source 的字典
    """
    # 首先尝试TDX
    logger.debug(f"🔍 [{code}] 尝试使用TDX获取行业信息...")
    tdx_result = await get_stock_industry_from_tdx(code)
    
    # 如果TDX成功获取到行业信息（非"未知"），直接返回
    if tdx_result.get("industry") and tdx_result.get("industry") != "未知":
        logger.info(f"✅ [{code}] TDX成功获取行业信息: {tdx_result['industry']}")
        return tdx_result
    
    # TDX无法提供行业信息，尝试AKShare备用方案
    if use_akshare_fallback:
        logger.debug(f"🔄 [{code}] TDX无法提供行业信息，尝试AKShare备用方案...")
        akshare_result = await get_stock_industry_from_akshare(code)
        
        if akshare_result.get("industry") and akshare_result.get("industry") != "未知":
            logger.info(f"✅ [{code}] AKShare成功获取行业信息: {akshare_result['industry']}")
            # 标记为TDX数据源，但行业信息来自AKShare
            akshare_result["source"] = "tdx_akshare"
            return akshare_result
        else:
            logger.debug(f"⚠️ [{code}] AKShare也无法获取行业信息")
    
    # AKShare也失败，尝试Tushare备用方案
    if use_tushare_fallback:
        logger.debug(f"🔄 [{code}] AKShare无法提供行业信息，尝试Tushare备用方案...")
        tushare_result = await get_stock_industry_from_tushare(code)
        
        if tushare_result.get("industry") and tushare_result.get("industry") != "未知":
            logger.info(f"✅ [{code}] Tushare成功获取行业信息: {tushare_result['industry']}")
            # 标记为TDX数据源，但行业信息来自Tushare
            tushare_result["source"] = "tdx_tushare"
            return tushare_result
        else:
            logger.debug(f"⚠️ [{code}] Tushare也无法获取行业信息")
    
    # 所有数据源都失败
    logger.warning(f"⚠️ [{code}] 所有数据源都无法获取行业信息")
    return {"industry": "未知", "area": "未知", "source": "all_failed"}


async def 更新行业信息(
    source: Optional[str] = None,
    missing_only: bool = False,
    limit: Optional[int] = None,
    batch_size: int = 50,
    delay: float = 0.5,
    use_akshare_fallback: bool = True,
    use_tushare_fallback: bool = True
):
    """
    更新行业信息主函数
    
    Args:
        source: 数据源（如'tdx'），None表示所有数据源
        missing_only: 是否只处理缺少行业信息的股票
        limit: 限制处理的股票数量（None=全部）
        batch_size: 每批处理的股票数量
        delay: 每只股票之间的延迟（秒），避免API限流
        use_akshare_fallback: 是否使用AKShare作为备用方案
        use_tushare_fallback: 是否使用Tushare作为备用方案
    """
    logger.info("=" * 80)
    logger.info("🚀 开始使用TDX接口查询股票行业信息并更新数据库")
    logger.info("=" * 80)
    
    if source:
        logger.info(f"📌 数据源限制: {source}")
    if missing_only:
        logger.info(f"📌 只处理缺少行业信息的股票")
    if use_akshare_fallback:
        logger.info(f"📌 启用AKShare备用方案")
    if use_tushare_fallback:
        logger.info(f"📌 启用Tushare备用方案")
    
    # 连接 MongoDB
    logger.info(f"🔌 连接 MongoDB: {MONGO_URI}")
    client = AsyncIOMotorClient(MONGO_URI)
    db = client[MONGO_DB]
    collection = db["stock_basic_info"]
    
    try:
        # 1. 构建查询条件
        query = {}
        
        # 数据源过滤
        if source:
            query["source"] = source
        
        # 只处理缺少行业信息的股票
        if missing_only:
            query["$or"] = [
                {"industry": "未知"},
                {"industry": {"$exists": False}},
                {"industry": None},
                {"industry": ""}
            ]
        
        total_count = await collection.count_documents(query)
        logger.info(f"📊 找到 {total_count} 只需要处理的股票")
        
        if total_count == 0:
            logger.info("✅ 没有需要处理的股票")
            return
        
        # 限制处理数量
        if limit:
            logger.info(f"⚠️  限制处理数量: {limit}")
            total_count = min(total_count, limit)
        
        # 2. 批量处理
        cursor = collection.find(query, {"code": 1, "symbol": 1, "name": 1, "industry": 1, "_id": 0})
        if limit:
            cursor = cursor.limit(limit)
        
        stocks = await cursor.to_list(length=None)
        
        logger.info(f"\n🔄 开始处理 {len(stocks)} 只股票...")
        logger.info(f"   批次大小: {batch_size}")
        logger.info(f"   延迟时间: {delay}秒/股票")
        logger.info("")
        
        success_count = 0
        failed_count = 0
        skipped_count = 0
        tdx_count = 0
        akshare_count = 0
        tushare_count = 0
        
        for i, stock in enumerate(stocks, 1):
            code = stock.get("code") or stock.get("symbol")
            name = stock.get("name", "")
            current_industry = stock.get("industry", "")
            
            if not code:
                logger.warning(f"⚠️  [{i}/{len(stocks)}] 跳过: 缺少股票代码")
                skipped_count += 1
                continue
            
            try:
                # 如果已经有行业信息且不是"未知"，可以跳过（除非missing_only=False且用户想更新所有）
                if not missing_only and current_industry and current_industry != "未知":
                    logger.debug(f"⏭️  [{i}/{len(stocks)}] 跳过 {code} ({name}): 已有行业信息={current_industry}")
                    skipped_count += 1
                    continue
                
                # 获取行业信息
                logger.info(f"🔍 [{i}/{len(stocks)}] 获取 {code} ({name}) 的行业信息...")
                info = await get_stock_industry_with_fallback(
                    code, 
                    use_akshare_fallback=use_akshare_fallback,
                    use_tushare_fallback=use_tushare_fallback
                )
                
                # 统计数据源
                source_used = info.get("source", "unknown")
                if "tdx" in source_used and "akshare" not in source_used and "tushare" not in source_used:
                    tdx_count += 1
                elif "akshare" in source_used:
                    akshare_count += 1
                elif "tushare" in source_used:
                    tushare_count += 1
                
                if info["industry"] != "未知" or info["area"] != "未知":
                    # 更新数据库
                    update_data = {
                        "industry": info["industry"],
                        "updated_at": datetime.utcnow()
                    }
                    
                    # 如果有地区信息，也更新
                    if info.get("area") and info["area"] != "未知":
                        update_data["area"] = info["area"]
                    
                    result = await collection.update_one(
                        {"$or": [{"code": code}, {"symbol": code}]},
                        {"$set": update_data}
                    )
                    
                    if result.modified_count > 0:
                        logger.info(f"   ✅ 更新成功: 行业={info['industry']}, 地区={info.get('area', 'N/A')}, 数据源={source_used}")
                        success_count += 1
                    else:
                        logger.warning(f"   ⚠️  未更新: 可能已存在相同数据")
                        skipped_count += 1
                else:
                    logger.warning(f"   ⚠️  未获取到有效信息（数据源: {source_used}）")
                    failed_count += 1
                
                # 延迟，避免API限流
                if i < len(stocks):
                    await asyncio.sleep(delay)
                
                # 每批次输出进度
                if i % batch_size == 0:
                    logger.info(f"\n📈 进度: {i}/{len(stocks)} ({i*100//len(stocks)}%)")
                    logger.info(f"   成功: {success_count}, 失败: {failed_count}, 跳过: {skipped_count}")
                    logger.info(f"   TDX: {tdx_count}, AKShare: {akshare_count}, Tushare: {tushare_count}\n")
                
            except Exception as e:
                logger.error(f"   ❌ 处理失败: {e}")
                failed_count += 1
        
        # 3. 输出统计
        logger.info("")
        logger.info("=" * 80)
        logger.info("📊 更新完成统计")
        logger.info("=" * 80)
        logger.info(f"   总计: {len(stocks)} 只股票")
        logger.info(f"   成功: {success_count} 只")
        logger.info(f"   失败: {failed_count} 只")
        logger.info(f"   跳过: {skipped_count} 只")
        logger.info(f"   成功率: {success_count*100//len(stocks) if len(stocks) > 0 else 0}%")
        logger.info(f"   数据源统计:")
        logger.info(f"     TDX: {tdx_count} 只")
        logger.info(f"     AKShare: {akshare_count} 只")
        logger.info(f"     Tushare: {tushare_count} 只")
        logger.info("=" * 80)
        
        # 4. 验证结果
        if missing_only:
            remaining_query = query.copy()
            remaining_count = await collection.count_documents(remaining_query)
            logger.info(f"\n✅ 剩余需要补充的股票: {remaining_count} 只")
            
            if remaining_count > 0:
                logger.info(f"💡 提示: 可以再次运行此脚本继续补充")
            else:
                logger.info(f"🎉 所有股票的行业信息已补充完成！")
        
    finally:
        client.close()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="使用TDX接口查询股票行业信息并更新到数据库",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 使用TDX查询所有股票的行业信息（TDX无法提供时使用AKShare备用方案）
  python scripts/使用TDX查询行业信息并更新.py

  # 只处理TDX数据源的股票
  python scripts/使用TDX查询行业信息并更新.py --source tdx

  # 只处理缺少行业信息的股票
  python scripts/使用TDX查询行业信息并更新.py --missing-only

  # 只处理前100只股票
  python scripts/使用TDX查询行业信息并更新.py --limit 100

  # 不使用AKShare备用方案（仅使用TDX和Tushare）
  python scripts/使用TDX查询行业信息并更新.py --no-akshare-fallback

  # 不使用Tushare备用方案（仅使用TDX和AKShare）
  python scripts/使用TDX查询行业信息并更新.py --no-tushare-fallback

  # 组合使用
  python scripts/使用TDX查询行业信息并更新.py --source tdx --missing-only --limit 100
        """
    )
    
    parser.add_argument(
        "--source",
        type=str,
        default=None,
        help="数据源过滤（如'tdx'），默认：所有数据源"
    )
    parser.add_argument(
        "--missing-only",
        action="store_true",
        help="只处理缺少行业信息的股票"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="限制处理的股票数量（默认：全部）"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=50,
        help="每批处理的股票数量（默认：50）"
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.5,
        help="每只股票之间的延迟（秒）（默认：0.5）"
    )
    parser.add_argument(
        "--no-akshare-fallback",
        action="store_true",
        help="不使用AKShare备用方案（仅使用TDX）"
    )
    parser.add_argument(
        "--no-tushare-fallback",
        action="store_true",
        help="不使用Tushare备用方案"
    )
    
    args = parser.parse_args()
    
    # 运行异步任务
    asyncio.run(更新行业信息(
        source=args.source,
        missing_only=args.missing_only,
        limit=args.limit,
        batch_size=args.batch_size,
        delay=args.delay,
        use_akshare_fallback=not args.no_akshare_fallback,
        use_tushare_fallback=not args.no_tushare_fallback
    ))


if __name__ == "__main__":
    main()

