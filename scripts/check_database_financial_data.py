"""检查数据库中的财务数据情况"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import init_database, get_mongo_db
from app.core.config import get_settings
import json


async def check_database():
    """检查数据库中的财务数据"""
    settings = get_settings()
    
    # 初始化数据库
    await init_database()
    db = get_mongo_db()
    
    print("=" * 80)
    print("数据库财务数据检查报告")
    print("=" * 80)
    print()
    
    # 1. 检查 stock_financial_data 集合统计
    print("1️⃣ stock_financial_data 集合统计:")
    print("-" * 80)
    total_count = await db.stock_financial_data.count_documents({})
    print(f"   总记录数: {total_count}")
    
    if total_count == 0:
        print("   ⚠️ 集合为空，没有财务数据！")
        print()
    else:
        # 按数据源统计
        pipeline = [
            {"$group": {"_id": "$data_source", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        print("   按数据源统计:")
        async for doc in db.stock_financial_data.aggregate(pipeline):
            source = doc.get("_id") or "未知"
            count = doc.get("count", 0)
            print(f"     - {source}: {count} 条")
        print()
    
    # 2. 检查关键字段存在情况
    print("2️⃣ 关键字段存在情况:")
    print("-" * 80)
    if total_count > 0:
        has_revenue_ttm = await db.stock_financial_data.count_documents({"revenue_ttm": {"$exists": True, "$ne": None}})
        has_revenue = await db.stock_financial_data.count_documents({"revenue": {"$exists": True, "$ne": None}})
        has_roe = await db.stock_financial_data.count_documents({"roe": {"$exists": True, "$ne": None}})
        has_debt = await db.stock_financial_data.count_documents({"debt_to_assets": {"$exists": True, "$ne": None}})
        has_indicators_roe = await db.stock_financial_data.count_documents({"financial_indicators.roe": {"$exists": True, "$ne": None}})
        has_indicators_debt = await db.stock_financial_data.count_documents({"financial_indicators.debt_to_assets": {"$exists": True, "$ne": None}})
        
        print(f"   有 revenue_ttm 字段: {has_revenue_ttm} / {total_count} ({has_revenue_ttm/total_count*100:.1f}%)")
        print(f"   有 revenue 字段: {has_revenue} / {total_count} ({has_revenue/total_count*100:.1f}%)")
        print(f"   有 roe 字段（顶层）: {has_roe} / {total_count} ({has_roe/total_count*100:.1f}%)")
        print(f"   有 debt_to_assets 字段（顶层）: {has_debt} / {total_count} ({has_debt/total_count*100:.1f}%)")
        print(f"   有 financial_indicators.roe: {has_indicators_roe} / {total_count} ({has_indicators_roe/total_count*100:.1f}%)")
        print(f"   有 financial_indicators.debt_to_assets: {has_indicators_debt} / {total_count} ({has_indicators_debt/total_count*100:.1f}%)")
    else:
        print("   集合为空，无法统计")
    print()
    
    # 3. 检查 000001 的具体数据
    print("3️⃣ 检查股票 000001 的财务数据:")
    print("-" * 80)
    code6 = "000001"
    financial_docs = []
    async for doc in db.stock_financial_data.find({"$or": [{"code": code6}, {"symbol": code6}]}).sort("report_period", -1).limit(3):
        financial_docs.append(doc)
    
    if not financial_docs:
        print(f"   ❌ 未找到 {code6} 的财务数据")
    else:
        print(f"   ✅ 找到 {len(financial_docs)} 条记录（显示最新3条）")
        for i, doc in enumerate(financial_docs, 1):
            print(f"\n   记录 {i}:")
            print(f"     数据源: {doc.get('data_source', 'N/A')}")
            print(f"     报告期: {doc.get('report_period', 'N/A')}")
            print(f"     Revenue TTM: {doc.get('revenue_ttm', 'N/A')}")
            print(f"     Revenue: {doc.get('revenue', 'N/A')}")
            print(f"     ROE (顶层): {doc.get('roe', 'N/A')}")
            print(f"     Debt to Assets (顶层): {doc.get('debt_to_assets', 'N/A')}")
            if doc.get('financial_indicators'):
                indicators = doc['financial_indicators']
                print(f"     financial_indicators.roe: {indicators.get('roe', 'N/A')}")
                print(f"     financial_indicators.debt_to_assets: {indicators.get('debt_to_assets', 'N/A')}")
    print()
    
    # 4. 检查 stock_basic_info 中的 ROE
    print("4️⃣ 检查 stock_basic_info 中的 ROE:")
    print("-" * 80)
    basic_total = await db.stock_basic_info.count_documents({})
    basic_with_roe = await db.stock_basic_info.count_documents({"roe": {"$exists": True, "$ne": None}})
    print(f"   总记录数: {basic_total}")
    if basic_total > 0:
        roe_pct = basic_with_roe / basic_total * 100
    else:
        roe_pct = 0
    print(f"   有 roe 字段: {basic_with_roe} / {basic_total} ({roe_pct:.1f}%)")
    
    # 检查 000001 的基础信息
    basic_docs = []
    async for doc in db.stock_basic_info.find({"code": code6}).limit(3):
        basic_docs.append(doc)
    
    if basic_docs:
        print(f"\n   {code6} 的基础信息（显示所有数据源）:")
        for doc in basic_docs:
            print(f"     数据源: {doc.get('source', 'N/A')}")
            print(f"     名称: {doc.get('name', 'N/A')}")
            print(f"     ROE: {doc.get('roe', 'N/A')}")
            print(f"     PE_TTM: {doc.get('pe_ttm', 'N/A')}")
            print(f"     总市值: {doc.get('total_mv', 'N/A')}")
            print()
    else:
        print(f"   ❌ 未找到 {code6} 的基础信息")
    print()
    
    # 5. 随机检查几条样本数据
    print("5️⃣ 随机样本数据（5条）:")
    print("-" * 80)
    sample_docs = []
    async for doc in db.stock_financial_data.find({}).limit(5):
        sample_docs.append(doc)
    
    if sample_docs:
        for i, doc in enumerate(sample_docs, 1):
            print(f"\n   样本 {i}:")
            print(f"     Code: {doc.get('code') or doc.get('symbol', 'N/A')}")
            print(f"     数据源: {doc.get('data_source', 'N/A')}")
            print(f"     报告期: {doc.get('report_period', 'N/A')}")
            print(f"     Revenue TTM: {doc.get('revenue_ttm', 'N/A')}")
            print(f"     Revenue: {doc.get('revenue', 'N/A')}")
            print(f"     ROE: {doc.get('roe', 'N/A')}")
            print(f"     Debt to Assets: {doc.get('debt_to_assets', 'N/A')}")
    else:
        print("   没有数据可显示")
    
    print()
    print("=" * 80)
    print("检查完成")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(check_database())

