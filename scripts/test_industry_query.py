#!/usr/bin/env python3
"""
测试行业查询（包含TDX数据源）
"""
import asyncio
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import get_mongo_db, init_db
from app.core.unified_config import UnifiedConfigManager
from app.routers.screening import get_industries

async def test():
    await init_db()
    
    # 1. 检查配置
    config = UnifiedConfigManager()
    data_sources = await config.get_data_source_configs_async()
    print('数据源配置:')
    for ds in data_sources:
        print(f'  {ds.type}: enabled={ds.enabled}')
    
    enabled = [ds.type.lower() for ds in data_sources if ds.enabled and ds.type.lower() in ['tushare', 'akshare', 'baostock', 'tdx']]
    print(f'\n启用的数据源（包含TDX）: {enabled}')
    
    # 2. 直接查询数据库
    db = get_mongo_db()
    collection = db['stock_basic_info']
    
    pipeline = [
        {
            '$match': {
                'source': {'$in': enabled},
                'industry': {'$ne': None, '$ne': '', '$exists': True}
            }
        },
        {
            '$group': {
                '_id': '$industry',
                'count': {'$sum': 1},
                'sources': {'$addToSet': '$source'}
            }
        },
        {'$sort': {'count': -1}},
        {'$limit': 10}
    ]
    
    print('\n数据库查询结果:')
    async for doc in collection.aggregate(pipeline):
        industry = doc.get('_id')
        count = doc.get('count')
        sources = doc.get('sources', [])
        print(f'  {industry}: {count}只 (来源: {sources})')
    
    # 3. 测试接口
    print('\n接口查询结果:')
    result = await get_industries(user={'username': 'test', 'id': 'test'})
    print(f'  行业总数: {result.get("total", 0)}')
    print(f'  数据源: {result.get("source", "unknown")}')
    industries = result.get('industries', [])
    if industries:
        print(f'  前5个行业:')
        for i, ind in enumerate(industries[:5], 1):
            print(f'    {i}. {ind.get("label")}: {ind.get("count")}只')
    else:
        print('  无行业数据')

if __name__ == '__main__':
    asyncio.run(test())

