#!/usr/bin/env python3
"""
测试从TDX获取行业数据的可行性
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import get_mongo_db, init_db
from app.services.data_sources.tdx_adapter import TDXAdapter
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


async def test_tdx_availability():
    """测试TDX数据源是否可用"""
    logger.info("=" * 80)
    logger.info("测试1: TDX数据源可用性")
    logger.info("=" * 80)
    
    try:
        adapter = TDXAdapter()
        is_available = adapter.is_available()
        
        if is_available:
            logger.info("✅ TDX数据源可用")
            provider = adapter._get_provider()
            if provider:
                logger.info(f"  连接状态: {provider.connected}")
                logger.info(f"  API对象: {provider.api is not None}")
        else:
            logger.warning("⚠️  TDX数据源不可用")
        
        return is_available
    except Exception as e:
        logger.error(f"❌ 测试TDX可用性失败: {e}", exc_info=True)
        return False


async def check_database_tdx_data():
    """检查数据库中TDX数据源的股票数据"""
    logger.info("\n" + "=" * 80)
    logger.info("测试2: 检查数据库中TDX数据源的股票数据")
    logger.info("=" * 80)
    
    await init_db()
    db = get_mongo_db()
    collection = db["stock_basic_info"]
    
    # 统计TDX数据源的股票数量
    total_count = await collection.count_documents({"source": "tdx"})
    logger.info(f"📊 TDX数据源股票总数: {total_count}")
    
    if total_count == 0:
        logger.warning("⚠️  数据库中没有TDX数据源的股票数据")
        return None
    
    # 检查有行业数据的股票数量
    with_industry_count = await collection.count_documents({
        "source": "tdx",
        "industry": {"$ne": None, "$ne": "", "$exists": True}
    })
    logger.info(f"📊 有行业数据的股票数: {with_industry_count}")
    
    # 获取样本数据
    sample_docs = await collection.find(
        {"source": "tdx"},
        {"code": 1, "name": 1, "industry": 1, "symbol": 1}
    ).limit(10).to_list(length=10)
    
    logger.info(f"\n📋 样本数据（前10条）:")
    for i, doc in enumerate(sample_docs, 1):
        code = doc.get("code") or doc.get("symbol", "N/A")
        name = doc.get("name", "N/A")
        industry = doc.get("industry", "无")
        logger.info(f"  {i}. {code} - {name}: 行业={industry}")
    
    return sample_docs


async def test_tdx_provider_methods():
    """测试TDX提供器的方法"""
    logger.info("\n" + "=" * 80)
    logger.info("测试3: TDX提供器的方法")
    logger.info("=" * 80)
    
    try:
        from data.tdx_utils import get_tdx_provider
        
        provider = get_tdx_provider()
        if not provider:
            logger.warning("⚠️  无法获取TDX提供器")
            return
        
        if not provider.connected:
            logger.info("🔌 尝试连接TDX服务器...")
            if not provider.connect():
                logger.warning("⚠️  TDX连接失败")
                return
        
        logger.info("✅ TDX提供器已连接")
        
        # 检查提供器有哪些方法
        logger.info("\n📋 TDX提供器可用方法:")
        methods = [m for m in dir(provider) if not m.startswith('_') and callable(getattr(provider, m))]
        for method in methods[:20]:  # 只显示前20个
            logger.info(f"  - {method}")
        
        # 测试获取股票基本信息的方法
        test_code = "000001"
        logger.info(f"\n🔍 测试获取股票 {test_code} 的信息...")
        
        # 尝试常见的方法
        test_methods = [
            'get_real_time_data',
            'get_security_quotes',
            'get_security_list',
        ]
        
        for method_name in test_methods:
            if hasattr(provider, method_name):
                try:
                    method = getattr(provider, method_name)
                    logger.info(f"  尝试调用: {method_name}()")
                    # 根据方法签名调用
                    if method_name == 'get_real_time_data':
                        result = method(test_code)
                    elif method_name == 'get_security_quotes':
                        market = 0 if test_code.startswith(('000', '002', '300')) else 1
                        result = method([(market, test_code)])
                    elif method_name == 'get_security_list':
                        market = 0 if test_code.startswith(('000', '002', '300')) else 1
                        result = method(market)
                    else:
                        result = method()
                    
                    if result:
                        logger.info(f"    ✅ 成功，返回类型: {type(result)}")
                        if isinstance(result, (list, dict)):
                            logger.info(f"    数据量: {len(result) if hasattr(result, '__len__') else 'N/A'}")
                    else:
                        logger.info(f"    ⚠️  返回空结果")
                except Exception as e:
                    logger.warning(f"    ❌ 调用失败: {e}")
        
    except Exception as e:
        logger.error(f"❌ 测试TDX提供器方法失败: {e}", exc_info=True)


async def test_get_industry_from_mongodb():
    """测试从MongoDB获取TDX数据源的行业数据"""
    logger.info("\n" + "=" * 80)
    logger.info("测试4: 从MongoDB获取TDX数据源的行业数据")
    logger.info("=" * 80)
    
    await init_db()
    db = get_mongo_db()
    collection = db["stock_basic_info"]
    
    # 查询TDX数据源的行业数据
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
        {"$limit": 20}
    ]
    
    industries = []
    async for doc in collection.aggregate(pipeline):
        industries.append({
            "industry": doc.get("_id"),
            "count": doc.get("count", 0)
        })
    
    logger.info(f"📊 TDX数据源的行业数量: {len(industries)}")
    
    if industries:
        logger.info(f"\n📋 前20个行业:")
        for i, ind in enumerate(industries, 1):
            logger.info(f"  {i}. {ind['industry']}: {ind['count']}只股票")
    else:
        logger.warning("⚠️  没有找到TDX数据源的行业数据")
    
    return industries


async def test_industry_api_with_tdx():
    """测试行业接口是否包含TDX数据源"""
    logger.info("\n" + "=" * 80)
    logger.info("测试5: 测试行业接口（包含TDX数据源）")
    logger.info("=" * 80)
    
    try:
        from app.routers.screening import get_industries
        
        # 模拟用户
        mock_user = {
            "username": "test_user",
            "id": "test_id",
            "email": "test@example.com"
        }
        
        # 调用接口
        result = await get_industries(user=mock_user)
        
        logger.info(f"✅ 接口调用成功")
        logger.info(f"  返回的行业总数: {result.get('total', 0)}")
        logger.info(f"  数据源: {result.get('source', 'unknown')}")
        
        industries = result.get('industries', [])
        if industries:
            logger.info(f"\n📋 前10个行业:")
            for i, ind in enumerate(industries[:10], 1):
                logger.info(f"  {i}. {ind.get('label', 'N/A')}: {ind.get('count', 0)}只股票")
        else:
            logger.warning("⚠️  接口返回的行业列表为空")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ 测试接口失败: {e}", exc_info=True)
        return None


async def main():
    """主函数"""
    logger.info("=" * 80)
    logger.info("🚀 开始测试从TDX获取行业数据的可行性")
    logger.info("=" * 80)
    
    # 1. 测试TDX可用性
    tdx_available = await test_tdx_availability()
    
    # 2. 检查数据库中的TDX数据
    tdx_data = await check_database_tdx_data()
    
    # 3. 测试TDX提供器方法
    if tdx_available:
        await test_tdx_provider_methods()
    
    # 4. 测试从MongoDB获取TDX行业数据
    tdx_industries = await test_get_industry_from_mongodb()
    
    # 5. 测试行业接口
    await test_industry_api_with_tdx()
    
    # 总结
    logger.info("\n" + "=" * 80)
    logger.info("📊 测试总结")
    logger.info("=" * 80)
    logger.info(f"  TDX数据源可用: {'✅' if tdx_available else '❌'}")
    logger.info(f"  数据库TDX股票数: {len(tdx_data) if tdx_data else 0}")
    logger.info(f"  TDX行业数量: {len(tdx_industries) if tdx_industries else 0}")
    
    if tdx_available and tdx_industries:
        logger.info("\n✅ 结论: TDX数据源可用，且数据库中有行业数据")
    elif tdx_available:
        logger.info("\n⚠️  结论: TDX数据源可用，但数据库中没有行业数据")
        logger.info("   建议: 需要从其他数据源同步行业数据到TDX数据源")
    else:
        logger.info("\n❌ 结论: TDX数据源不可用")
    
    logger.info("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())

