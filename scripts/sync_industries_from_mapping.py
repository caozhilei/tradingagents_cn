#!/usr/bin/env python3
"""
使用行业映射表同步行业数据
当AKShare API不可用时，使用预定义的行业映射表来补充行业数据
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import UpdateOne
from app.core.config import settings
import logging
import re

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def get_industry_by_code_pattern(code: str) -> str:
    """
    根据股票代码模式推断行业（基于常见行业分布）
    这是一个简化的映射，实际应该从数据源获取
    """
    code = str(code).zfill(6)
    
    # 银行类（常见银行代码）
    bank_codes = ['000001', '600000', '600015', '600016', '600036', '601166', '601169', 
                  '601288', '601328', '601398', '601818', '601838', '601860', '601916',
                  '601939', '601988', '601998', '002142', '002839']
    if code in bank_codes:
        return '银行'
    
    # 证券类（常见证券代码）
    security_codes = ['000166', '000686', '000728', '000750', '000776', '000783', '002500',
                     '002673', '002736', '002797', '600030', '600061', '600109', '600369',
                     '600837', '600909', '600958', '600999', '601066', '601108', '601136',
                     '601162', '601198', '601211', '601236', '601375', '601377', '601456',
                     '601555', '601688', '601788', '601878', '601881', '601901', '601990']
    if code in security_codes:
        return '证券'
    
    # 保险类
    insurance_codes = ['000627', '601318', '601601', '601628', '601319', '601336']
    if code in insurance_codes:
        return '保险'
    
    # 根据代码段推断（简化版）
    if code.startswith('60'):  # 上海主板
        if code.startswith('600519') or code.startswith('000858'):
            return '酿酒行业'
        elif code.startswith('600276') or code.startswith('000538'):
            return '化学制药'
        elif code.startswith('600887') or code.startswith('000895'):
            return '食品饮料'
        elif code.startswith('600036') or code.startswith('600000'):
            return '银行'
    elif code.startswith('000'):  # 深圳主板
        if code.startswith('000001'):
            return '银行'
        elif code.startswith('000002'):
            return '房地产开发'
        elif code.startswith('000651') or code.startswith('000333'):
            return '家电行业'
        elif code.startswith('000858'):
            return '酿酒行业'
    elif code.startswith('300'):  # 创业板
        if code.startswith('300750'):
            return '电池'
        elif code.startswith('300059'):
            return '互联网服务'
        elif code.startswith('300015'):
            return '医疗服务'
    
    return ''  # 无法推断时返回空


async def sync_industries_from_mapping():
    """使用行业映射表同步行业数据"""
    logger.info("=" * 80)
    logger.info("🚀 使用行业映射表同步行业数据")
    logger.info("=" * 80)
    
    # 连接MongoDB
    logger.info("\n🔌 连接MongoDB...")
    client = AsyncIOMotorClient(settings.MONGO_URI)
    db = client[settings.MONGO_DB]
    collection = db["stock_basic_info"]
    
    try:
        # 1. 查找没有行业数据的股票
        logger.info("\n📋 步骤1: 查找需要补充行业数据的股票...")
        
        # 查找AKShare数据源中没有行业数据的股票
        query = {
            "source": "akshare",
            "$or": [
                {"industry": {"$exists": False}},
                {"industry": None},
                {"industry": ""}
            ]
        }
        
        stocks_without_industry = await collection.find(
            query,
            {"code": 1, "symbol": 1, "name": 1}
        ).limit(1000).to_list(length=1000)  # 限制处理1000只股票
        
        logger.info(f"  找到 {len(stocks_without_industry)} 只需要补充行业数据的股票（限制1000只）")
        
        if not stocks_without_industry:
            logger.info("✅ 所有股票都已有行业数据")
            return
        
        # 2. 尝试从AKShare获取行业信息（如果API可用）
        logger.info("\n📋 步骤2: 尝试从AKShare获取行业信息...")
        
        import akshare as ak
        
        industry_map = {}
        success_count = 0
        failed_count = 0
        
        # 只处理前100只股票，避免超时
        sample_stocks = stocks_without_industry[:100]
        
        for i, stock in enumerate(sample_stocks, 1):
            code = stock.get("code") or stock.get("symbol")
            name = stock.get("name", "")
            
            if not code:
                continue
            
            code = str(code).zfill(6)
            
            # 尝试从AKShare获取
            try:
                def fetch_info():
                    try:
                        return ak.stock_individual_info_em(symbol=code)
                    except:
                        return None
                
                stock_info = await asyncio.to_thread(fetch_info)
                
                if stock_info is not None and not stock_info.empty:
                    # 提取行业信息
                    industry_row = stock_info[stock_info['item'] == '所属行业']
                    if not industry_row.empty:
                        industry = str(industry_row['value'].iloc[0]).strip()
                        if industry and industry not in ['-', '--', '未知', '']:
                            industry_map[code] = industry
                            success_count += 1
                            logger.info(f"  ✅ [{i}/{len(sample_stocks)}] {code} ({name}): {industry}")
                            await asyncio.sleep(0.2)  # 延迟避免限流
                            continue
            except Exception as e:
                # API调用失败，继续使用映射表
                pass
            
            # 如果API获取失败，使用映射表
            industry = get_industry_by_code_pattern(code)
            if industry:
                industry_map[code] = industry
                logger.info(f"  📋 [{i}/{len(sample_stocks)}] {code} ({name}): {industry} (映射表)")
            else:
                failed_count += 1
                logger.debug(f"  ⚠️  [{i}/{len(sample_stocks)}] {code} ({name}): 无法推断行业")
            
            await asyncio.sleep(0.1)
        
        logger.info(f"\n✅ 成功获取 {success_count} 只股票的行业信息（API）")
        logger.info(f"📋 使用映射表补充 {len(industry_map) - success_count} 只股票")
        logger.info(f"⚠️  无法获取 {failed_count} 只股票的行业信息")
        
        if not industry_map:
            logger.warning("⚠️  没有获取到任何行业数据")
            return
        
        # 3. 批量更新AKShare数据源
        logger.info("\n💾 步骤3: 批量更新AKShare数据源的行业数据...")
        
        operations = []
        update_count = 0
        batch_size = 100
        
        for code, industry in industry_map.items():
            operations.append(
                UpdateOne(
                    {"code": code, "source": "akshare"},
                    {"$set": {"industry": industry, "updated_at": datetime.utcnow()}},
                    upsert=False
                )
            )
            
            if len(operations) >= batch_size:
                try:
                    result = await collection.bulk_write(operations, ordered=False)
                    update_count += result.modified_count
                    logger.info(f"  已更新 {update_count} 只股票的行业数据...")
                    operations = []
                except Exception as e:
                    logger.warning(f"  批量更新失败: {e}")
                    operations = []
        
        if operations:
            try:
                result = await collection.bulk_write(operations, ordered=False)
                update_count += result.modified_count
            except Exception as e:
                logger.warning(f"  最后一批更新失败: {e}")
        
        logger.info(f"✅ 共更新 {update_count} 只AKShare数据源股票的行业数据")
        
        # 4. 同步到TDX数据源
        logger.info("\n💾 步骤4: 将行业数据同步到TDX数据源...")
        
        tdx_operations = []
        tdx_update_count = 0
        
        for code, industry in industry_map.items():
            # 获取股票名称
            stock_doc = await collection.find_one(
                {"code": code, "source": "akshare"},
                {"name": 1}
            )
            stock_name = stock_doc.get("name", f"股票{code}") if stock_doc else f"股票{code}"
            
            tdx_operations.append(
                UpdateOne(
                    {"code": code, "source": "tdx"},
                    {
                        "$set": {
                            "code": code,
                            "symbol": code,
                            "name": stock_name,
                            "industry": industry,
                            "source": "tdx",
                            "updated_at": datetime.utcnow()
                        }
                    },
                    upsert=True
                )
            )
            
            if len(tdx_operations) >= batch_size:
                try:
                    result = await collection.bulk_write(tdx_operations, ordered=False)
                    tdx_update_count += result.modified_count + result.upserted_count
                    logger.info(f"  已同步 {tdx_update_count} 条TDX记录...")
                    tdx_operations = []
                except Exception as e:
                    logger.warning(f"  批量同步TDX失败: {e}")
                    tdx_operations = []
        
        if tdx_operations:
            try:
                result = await collection.bulk_write(tdx_operations, ordered=False)
                tdx_update_count += result.modified_count + result.upserted_count
            except Exception as e:
                logger.warning(f"  最后一批TDX同步失败: {e}")
        
        logger.info(f"✅ 共同步 {tdx_update_count} 条TDX数据源记录")
        
        # 5. 验证结果
        logger.info("\n📊 步骤5: 验证同步结果...")
        
        # 统计各数据源的行业数据
        for source in ['akshare', 'tdx']:
            total = await collection.count_documents({"source": source})
            with_industry = await collection.count_documents({
                "source": source,
                "industry": {"$ne": None, "$ne": "", "$exists": True}
            })
            logger.info(f"  {source.upper()}数据源:")
            logger.info(f"    股票总数: {total}")
            logger.info(f"    有行业数据: {with_industry}")
            logger.info(f"    覆盖率: {with_industry*100//total if total > 0 else 0}%")
        
        # 统计行业分布
        pipeline = [
            {
                "$match": {
                    "source": {"$in": ["akshare", "tdx"]},
                    "industry": {"$ne": None, "$ne": "", "$exists": True}
                }
            },
            {
                "$group": {
                    "_id": "$industry",
                    "count": {"$sum": 1}
                }
            },
            {"$sort": {"count": -1}},
            {"$limit": 20}
        ]
        
        industries = []
        async for doc in collection.aggregate(pipeline):
            industries.append({
                "industry": doc.get("_id"),
                "count": doc.get("count", 0)
            })
        
        if industries:
            logger.info(f"\n📊 前20个行业分布:")
            for i, ind in enumerate(industries, 1):
                logger.info(f"  {i}. {ind['industry']}: {ind['count']}只股票")
        
        logger.info("\n" + "=" * 80)
        logger.info("🎉 行业数据同步完成！")
        logger.info("=" * 80)
        
    except ImportError:
        logger.error("❌ akshare库未安装")
    except Exception as e:
        logger.error(f"❌ 同步失败: {e}", exc_info=True)
    finally:
        client.close()


if __name__ == "__main__":
    asyncio.run(sync_industries_from_mapping())


