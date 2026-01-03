#!/usr/bin/env python3
"""检查 Tushare 同步后的财务数据"""
import asyncio
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import init_database, get_mongo_db
from app.core.config import get_settings


async def main():
    settings = get_settings()
    await init_database()
    db = get_mongo_db()
    
    print("=" * 80)
    print("检查 Tushare 财务数据")
    print("=" * 80)
    
    code = "000001"
    doc = await db.stock_financial_data.find_one(
        {"code": code, "data_source": "tushare"},
        {"_id": 0}
    )
    
    if doc:
        print(f"\n✅ 找到 {code} 的 Tushare 财务数据")
        print(f"报告期: {doc.get('report_period', 'N/A')}")
        print(f"\n关键字段:")
        print(f"  Revenue TTM: {doc.get('revenue_ttm', 'N/A')}")
        print(f"  Revenue: {doc.get('revenue', 'N/A')}")
        print(f"  ROE: {doc.get('roe', 'N/A')}")
        print(f"  Debt to Assets: {doc.get('debt_to_assets', 'N/A')}")
        
        # 检查 financial_indicators
        if doc.get('financial_indicators'):
            indicators = doc['financial_indicators']
            print(f"\n  financial_indicators:")
            print(f"    ROE: {indicators.get('roe', 'N/A')}")
            print(f"    Debt to Assets: {indicators.get('debt_to_assets', 'N/A')}")
        
        # 显示所有非空字段
        non_empty = {k: v for k, v in doc.items() if v not in [None, ''] and k not in ['_id']}
        print(f"\n非空字段数: {len(non_empty)}")
        print(f"字段列表: {sorted(non_empty.keys())[:20]}")
    else:
        print(f"\n❌ 未找到 {code} 的 Tushare 财务数据")


if __name__ == "__main__":
    asyncio.run(main())

