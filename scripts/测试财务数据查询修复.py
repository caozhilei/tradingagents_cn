#!/usr/bin/env python3
"""
测试财务数据查询修复

验证修复后的MongoDB查询是否能正确获取财务数据
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import get_mongo_db
from tradingagents.dataflows.cache.mongodb_cache_adapter import get_mongodb_cache_adapter


async def test_database_query():
    """测试数据库直接查询"""
    print("\n" + "="*70)
    print("📊 测试1: 数据库直接查询")
    print("="*70)
    
    db = get_mongo_db()
    collection = db["stock_financial_data"]
    
    test_code = "000001"
    code6 = test_code.zfill(6)
    
    # 测试1: 只查询 code 字段
    print(f"\n测试1.1: 只查询 code={code6}")
    doc1 = await collection.find_one({"code": code6}, {"_id": 0})
    if doc1:
        print(f"  ✅ 找到数据 (code字段)")
        print(f"  - 数据源: {doc1.get('data_source')}")
        print(f"  - 报告期: {doc1.get('report_period')}")
    else:
        print(f"  ❌ 未找到数据 (code字段)")
    
    # 测试2: 只查询 symbol 字段
    print(f"\n测试1.2: 只查询 symbol={code6}")
    doc2 = await collection.find_one({"symbol": code6}, {"_id": 0})
    if doc2:
        print(f"  ✅ 找到数据 (symbol字段)")
        print(f"  - 数据源: {doc2.get('data_source')}")
        print(f"  - 报告期: {doc2.get('report_period')}")
    else:
        print(f"  ❌ 未找到数据 (symbol字段)")
    
    # 测试3: 使用 $or 查询（修复后的方式）
    print(f"\n测试1.3: 使用 $or 查询 (code 或 symbol)")
    doc3 = await collection.find_one({
        "$or": [
            {"code": code6},
            {"symbol": code6}
        ]
    }, {"_id": 0}, sort=[("report_period", -1)])
    if doc3:
        print(f"  ✅ 找到数据 ($or查询)")
        print(f"  - 数据源: {doc3.get('data_source')}")
        print(f"  - 报告期: {doc3.get('report_period')}")
        print(f"  - 使用的字段: {'code' if 'code' in doc3 and doc3.get('code') == code6 else 'symbol'}")
    else:
        print(f"  ❌ 未找到数据 ($or查询)")
    
    # 测试4: 统计数据
    print(f"\n测试1.4: 统计数据")
    count_code = await collection.count_documents({"code": code6})
    count_symbol = await collection.count_documents({"symbol": code6})
    count_or = await collection.count_documents({
        "$or": [
            {"code": code6},
            {"symbol": code6}
        ]
    })
    print(f"  - code字段记录数: {count_code}")
    print(f"  - symbol字段记录数: {count_symbol}")
    print(f"  - $or查询记录数: {count_or}")


def test_cache_adapter():
    """测试缓存适配器"""
    print("\n" + "="*70)
    print("📊 测试2: MongoDB缓存适配器")
    print("="*70)
    
    adapter = get_mongodb_cache_adapter()
    
    if not adapter.use_app_cache:
        print("  ⚠️ MongoDB缓存适配器未启用")
        print("  💡 提示: 需要设置 TA_USE_APP_CACHE=true")
        return
    
    test_code = "000001"
    
    print(f"\n测试2.1: 获取财务数据 (code={test_code})")
    data = adapter.get_financial_data(test_code)
    
    if data:
        print(f"  ✅ 成功获取财务数据")
        print(f"  - 数据源: {data.get('data_source')}")
        print(f"  - 报告期: {data.get('report_period')}")
        print(f"  - 包含字段: {len(data)} 个")
        
        # 检查关键字段
        key_fields = ['roe', 'revenue', 'net_income', 'total_assets', 'financial_indicators']
        print(f"  - 关键字段检查:")
        for field in key_fields:
            if field in data:
                print(f"    ✅ {field}: 存在")
            else:
                print(f"    ❌ {field}: 缺失")
    else:
        print(f"  ❌ 未获取到财务数据")
        print(f"  💡 可能原因:")
        print(f"    1. 数据库中没有该股票的财务数据")
        print(f"    2. 查询条件不匹配")
        print(f"    3. 数据源配置问题")


async def test_multiple_stocks():
    """测试多只股票"""
    print("\n" + "="*70)
    print("📊 测试3: 多只股票查询")
    print("="*70)
    
    db = get_mongo_db()
    collection = db["stock_financial_data"]
    
    test_codes = ["000001", "600000", "000002"]
    
    for code in test_codes:
        code6 = code.zfill(6)
        print(f"\n测试股票: {code}")
        
        # 使用修复后的查询方式
        doc = await collection.find_one({
            "$or": [
                {"code": code6},
                {"symbol": code6}
            ]
        }, {"_id": 0}, sort=[("report_period", -1)])
        
        if doc:
            print(f"  ✅ 找到数据")
            print(f"    - 数据源: {doc.get('data_source')}")
            print(f"    - 报告期: {doc.get('report_period')}")
        else:
            print(f"  ❌ 未找到数据")


async def main():
    """主函数"""
    print("="*70)
    print("🔍 财务数据查询修复验证")
    print("="*70)
    
    try:
        # 测试1: 数据库直接查询
        await test_database_query()
        
        # 测试2: 缓存适配器
        test_cache_adapter()
        
        # 测试3: 多只股票
        await test_multiple_stocks()
        
        print("\n" + "="*70)
        print("✅ 测试完成")
        print("="*70)
        
        print("\n💡 修复建议:")
        print("  1. 如果测试1.3成功但测试2失败，说明缓存适配器需要更新")
        print("  2. 如果所有测试都失败，说明数据库中没有财务数据，需要运行同步")
        print("  3. 如果只有部分股票有数据，说明同步不完整")
        
    except Exception as e:
        print(f"\n❌ 测试过程出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

