"""检查股票详情页面的数据来源"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import init_mongodb, get_mongo_db
from app.core.config import get_settings


async def check_stock_data(code: str = "000001"):
    """检查指定股票的数据"""
    # 初始化数据库连接
    settings = get_settings()
    await init_mongodb(settings.MONGO_URI, settings.MONGO_DB)
    db = get_mongo_db()
    code6 = code.zfill(6)
    
    print(f"\n{'='*80}")
    print(f"检查股票 {code6} 的数据来源")
    print(f"{'='*80}\n")
    
    # 1. 检查 stock_basic_info
    print("1️⃣ stock_basic_info 集合:")
    print("-" * 80)
    basic_info_list = await db['stock_basic_info'].find({"code": code6}).to_list(length=10)
    if not basic_info_list:
        print(f"❌ 未找到 {code6} 的基础信息")
    else:
        for i, basic in enumerate(basic_info_list):
            source = basic.get('source', 'unknown')
            print(f"\n  数据源 {i+1}: {source}")
            print(f"    - PE: {basic.get('pe')}")
            print(f"    - PB: {basic.get('pb')}")
            print(f"    - PE_TTM: {basic.get('pe_ttm')}")
            print(f"    - ROE: {basic.get('roe')}")
            print(f"    - PS: {basic.get('ps')}")
            print(f"    - PS_TTM: {basic.get('ps_ttm')}")
            print(f"    - 总市值: {basic.get('total_mv')}")
    
    # 2. 检查 stock_financial_data
    print(f"\n2️⃣ stock_financial_data 集合:")
    print("-" * 80)
    financial_list = await db['stock_financial_data'].find({
        "$or": [{"code": code6}, {"symbol": code6}]
    }).sort("report_period", -1).to_list(length=5)
    
    if not financial_list:
        print(f"❌ 未找到 {code6} 的财务数据")
    else:
        print(f"✅ 找到 {len(financial_list)} 条财务数据记录\n")
        for i, financial in enumerate(financial_list[:3]):  # 只显示最新的3条
            print(f"  记录 {i+1}:")
            print(f"    - 数据源: {financial.get('data_source', 'unknown')}")
            print(f"    - 报告期: {financial.get('report_period', 'N/A')}")
            print(f"    - ROE: {financial.get('roe')}")
            print(f"    - 负债率 (debt_to_assets): {financial.get('debt_to_assets')}")
            print(f"    - 营业收入 (revenue): {financial.get('revenue')}")
            print(f"    - TTM营业收入 (revenue_ttm): {financial.get('revenue_ttm')}")
            
            # 检查 financial_indicators 嵌套字段
            if financial.get('financial_indicators'):
                indicators = financial['financial_indicators']
                print(f"    - financial_indicators.roe: {indicators.get('roe')}")
                print(f"    - financial_indicators.debt_to_assets: {indicators.get('debt_to_assets')}")
    
    # 3. 模拟 API 接口逻辑
    print(f"\n3️⃣ 模拟 API 接口返回结果:")
    print("-" * 80)
    
    # 获取基础信息（按优先级）
    source_priority = ["tushare", "multi_source", "akshare", "baostock"]
    basic_info = None
    used_source = None
    
    for src in source_priority:
        basic_info = await db['stock_basic_info'].find_one({"code": code6, "source": src}, {"_id": 0})
        if basic_info:
            used_source = src
            break
    
    if not basic_info:
        basic_info = await db['stock_basic_info'].find_one({"code": code6}, {"_id": 0})
    
    if not basic_info:
        print(f"❌ 无法获取基础信息")
        return
    
    print(f"✅ 使用数据源: {used_source or 'unknown'}")
    
    # 获取财务数据（按优先级）
    from app.core.unified_config import UnifiedConfigManager
    config = UnifiedConfigManager()
    data_source_configs = await config.get_data_source_configs_async()
    
    enabled_sources = [
        ds.type.lower() for ds in data_source_configs
        if ds.enabled and ds.type.lower() in ['tushare', 'akshare', 'baostock']
    ]
    
    if not enabled_sources:
        enabled_sources = ['tushare', 'akshare', 'baostock']
    
    financial_data = None
    financial_source = None
    
    for data_source in enabled_sources:
        financial_data = await db['stock_financial_data'].find_one(
            {"$or": [{"symbol": code6}, {"code": code6}], "data_source": data_source},
            {"_id": 0},
            sort=[("report_period", -1)]
        )
        if financial_data:
            financial_source = data_source
            break
    
    print(f"✅ 财务数据源: {financial_source or 'N/A'}")
    
    # 模拟构建返回数据
    result = {
        "roe": None,
        "debt_ratio": None,
        "ps": None,
        "ps_ttm": None,
    }
    
    if financial_data:
        # 提取 ROE
        if financial_data.get("financial_indicators"):
            indicators = financial_data["financial_indicators"]
            result["roe"] = indicators.get("roe")
            result["debt_ratio"] = indicators.get("debt_to_assets")
        
        if result["roe"] is None:
            result["roe"] = financial_data.get("roe")
        if result["debt_ratio"] is None:
            result["debt_ratio"] = financial_data.get("debt_to_assets")
        
        # 计算 PS
        revenue_ttm = financial_data.get("revenue_ttm")
        revenue = financial_data.get("revenue")
        revenue_for_ps = revenue_ttm if revenue_ttm and revenue_ttm > 0 else revenue
        
        total_mv = basic_info.get("total_mv")
        
        if revenue_for_ps and revenue_for_ps > 0 and total_mv and total_mv > 0:
            revenue_yi = revenue_for_ps / 100000000
            ps_calculated = total_mv / revenue_yi
            result["ps"] = round(ps_calculated, 2)
            result["ps_ttm"] = round(ps_calculated, 2) if revenue_ttm else None
        else:
            print(f"   ⚠️ PS 计算失败:")
            print(f"      - revenue_ttm: {revenue_ttm}")
            print(f"      - revenue: {revenue}")
            print(f"      - total_mv: {total_mv}")
    
    # 如果财务数据中没有 ROE，尝试从 basic_info 获取
    if result["roe"] is None:
        result["roe"] = basic_info.get("roe")
    
    print(f"\n📊 最终返回结果:")
    print(f"   - ROE: {result['roe']}")
    print(f"   - 负债率: {result['debt_ratio']}")
    print(f"   - PS: {result['ps']}")
    print(f"   - PS_TTM: {result['ps_ttm']}")
    
    print(f"\n{'='*80}\n")


if __name__ == "__main__":
    code = sys.argv[1] if len(sys.argv) > 1 else "000001"
    asyncio.run(check_stock_data(code))

