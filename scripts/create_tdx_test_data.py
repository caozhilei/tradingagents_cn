#!/usr/bin/env python3
"""
创建TDX数据源测试数据（包含行业信息）
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


async def create_test_data():
    """创建TDX数据源测试数据"""
    client = AsyncIOMotorClient(settings.MONGO_URI)
    db = client[settings.MONGO_DB]
    collection = db['stock_basic_info']
    
    # 创建测试数据：为一些常见股票创建TDX数据源记录（包含行业）
    test_stocks = [
        {'code': '000001', 'name': '平安银行', 'industry': '银行'},
        {'code': '600036', 'name': '招商银行', 'industry': '银行'},
        {'code': '600519', 'name': '贵州茅台', 'industry': '酿酒行业'},
        {'code': '000858', 'name': '五粮液', 'industry': '酿酒行业'},
        {'code': '300750', 'name': '宁德时代', 'industry': '电池'},
        {'code': '000002', 'name': '万科A', 'industry': '房地产开发'},
        {'code': '600276', 'name': '恒瑞医药', 'industry': '化学制药'},
        {'code': '000651', 'name': '格力电器', 'industry': '家电行业'},
        {'code': '000333', 'name': '美的集团', 'industry': '家电行业'},
        {'code': '600887', 'name': '伊利股份', 'industry': '食品饮料'},
    ]
    
    logger.info("创建TDX数据源测试数据...")
    for stock in test_stocks:
        result = await collection.update_one(
            {'code': stock['code'], 'source': 'tdx'},
            {
                '$set': {
                    'code': stock['code'],
                    'symbol': stock['code'],
                    'name': stock['name'],
                    'industry': stock['industry'],
                    'source': 'tdx',
                    'updated_at': datetime.utcnow()
                }
            },
            upsert=True
        )
        logger.info(f"  {stock['code']} - {stock['name']}: {stock['industry']}")
    
    # 验证
    count = await collection.count_documents({
        'source': 'tdx',
        'industry': {'$ne': None, '$ne': '', '$exists': True}
    })
    total = await collection.count_documents({'source': 'tdx'})
    
    logger.info(f"\n✅ 已创建 {len(test_stocks)} 条测试数据")
    logger.info(f"✅ TDX数据源股票总数: {total}")
    logger.info(f"✅ TDX数据源有行业数据的股票: {count} 只")
    
    client.close()


if __name__ == "__main__":
    asyncio.run(create_test_data())

