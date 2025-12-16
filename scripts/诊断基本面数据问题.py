#!/usr/bin/env python3
"""
诊断基本面数据问题脚本

检查：
1. 财务数据同步任务配置
2. 数据库中的财务数据数量
3. 数据源提供者的可用性
4. 测试获取财务数据
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import get_mongo_db
from app.core.config import settings
from app.services.financial_data_service import get_financial_data_service
from tradingagents.dataflows.providers.china.tushare import get_tushare_provider
from tradingagents.dataflows.providers.china.akshare import get_akshare_provider
from tradingagents.dataflows.providers.china.baostock import get_baostock_provider


async def check_database_financial_data():
    """检查数据库中的财务数据"""
    print("\n" + "="*70)
    print("📊 检查数据库中的财务数据")
    print("="*70)
    
    db = get_mongo_db()
    collection = db["stock_financial_data"]
    
    # 统计总数
    total_count = await collection.count_documents({})
    print(f"✅ 财务数据总记录数: {total_count}")
    
    if total_count == 0:
        print("❌ 警告：数据库中没有财务数据！")
        return
    
    # 按数据源统计
    pipeline = [
        {
            "$group": {
                "_id": "$data_source",
                "count": {"$sum": 1},
                "symbols": {"$addToSet": "$symbol"}
            }
        }
    ]
    
    results = await collection.aggregate(pipeline).to_list(length=None)
    
    print("\n按数据源统计:")
    for result in results:
        data_source = result["_id"] or "未知"
        count = result["count"]
        symbol_count = len(result["symbols"])
        print(f"  • {data_source}: {count} 条记录, {symbol_count} 只股票")
    
    # 按报告期统计
    pipeline = [
        {
            "$group": {
                "_id": "$report_period",
                "count": {"$sum": 1}
            }
        },
        {"$sort": {"_id": -1}},
        {"$limit": 5}
    ]
    
    results = await collection.aggregate(pipeline).to_list(length=None)
    
    print("\n最新报告期（前5个）:")
    for result in results:
        period = result["_id"] or "未知"
        count = result["count"]
        print(f"  • {period}: {count} 条记录")
    
    # 检查示例股票
    print("\n检查示例股票（前10只）:")
    sample_docs = await collection.find({}).limit(10).to_list(length=10)
    for doc in sample_docs:
        symbol = doc.get("symbol", "未知")
        data_source = doc.get("data_source", "未知")
        period = doc.get("report_period", "未知")
        has_roe = "roe" in doc or "financial_indicators" in doc
        print(f"  • {symbol} ({data_source}): 报告期={period}, 有ROE={has_roe}")


async def check_sync_task_config():
    """检查同步任务配置"""
    print("\n" + "="*70)
    print("⚙️  检查财务数据同步任务配置")
    print("="*70)
    
    # Tushare配置
    print("\nTushare配置:")
    print(f"  • TUSHARE_UNIFIED_ENABLED: {settings.TUSHARE_UNIFIED_ENABLED}")
    print(f"  • TUSHARE_FINANCIAL_SYNC_ENABLED: {getattr(settings, 'TUSHARE_FINANCIAL_SYNC_ENABLED', '未配置')}")
    print(f"  • TUSHARE_FINANCIAL_SYNC_CRON: {getattr(settings, 'TUSHARE_FINANCIAL_SYNC_CRON', '未配置')}")
    
    # AKShare配置
    print("\nAKShare配置:")
    print(f"  • AKSHARE_UNIFIED_ENABLED: {settings.AKSHARE_UNIFIED_ENABLED}")
    print(f"  • AKSHARE_FINANCIAL_SYNC_ENABLED: {settings.AKSHARE_FINANCIAL_SYNC_ENABLED}")
    print(f"  • AKSHARE_FINANCIAL_SYNC_CRON: {settings.AKSHARE_FINANCIAL_SYNC_CRON}")
    
    # BaoStock配置
    print("\nBaoStock配置:")
    print(f"  • BAOSTOCK_UNIFIED_ENABLED: {settings.BAOSTOCK_UNIFIED_ENABLED}")
    print(f"  • BAOSTOCK_FINANCIAL_SYNC_ENABLED: {getattr(settings, 'BAOSTOCK_FINANCIAL_SYNC_ENABLED', '未配置')}")


async def check_provider_availability():
    """检查数据源提供者可用性"""
    print("\n" + "="*70)
    print("🔌 检查数据源提供者可用性")
    print("="*70)
    
    # Tushare
    print("\nTushare:")
    try:
        provider = get_tushare_provider()
        is_available = provider.is_available()
        print(f"  • 可用性: {'✅ 可用' if is_available else '❌ 不可用'}")
        if is_available:
            print(f"  • API状态: {'✅ 已连接' if provider.api else '❌ 未连接'}")
    except Exception as e:
        print(f"  • ❌ 检查失败: {e}")
    
    # AKShare
    print("\nAKShare:")
    try:
        provider = get_akshare_provider()
        is_available = provider.is_available()
        print(f"  • 可用性: {'✅ 可用' if is_available else '❌ 不可用'}")
    except Exception as e:
        print(f"  • ❌ 检查失败: {e}")
    
    # BaoStock
    print("\nBaoStock:")
    try:
        provider = get_baostock_provider()
        is_available = provider.is_available()
        print(f"  • 可用性: {'✅ 可用' if is_available else '❌ 不可用'}")
    except Exception as e:
        print(f"  • ❌ 检查失败: {e}")


async def test_get_financial_data():
    """测试获取财务数据"""
    print("\n" + "="*70)
    print("🧪 测试获取财务数据")
    print("="*70)
    
    # 获取一只示例股票
    db = get_mongo_db()
    basic_info = await db["stock_basic_info"].find_one({})
    
    if not basic_info:
        print("❌ 未找到股票基础信息，无法测试")
        return
    
    test_code = basic_info.get("code", "000001")
    print(f"\n测试股票代码: {test_code}")
    
    # 测试Tushare
    print("\n测试Tushare:")
    try:
        provider = get_tushare_provider()
        if provider.is_available():
            financial_data = await provider.get_financial_data(test_code, report_type="quarterly")
            if financial_data:
                print(f"  • ✅ 获取成功: {len(financial_data) if isinstance(financial_data, dict) else 'N/A'} 个字段")
                # 检查关键字段
                key_fields = ['roe', 'revenue', 'net_income', 'total_assets']
                for field in key_fields:
                    if field in financial_data:
                        print(f"    - {field}: {financial_data[field]}")
            else:
                print("  • ❌ 返回空数据")
        else:
            print("  • ⚠️  提供者不可用")
    except Exception as e:
        print(f"  • ❌ 获取失败: {e}")
    
    # 测试AKShare
    print("\n测试AKShare:")
    try:
        provider = get_akshare_provider()
        if provider.is_available():
            financial_data = await provider.get_financial_data(test_code)
            if financial_data:
                print(f"  • ✅ 获取成功: {len(financial_data) if isinstance(financial_data, dict) else 'N/A'} 个字段")
                # 检查关键字段
                if 'main_indicators' in financial_data:
                    print(f"    - main_indicators: {len(financial_data['main_indicators'])} 条记录")
            else:
                print("  • ❌ 返回空数据")
        else:
            print("  • ⚠️  提供者不可用")
    except Exception as e:
        print(f"  • ❌ 获取失败: {e}")
    
    # 测试从数据库查询
    print("\n测试从数据库查询:")
    try:
        service = await get_financial_data_service()
        financial_data = await service.get_latest_financial_data(test_code)
        if financial_data:
            print(f"  • ✅ 查询成功")
            print(f"    - 数据源: {financial_data.get('data_source')}")
            print(f"    - 报告期: {financial_data.get('report_period')}")
            print(f"    - 有ROE: {'roe' in financial_data or 'financial_indicators' in financial_data}")
        else:
            print(f"  • ❌ 未找到 {test_code} 的财务数据")
    except Exception as e:
        print(f"  • ❌ 查询失败: {e}")


async def check_fundamentals_api():
    """检查基本面API接口"""
    print("\n" + "="*70)
    print("🌐 检查基本面API接口")
    print("="*70)
    
    # 获取一只示例股票
    db = get_mongo_db()
    basic_info = await db["stock_basic_info"].find_one({})
    
    if not basic_info:
        print("❌ 未找到股票基础信息，无法测试")
        return
    
    test_code = basic_info.get("code", "000001")
    print(f"\n测试股票代码: {test_code}")
    
    # 检查基本面接口逻辑
    print("\n检查基本面接口逻辑:")
    
    # 1. 检查基础信息
    basic_doc = await db["stock_basic_info"].find_one({"code": test_code})
    if basic_doc:
        print(f"  • ✅ 基础信息存在: {basic_doc.get('name')}")
    else:
        print(f"  • ❌ 基础信息不存在")
    
    # 2. 检查财务数据
    financial_doc = await db["stock_financial_data"].find_one(
        {"$or": [{"symbol": test_code}, {"code": test_code}]},
        sort=[("report_period", -1)]
    )
    if financial_doc:
        print(f"  • ✅ 财务数据存在: 数据源={financial_doc.get('data_source')}, 报告期={financial_doc.get('report_period')}")
    else:
        print(f"  • ❌ 财务数据不存在")


async def main():
    """主函数"""
    print("="*70)
    print("🔍 TradingAgents-CN 基本面数据诊断工具")
    print("="*70)
    
    try:
        # 1. 检查数据库财务数据
        await check_database_financial_data()
        
        # 2. 检查同步任务配置
        await check_sync_task_config()
        
        # 3. 检查数据源提供者
        await check_provider_availability()
        
        # 4. 测试获取财务数据
        await test_get_financial_data()
        
        # 5. 检查基本面API
        await check_fundamentals_api()
        
        print("\n" + "="*70)
        print("✅ 诊断完成")
        print("="*70)
        
        print("\n💡 建议:")
        print("  1. 如果数据库中没有财务数据，请运行财务数据同步任务")
        print("  2. 如果数据源不可用，请检查配置和网络连接")
        print("  3. 如果获取失败，请查看日志了解详细错误信息")
        print("  4. 可以通过 /api/financial-data/sync/start 接口手动触发同步")
        
    except Exception as e:
        print(f"\n❌ 诊断过程出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

