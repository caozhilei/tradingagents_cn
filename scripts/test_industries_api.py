#!/usr/bin/env python3
"""
验证行业数据接口脚本
检查数据库中的行业数据以及接口是否正常工作
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import get_mongo_db, init_db
from app.core.unified_config import UnifiedConfigManager
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(name)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


async def check_database_industries():
    """检查数据库中的行业数据"""
    print("\n" + "="*80)
    print("📊 检查数据库中的行业数据")
    print("="*80)
    
    await init_db()
    db = get_mongo_db()
    collection = db["stock_basic_info"]
    
    # 获取数据源配置
    config = UnifiedConfigManager()
    data_source_configs = await config.get_data_source_configs_async()
    
    enabled_sources = [
        ds.type.lower() for ds in data_source_configs
        if ds.enabled and ds.type.lower() in ['tushare', 'akshare', 'baostock', 'tdx']
    ]
    
    if not enabled_sources:
        enabled_sources = ['tushare', 'akshare', 'baostock', 'tdx']
    
    print(f"\n🔍 启用的数据源: {enabled_sources}")
    
    # 检查每个数据源的行业数据
    for source in enabled_sources:
        print(f"\n📋 检查数据源: {source}")
        print("-" * 80)
        
        # 统计该数据源的股票总数
        total_count = await collection.count_documents({"source": source})
        print(f"  总股票数: {total_count}")
        
        # 统计有行业数据的股票数
        with_industry_count = await collection.count_documents({
            "source": source,
            "industry": {"$ne": None, "$ne": "", "$exists": True}
        })
        print(f"  有行业数据的股票数: {with_industry_count}")
        
        # 获取该数据源的所有行业
        pipeline = [
            {
                "$match": {
                    "source": source,
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
            {"$limit": 10}  # 只显示前10个
        ]
        
        industries = []
        async for doc in collection.aggregate(pipeline):
            industries.append({
                "industry": doc.get("_id"),
                "count": doc.get("count", 0)
            })
        
        print(f"  行业数量: {len(industries)}")
        if industries:
            print(f"  前10个行业:")
            for i, ind in enumerate(industries[:10], 1):
                print(f"    {i}. {ind['industry']}: {ind['count']}只股票")
        else:
            print(f"  ⚠️  该数据源没有行业数据")
    
    # 合并所有数据源的行业数据
    print(f"\n📊 合并所有数据源的行业数据")
    print("-" * 80)
    
    pipeline = [
        {
            "$match": {
                "source": {"$in": enabled_sources},
                "industry": {"$ne": None, "$ne": "", "$exists": True}
            }
        },
        {
            "$group": {
                "_id": "$industry",
                "count": {"$sum": 1},
                "sources": {"$addToSet": "$source"}
            }
        },
        {"$sort": {"count": -1}},
        {"$limit": 20}
    ]
    
    all_industries = []
    async for doc in collection.aggregate(pipeline):
        all_industries.append({
            "industry": doc.get("_id"),
            "count": doc.get("count", 0),
            "sources": doc.get("sources", [])
        })
    
    print(f"  合并后的行业总数: {len(all_industries)}")
    if all_industries:
        print(f"  前20个行业:")
        for i, ind in enumerate(all_industries[:20], 1):
            sources_str = ", ".join(ind['sources'])
            print(f"    {i}. {ind['industry']}: {ind['count']}只股票 (来源: {sources_str})")
    else:
        print(f"  ⚠️  没有找到任何行业数据")


async def test_api_interface():
    """测试API接口"""
    print("\n" + "="*80)
    print("🔧 测试API接口")
    print("="*80)
    
    try:
        from app.routers.screening import get_industries
        from app.routers.auth_db import get_current_user
        
        # 模拟用户（用于测试）
        class MockUser:
            def __init__(self):
                self.username = "test_user"
                self.id = "test_id"
        
        mock_user_dict = {
            "username": "test_user",
            "id": "test_id",
            "email": "test@example.com"
        }
        
        # 创建一个依赖函数来返回mock用户
        async def get_mock_user():
            return mock_user_dict
        
        # 临时替换get_current_user
        import app.routers.screening as screening_module
        original_get_user = screening_module.get_current_user
        screening_module.get_current_user = lambda: get_mock_user()
        
        try:
            result = await get_industries(user=mock_user_dict)
            print(f"\n✅ API接口调用成功")
            print(f"  返回的行业总数: {result.get('total', 0)}")
            print(f"  数据源: {result.get('source', 'unknown')}")
            
            industries = result.get('industries', [])
            if industries:
                print(f"\n  前10个行业:")
                for i, ind in enumerate(industries[:10], 1):
                    print(f"    {i}. {ind.get('label', 'N/A')}: {ind.get('count', 0)}只股票")
            else:
                print(f"\n  ⚠️  接口返回的行业列表为空")
                
        finally:
            # 恢复原始函数
            screening_module.get_current_user = original_get_user
            
    except Exception as e:
        print(f"\n❌ API接口测试失败: {e}")
        import traceback
        traceback.print_exc()


async def check_sample_stocks():
    """检查样本股票的行业数据"""
    print("\n" + "="*80)
    print("🔍 检查样本股票的行业数据")
    print("="*80)
    
    await init_db()
    db = get_mongo_db()
    collection = db["stock_basic_info"]
    
    # 检查几个常见股票
    sample_codes = ['000001', '600036', '600519', '000858', '300750']
    
    for code in sample_codes:
        print(f"\n📌 股票代码: {code}")
        print("-" * 80)
        
        docs = await collection.find({"code": code}).to_list(length=None)
        
        if not docs:
            print(f"  ⚠️  未找到该股票的数据")
            continue
        
        for doc in docs:
            source = doc.get('source', 'unknown')
            name = doc.get('name', 'N/A')
            industry = doc.get('industry', 'N/A')
            
            print(f"  数据源: {source}")
            print(f"  股票名称: {name}")
            print(f"  行业: {industry if industry and industry != '' else '⚠️ 无行业数据'}")
            print()


async def main():
    """主函数"""
    print("\n" + "="*80)
    print("🚀 开始验证行业数据")
    print("="*80)
    
    try:
        # 1. 检查数据库中的行业数据
        await check_database_industries()
        
        # 2. 检查样本股票
        await check_sample_stocks()
        
        # 3. 测试API接口
        await test_api_interface()
        
        print("\n" + "="*80)
        print("✅ 验证完成")
        print("="*80)
        
    except Exception as e:
        print(f"\n❌ 验证过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

