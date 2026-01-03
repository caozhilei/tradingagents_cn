#!/usr/bin/env python3
"""
安全地同步行业数据（带重试和错误处理）
使用之前测试成功的行业板块接口，逐步同步
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List
import time

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


async def sync_industries_with_retry(max_retries: int = 3, delay: float = 2.0):
    """带重试机制的行业数据同步"""
    try:
        import akshare as ak
        
        logger.info("=" * 80)
        logger.info("🚀 开始安全地同步行业数据（带重试机制）")
        logger.info("=" * 80)
        
        # 连接MongoDB
        logger.info("\n🔌 连接MongoDB...")
        client = AsyncIOMotorClient(settings.MONGO_URI)
        db = client[settings.MONGO_DB]
        collection = db["stock_basic_info"]
        
        # 1. 获取行业板块列表（带重试）
        logger.info("\n📋 步骤1: 获取行业板块列表（带重试）...")
        
        industries_df = None
        for retry in range(max_retries):
            try:
                def fetch_industries():
                    return ak.stock_board_industry_name_em()
                
                industries_df = await asyncio.to_thread(fetch_industries)
                if industries_df is not None and not industries_df.empty:
                    logger.info(f"✅ 成功获取 {len(industries_df)} 个行业板块（重试 {retry + 1}/{max_retries}）")
                    break
            except Exception as e:
                if retry < max_retries - 1:
                    wait_time = delay * (retry + 1)
                    logger.warning(f"⚠️  获取行业板块失败（重试 {retry + 1}/{max_retries}），等待 {wait_time}秒后重试...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"❌ 获取行业板块失败（已重试 {max_retries} 次）: {e}")
                    return
        
        if industries_df is None or industries_df.empty:
            logger.error("❌ 无法获取行业板块列表，同步终止")
            return
        
        # 2. 逐步获取每个行业的股票列表
        logger.info(f"\n📊 步骤2: 逐步获取各行业的股票列表...")
        logger.info(f"   共 {len(industries_df)} 个行业需要处理\n")
        
        industry_stock_map: Dict[str, List[str]] = {}
        success_count = 0
        failed_count = 0
        
        for idx, row in industries_df.iterrows():
            industry_name = str(row.get('板块名称', '')).strip()
            if not industry_name:
                continue
            
            # 尝试获取该行业的股票列表（带重试）
            stocks_df = None
            for retry in range(max_retries):
                try:
                    def fetch_stocks():
                        return ak.stock_board_industry_cons_em(symbol=industry_name)
                    
                    stocks_df = await asyncio.to_thread(fetch_stocks)
                    if stocks_df is not None and not stocks_df.empty:
                        break
                except Exception as e:
                    if retry < max_retries - 1:
                        wait_time = delay * (retry + 1)
                        logger.debug(f"    行业 {industry_name} 获取失败（重试 {retry + 1}/{max_retries}），等待 {wait_time}秒...")
                        await asyncio.sleep(wait_time)
                    else:
                        logger.warning(f"  ⚠️  行业 {industry_name} 获取失败（已重试 {max_retries} 次）: {e}")
                        failed_count += 1
                        break
            
            if stocks_df is not None and not stocks_df.empty:
                # 提取股票代码
                stock_codes = []
                for _, stock_row in stocks_df.iterrows():
                    code = str(stock_row.get('代码', '')).strip()
                    if code:
                        code = code.zfill(6)
                        stock_codes.append(code)
                        industry_stock_map[code] = industry_name
                
                success_count += 1
                logger.info(f"  ✅ [{idx+1}/{len(industries_df)}] {industry_name}: {len(stock_codes)} 只股票")
            else:
                failed_count += 1
                logger.warning(f"  ⚠️  [{idx+1}/{len(industries_df)}] {industry_name}: 获取失败")
            
            # 添加延迟，避免API限流
            await asyncio.sleep(1.0)  # 每个行业之间延迟1秒
        
        logger.info(f"\n✅ 成功获取 {success_count} 个行业的股票数据")
        logger.info(f"⚠️  失败 {failed_count} 个行业")
        logger.info(f"📊 共获取 {len(industry_stock_map)} 只股票的行业信息")
        
        if not industry_stock_map:
            logger.warning("⚠️  没有获取到任何行业数据，同步终止")
            return
        
        # 3. 批量更新数据库（先更新AKShare数据源）
        logger.info("\n💾 步骤3: 批量更新AKShare数据源的行业数据...")
        
        operations = []
        update_count = 0
        batch_size = 100
        
        for code, industry in industry_stock_map.items():
            operations.append(
                UpdateOne(
                    {"code": code, "source": "akshare"},
                    {"$set": {"industry": industry, "updated_at": datetime.utcnow()}},
                    upsert=False
                )
            )
            
            # 批量执行
            if len(operations) >= batch_size:
                try:
                    result = await collection.bulk_write(operations, ordered=False)
                    update_count += result.modified_count
                    logger.info(f"  已更新 {update_count} 只股票的行业数据...")
                    operations = []
                except Exception as e:
                    logger.warning(f"  批量更新失败: {e}")
                    operations = []
        
        # 处理剩余的
        if operations:
            try:
                result = await collection.bulk_write(operations, ordered=False)
                update_count += result.modified_count
            except Exception as e:
                logger.warning(f"  最后一批更新失败: {e}")
        
        logger.info(f"✅ 共更新 {update_count} 只AKShare数据源股票的行业数据")
        
        # 4. 同步到TDX数据源
        logger.info("\n💾 步骤4: 将行业数据同步到TDX数据源...")
        
        # 获取所有有行业数据的股票代码
        akshare_stocks_with_industry = await collection.find(
            {"source": "akshare", "industry": {"$ne": None, "$ne": "", "$exists": True}},
            {"code": 1, "industry": 1}
        ).to_list(length=None)
        
        tdx_operations = []
        tdx_update_count = 0
        
        for doc in akshare_stocks_with_industry:
            code = doc.get("code")
            industry = doc.get("industry")
            if code and industry:
                # 更新或创建TDX数据源记录
                tdx_operations.append(
                    UpdateOne(
                        {"code": code, "source": "tdx"},
                        {
                            "$set": {
                                "code": code,
                                "symbol": code,
                                "industry": industry,
                                "source": "tdx",
                                "updated_at": datetime.utcnow()
                            }
                        },
                        upsert=True
                    )
                )
                
                # 批量执行
                if len(tdx_operations) >= batch_size:
                    try:
                        result = await collection.bulk_write(tdx_operations, ordered=False)
                        tdx_update_count += result.modified_count + result.upserted_count
                        logger.info(f"  已同步 {tdx_update_count} 条TDX记录...")
                        tdx_operations = []
                    except Exception as e:
                        logger.warning(f"  批量同步TDX失败: {e}")
                        tdx_operations = []
        
        # 处理剩余的
        if tdx_operations:
            try:
                result = await collection.bulk_write(tdx_operations, ordered=False)
                tdx_update_count += result.modified_count + result.upserted_count
            except Exception as e:
                logger.warning(f"  最后一批TDX同步失败: {e}")
        
        logger.info(f"✅ 共同步 {tdx_update_count} 条TDX数据源记录")
        
        # 5. 验证结果
        logger.info("\n📊 步骤5: 验证同步结果...")
        
        # AKShare数据源
        akshare_with_industry = await collection.count_documents({
            "source": "akshare",
            "industry": {"$ne": None, "$ne": "", "$exists": True}
        })
        akshare_total = await collection.count_documents({"source": "akshare"})
        
        logger.info(f"  AKShare数据源:")
        logger.info(f"    股票总数: {akshare_total}")
        logger.info(f"    有行业数据: {akshare_with_industry}")
        logger.info(f"    覆盖率: {akshare_with_industry*100//akshare_total if akshare_total > 0 else 0}%")
        
        # TDX数据源
        tdx_with_industry = await collection.count_documents({
            "source": "tdx",
            "industry": {"$ne": None, "$ne": "", "$exists": True}
        })
        tdx_total = await collection.count_documents({"source": "tdx"})
        
        logger.info(f"  TDX数据源:")
        logger.info(f"    股票总数: {tdx_total}")
        logger.info(f"    有行业数据: {tdx_with_industry}")
        logger.info(f"    覆盖率: {tdx_with_industry*100//tdx_total if tdx_total > 0 else 0}%")
        
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
        
        client.close()
        
    except ImportError:
        logger.error("❌ akshare库未安装，请运行: pip install akshare")
    except Exception as e:
        logger.error(f"❌ 同步失败: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(sync_industries_with_retry(max_retries=3, delay=2.0))













