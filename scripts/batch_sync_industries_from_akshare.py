#!/usr/bin/env python3
"""
从AKShare批量同步行业数据
使用行业板块接口批量获取股票行业信息，比逐个股票查询更高效
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

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


async def sync_industries_from_akshare():
    """从AKShare批量同步行业数据"""
    try:
        import akshare as ak
        
        logger.info("=" * 80)
        logger.info("🚀 开始从AKShare批量同步行业数据")
        logger.info("=" * 80)
        
        # 1. 获取所有行业板块列表
        logger.info("\n📋 步骤1: 获取行业板块列表...")
        
        def fetch_industries():
            return ak.stock_board_industry_name_em()
        
        industries_df = await asyncio.to_thread(fetch_industries)
        
        if industries_df is None or industries_df.empty:
            logger.error("❌ 未获取到行业板块列表")
            return
        
        logger.info(f"✅ 成功获取 {len(industries_df)} 个行业板块")
        
        # 2. 连接MongoDB
        logger.info("\n🔌 步骤2: 连接MongoDB...")
        client = AsyncIOMotorClient(settings.MONGO_URI)
        db = client[settings.MONGO_DB]
        collection = db["stock_basic_info"]
        
        # 3. 统计信息
        total_updated = 0
        total_processed = 0
        industry_stock_map: Dict[str, List[str]] = {}
        
        # 4. 遍历每个行业板块，获取该行业下的股票
        logger.info("\n📊 步骤3: 批量获取各行业的股票列表...")
        logger.info(f"   共 {len(industries_df)} 个行业需要处理\n")
        
        for idx, row in industries_df.iterrows():
            industry_name = str(row.get('板块名称', '')).strip()
            if not industry_name:
                continue
            
            try:
                # 获取该行业的股票列表（带重试机制）
                stocks_df = None
                max_retries = 3
                for retry in range(max_retries):
                    try:
                        def fetch_stocks():
                            return ak.stock_board_industry_cons_em(symbol=industry_name)
                        
                        stocks_df = await asyncio.to_thread(fetch_stocks)
                        break  # 成功获取，跳出重试循环
                    except Exception as e:
                        if retry < max_retries - 1:
                            wait_time = (retry + 1) * 2  # 递增等待时间：2s, 4s, 6s
                            logger.debug(f"    重试 {retry + 1}/{max_retries}，等待 {wait_time}秒...")
                            await asyncio.sleep(wait_time)
                        else:
                            raise e  # 最后一次重试失败，抛出异常
                
                if stocks_df is None or stocks_df.empty:
                    logger.debug(f"  ⚠️  行业 {industry_name} 没有股票数据")
                    continue
                
                # 提取股票代码
                stock_codes = []
                for _, stock_row in stocks_df.iterrows():
                    code = str(stock_row.get('代码', '')).strip()
                    if code:
                        # 确保代码是6位
                        code = code.zfill(6)
                        stock_codes.append(code)
                        industry_stock_map[code] = industry_name
                
                total_processed += len(stock_codes)
                logger.info(f"  ✅ [{idx+1}/{len(industries_df)}] {industry_name}: {len(stock_codes)} 只股票")
                
                # 添加延迟，避免API限流
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.warning(f"  ⚠️  处理行业 {industry_name} 失败: {e}")
                continue
        
        logger.info(f"\n✅ 共获取 {total_processed} 只股票的行业信息")
        
        # 5. 批量更新数据库
        logger.info("\n💾 步骤4: 批量更新数据库...")
        
        update_count = 0
        batch_size = 100
        batch = []
        
        for code, industry in industry_stock_map.items():
            batch.append(
                UpdateOne(
                    {"code": code, "source": "akshare"},
                    {"$set": {"industry": industry, "updated_at": datetime.utcnow()}},
                    upsert=False
                )
            )
            
            # 批量执行
            if len(batch) >= batch_size:
                try:
                    result = await collection.bulk_write(batch, ordered=False)
                    update_count += result.modified_count
                    logger.info(f"  已更新 {update_count} 只股票...")
                except Exception as e:
                    logger.warning(f"  批量更新失败: {e}")
                finally:
                    batch = []
        
        # 处理剩余的
        if batch:
            try:
                result = await collection.bulk_write(batch, ordered=False)
                update_count += result.modified_count
            except Exception as e:
                logger.warning(f"  最后一批更新失败: {e}")
        
        logger.info(f"✅ 批量更新完成，共更新 {update_count} 只股票的行业信息")
        
        # 6. 验证结果
        logger.info("\n📊 步骤5: 验证更新结果...")
        updated_count = await collection.count_documents({
            "source": "akshare",
            "industry": {"$ne": None, "$ne": "", "$exists": True}
        })
        logger.info(f"✅ 数据库中AKShare数据源有行业数据的股票: {updated_count} 只")
        
        logger.info("\n" + "=" * 80)
        logger.info("🎉 批量同步完成！")
        logger.info("=" * 80)
        
        client.close()
        
    except ImportError:
        logger.error("❌ akshare库未安装，请运行: pip install akshare")
    except Exception as e:
        logger.error(f"❌ 批量同步失败: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(sync_industries_from_akshare())

