#!/usr/bin/env python3
"""
将其他数据源的行业数据同步到TDX数据源
由于TDX主要用于实时行情，不提供股票基本信息，需要从其他数据源补充行业数据
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime

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


async def sync_industry_to_tdx():
    """将其他数据源的行业数据同步到TDX数据源"""
    logger.info("=" * 80)
    logger.info("🚀 开始将行业数据同步到TDX数据源")
    logger.info("=" * 80)
    
    # 连接MongoDB
    logger.info("\n🔌 连接MongoDB...")
    client = AsyncIOMotorClient(settings.MONGO_URI)
    db = client[settings.MONGO_DB]
    collection = db["stock_basic_info"]
    
    try:
        # 1. 查找有行业数据的其他数据源（akshare, tushare, baostock）
        logger.info("\n📋 步骤1: 查找有行业数据的其他数据源...")
        
        source_priority = ['akshare', 'tushare', 'baostock']
        industry_map = {}  # {code: industry}
        
        for source in source_priority:
            pipeline = [
                {
                    "$match": {
                        "source": source,
                        "industry": {"$ne": None, "$ne": "", "$exists": True}
                    }
                },
                {
                    "$project": {
                        "code": 1,
                        "symbol": 1,
                        "industry": 1
                    }
                }
            ]
            
            count = 0
            async for doc in collection.aggregate(pipeline):
                code = doc.get("code") or doc.get("symbol")
                if code:
                    code = str(code).zfill(6)
                    industry = doc.get("industry", "").strip()
                    if industry and code not in industry_map:
                        industry_map[code] = industry
                        count += 1
            
            logger.info(f"  从 {source} 获取 {count} 只股票的行业数据")
        
        logger.info(f"\n✅ 共获取 {len(industry_map)} 只股票的行业数据")
        
        if not industry_map:
            logger.warning("⚠️  没有找到任何行业数据，无法同步")
            return
        
        # 2. 检查TDX数据源的股票数据
        logger.info("\n📋 步骤2: 检查TDX数据源的股票数据...")
        
        tdx_stocks = await collection.find(
            {"source": "tdx"},
            {"code": 1, "symbol": 1}
        ).to_list(length=None)
        
        logger.info(f"  数据库中有 {len(tdx_stocks)} 只TDX数据源的股票")
        
        if len(tdx_stocks) == 0:
            logger.info("\n💡 数据库中没有TDX数据源的股票，将创建TDX数据源记录...")
            
            # 从其他数据源获取股票列表，创建TDX数据源记录
            logger.info("  从其他数据源获取股票列表...")
            
            all_stocks = await collection.find(
                {"source": {"$in": source_priority}},
                {"code": 1, "symbol": 1, "name": 1}
            ).to_list(length=None)
            
            # 去重
            stock_dict = {}
            for doc in all_stocks:
                code = doc.get("code") or doc.get("symbol")
                if code:
                    code = str(code).zfill(6)
                    if code not in stock_dict:
                        stock_dict[code] = {
                            "code": code,
                            "symbol": code,
                            "name": doc.get("name", f"股票{code}")
                        }
            
            logger.info(f"  准备创建 {len(stock_dict)} 只股票的TDX数据源记录...")
            
            # 批量创建TDX数据源记录
            operations = []
            created_count = 0
            
            for code, stock_info in stock_dict.items():
                industry = industry_map.get(code, "")
                
                operations.append(
                    UpdateOne(
                        {"code": code, "source": "tdx"},
                        {
                            "$set": {
                                "code": code,
                                "symbol": code,
                                "name": stock_info["name"],
                                "industry": industry,
                                "source": "tdx",
                                "updated_at": datetime.utcnow()
                            }
                        },
                        upsert=True
                    )
                )
                
                if industry:
                    created_count += 1
                
                # 批量执行
                if len(operations) >= 100:
                    try:
                        await collection.bulk_write(operations, ordered=False)
                        logger.info(f"  已创建 {len(operations)} 条TDX记录...")
                        operations = []
                    except Exception as e:
                        logger.warning(f"  批量创建失败: {e}")
                        operations = []
            
            # 处理剩余的
            if operations:
                try:
                    await collection.bulk_write(operations, ordered=False)
                    logger.info(f"  已创建最后 {len(operations)} 条TDX记录...")
                except Exception as e:
                    logger.warning(f"  最后一批创建失败: {e}")
            
            logger.info(f"✅ 共创建 {len(stock_dict)} 条TDX数据源记录，其中 {created_count} 条包含行业数据")
        
        else:
            # 3. 更新现有TDX数据源的行业数据
            logger.info("\n📋 步骤3: 更新现有TDX数据源的行业数据...")
            
            operations = []
            update_count = 0
            
            for doc in tdx_stocks:
                code = doc.get("code") or doc.get("symbol")
                if code:
                    code = str(code).zfill(6)
                    industry = industry_map.get(code)
                    
                    if industry:
                        operations.append(
                            UpdateOne(
                                {"code": code, "source": "tdx"},
                                {
                                    "$set": {
                                        "industry": industry,
                                        "updated_at": datetime.utcnow()
                                    }
                                }
                            )
                        )
                        update_count += 1
                        
                        # 批量执行
                        if len(operations) >= 100:
                            try:
                                result = await collection.bulk_write(operations, ordered=False)
                                logger.info(f"  已更新 {result.modified_count} 条记录...")
                                operations = []
                            except Exception as e:
                                logger.warning(f"  批量更新失败: {e}")
                                operations = []
            
            # 处理剩余的
            if operations:
                try:
                    result = await collection.bulk_write(operations, ordered=False)
                    logger.info(f"  已更新最后 {result.modified_count} 条记录...")
                except Exception as e:
                    logger.warning(f"  最后一批更新失败: {e}")
            
            logger.info(f"✅ 共更新 {update_count} 条TDX数据源记录的行业数据")
        
        # 4. 验证结果
        logger.info("\n📋 步骤4: 验证同步结果...")
        
        tdx_with_industry = await collection.count_documents({
            "source": "tdx",
            "industry": {"$ne": None, "$ne": "", "$exists": True}
        })
        
        tdx_total = await collection.count_documents({"source": "tdx"})
        
        logger.info(f"  TDX数据源股票总数: {tdx_total}")
        logger.info(f"  有行业数据的股票数: {tdx_with_industry}")
        logger.info(f"  行业数据覆盖率: {tdx_with_industry*100//tdx_total if tdx_total > 0 else 0}%")
        
        # 5. 统计行业分布
        pipeline = [
            {
                "$match": {
                    "source": "tdx",
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
            {"$limit": 10}
        ]
        
        industries = []
        async for doc in collection.aggregate(pipeline):
            industries.append({
                "industry": doc.get("_id"),
                "count": doc.get("count", 0)
            })
        
        if industries:
            logger.info(f"\n📊 TDX数据源前10个行业:")
            for i, ind in enumerate(industries, 1):
                logger.info(f"  {i}. {ind['industry']}: {ind['count']}只股票")
        
        logger.info("\n" + "=" * 80)
        logger.info("🎉 行业数据同步完成！")
        logger.info("=" * 80)
        
    finally:
        client.close()


if __name__ == "__main__":
    asyncio.run(sync_industry_to_tdx())

