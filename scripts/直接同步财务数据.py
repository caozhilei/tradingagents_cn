#!/usr/bin/env python3
"""
直接同步财务数据 - 不依赖完整应用配置
"""

import sys
import os
import asyncio
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 设置环境变量，避免配置验证错误
os.environ.setdefault("TUSHARE_ENABLED", "false")
os.environ.setdefault("AKSHARE_UNIFIED_ENABLED", "true")


async def sync_financial_data_direct():
    """直接同步财务数据"""
    print("="*70)
    print("🔄 直接同步财务数据")
    print("="*70)
    
    try:
        from pymongo import MongoClient
        from app.core.config import settings
        
        # 智能检测host
        mongodb_host = settings.MONGODB_HOST
        if mongodb_host == "mongodb":
            mongodb_host = "localhost"
        
        # 连接MongoDB
        print(f"\n连接MongoDB: {mongodb_host}:{settings.MONGODB_PORT}")
        connect_kwargs = {
            "host": mongodb_host,
            "port": settings.MONGODB_PORT,
            "serverSelectionTimeoutMS": 5000
        }
        
        if settings.MONGODB_USERNAME and settings.MONGODB_PASSWORD:
            connect_kwargs.update({
                "username": settings.MONGODB_USERNAME,
                "password": settings.MONGODB_PASSWORD,
                "authSource": settings.MONGODB_AUTH_SOURCE
            })
        
        client = MongoClient(**connect_kwargs)
        client.admin.command('ping')
        db = client[settings.MONGODB_DATABASE]
        print("✅ MongoDB连接成功")
        
        # 获取股票列表
        print("\n📊 获取股票列表...")
        basic_collection = db["stock_basic_info"]
        stocks = list(basic_collection.find({}, {"code": 1}).limit(10))  # 先测试10只股票
        
        if not stocks:
            print("❌ 未找到股票基础信息")
            return
        
        stock_codes = [s["code"] for s in stocks if "code" in s]
        print(f"✅ 找到 {len(stock_codes)} 只股票: {', '.join(stock_codes[:5])}...")
        
        # 测试AKShare提供者
        print("\n🔌 测试AKShare提供者...")
        from tradingagents.dataflows.providers.china.akshare import get_akshare_provider
        
        provider = get_akshare_provider()
        if not provider.is_available():
            print("❌ AKShare提供者不可用")
            return
        
        print("✅ AKShare提供者可用")
        
        # 直接使用MongoDB保存财务数据（不依赖应用服务）
        financial_collection = db["stock_financial_data"]
        
        # 同步财务数据
        print(f"\n🔄 开始同步 {len(stock_codes)} 只股票的财务数据...")
        print("="*70)
        
        success_count = 0
        error_count = 0
        
        for i, code in enumerate(stock_codes, 1):
            code6 = str(code).zfill(6)
            print(f"\n[{i}/{len(stock_codes)}] 同步 {code6}...")
            
            try:
                # 获取财务数据
                financial_data = await provider.get_financial_data(code6)
                
                if financial_data:
                    # 直接保存到数据库
                    from datetime import datetime, timezone
                    from pymongo import ReplaceOne
                    
                    # 提取报告期（从main_indicators中获取）
                    report_period = None
                    if 'main_indicators' in financial_data and financial_data['main_indicators']:
                        first_record = financial_data['main_indicators'][0]
                        if '报告期' in first_record:
                            period_str = str(first_record['报告期'])
                            # 转换为YYYYMMDD格式
                            report_period = period_str.replace('-', '')
                    
                    if not report_period:
                        # 使用当前季度
                        now = datetime.now()
                        quarter = (now.month - 1) // 3 + 1
                        quarter_end_months = {1: "03", 2: "06", 3: "09", 4: "12"}
                        quarter_end_days = {1: "31", 2: "30", 3: "30", 4: "31"}
                        report_period = f"{now.year}{quarter_end_months[quarter]}{quarter_end_days[quarter]}"
                    
                    # 构建文档
                    now = datetime.now(timezone.utc)
                    doc = {
                        "code": code6,
                        "symbol": code6,
                        "full_symbol": f"{code6}.SH" if code6.startswith("6") else f"{code6}.SZ",
                        "market": "CN",
                        "report_period": report_period,
                        "report_type": "quarterly",
                        "data_source": "akshare",
                        "created_at": now,
                        "updated_at": now,
                        "version": 1
                    }
                    
                    # 提取关键指标
                    if 'main_indicators' in financial_data and financial_data['main_indicators']:
                        main_data = financial_data['main_indicators'][0]
                        doc.update({
                            "revenue": main_data.get('营业收入'),
                            "net_income": main_data.get('净利润'),
                            "total_assets": main_data.get('总资产'),
                            "total_equity": main_data.get('股东权益合计'),
                            "roe": main_data.get('净资产收益率(ROE)') or main_data.get('净资产收益率'),
                            "debt_to_assets": main_data.get('资产负债率')
                        })
                    
                    # 保存（upsert）
                    filter_doc = {
                        "symbol": code6,
                        "report_period": report_period,
                        "data_source": "akshare"
                    }
                    
                    financial_collection.replace_one(filter_doc, doc, upsert=True)
                    success_count += 1
                    print(f"  ✅ 成功: 报告期={report_period}")
                else:
                    error_count += 1
                    print(f"  ⚠️ 未获取到数据")
                
                # API限流延迟
                await asyncio.sleep(1.0)
                
            except Exception as e:
                error_count += 1
                print(f"  ❌ 错误: {e}")
        
        # 显示结果
        print("\n" + "="*70)
        print("✅ 同步完成")
        print("="*70)
        print(f"  • 总股票数: {len(stock_codes)}")
        print(f"  • 成功: {success_count}")
        print(f"  • 失败: {error_count}")
        print(f"  • 成功率: {success_count/max(len(stock_codes),1)*100:.1f}%")
        
        # 验证结果
        print("\n📊 验证同步结果...")
        financial_collection = db["stock_financial_data"]
        total_count = financial_collection.count_documents({})
        print(f"  • 数据库总记录数: {total_count}")
        
        client.close()
        
    except Exception as e:
        print(f"\n❌ 同步失败: {e}")
        import traceback
        traceback.print_exc()


async def sync_specific_stocks(codes):
    """同步指定股票"""
    print(f"🔄 同步指定股票: {', '.join(codes)}")
    
    try:
        from pymongo import MongoClient
        from app.core.config import settings
        
        # 智能检测host
        mongodb_host = settings.MONGODB_HOST
        if mongodb_host == "mongodb":
            mongodb_host = "localhost"
        
        # 连接MongoDB
        connect_kwargs = {
            "host": mongodb_host,
            "port": settings.MONGODB_PORT,
            "serverSelectionTimeoutMS": 5000
        }
        
        if settings.MONGODB_USERNAME and settings.MONGODB_PASSWORD:
            connect_kwargs.update({
                "username": settings.MONGODB_USERNAME,
                "password": settings.MONGODB_PASSWORD,
                "authSource": settings.MONGODB_AUTH_SOURCE
            })
        
        client = MongoClient(**connect_kwargs)
        db = client[settings.MONGODB_DATABASE]
        
        # 获取提供者
        from tradingagents.dataflows.providers.china.akshare import get_akshare_provider
        provider = get_akshare_provider()
        
        if not provider.is_available():
            print("❌ AKShare提供者不可用")
            return
        
        # 直接使用MongoDB保存
        financial_collection = db["stock_financial_data"]
        
        # 同步
        success_count = 0
        for code in codes:
            code6 = str(code).zfill(6)
            print(f"\n同步 {code6}...")
            
            try:
                financial_data = await provider.get_financial_data(code6)
                if financial_data:
                    # 提取报告期
                    from datetime import datetime, timezone
                    from pymongo import ReplaceOne
                    
                    report_period = None
                    if 'main_indicators' in financial_data and financial_data['main_indicators']:
                        first_record = financial_data['main_indicators'][0]
                        if '报告期' in first_record:
                            period_str = str(first_record['报告期'])
                            report_period = period_str.replace('-', '')
                    
                    if not report_period:
                        now = datetime.now()
                        quarter = (now.month - 1) // 3 + 1
                        quarter_end_months = {1: "03", 2: "06", 3: "09", 4: "12"}
                        quarter_end_days = {1: "31", 2: "30", 3: "30", 4: "31"}
                        report_period = f"{now.year}{quarter_end_months[quarter]}{quarter_end_days[quarter]}"
                    
                    # 构建文档
                    now = datetime.now(timezone.utc)
                    doc = {
                        "code": code6,
                        "symbol": code6,
                        "full_symbol": f"{code6}.SH" if code6.startswith("6") else f"{code6}.SZ",
                        "market": "CN",
                        "report_period": report_period,
                        "report_type": "quarterly",
                        "data_source": "akshare",
                        "created_at": now,
                        "updated_at": now,
                        "version": 1
                    }
                    
                    # 提取关键指标
                    if 'main_indicators' in financial_data and financial_data['main_indicators']:
                        main_data = financial_data['main_indicators'][0]
                        doc.update({
                            "revenue": main_data.get('营业收入'),
                            "net_income": main_data.get('净利润'),
                            "total_assets": main_data.get('总资产'),
                            "total_equity": main_data.get('股东权益合计'),
                            "roe": main_data.get('净资产收益率(ROE)') or main_data.get('净资产收益率'),
                            "debt_to_assets": main_data.get('资产负债率')
                        })
                    
                    # 保存
                    filter_doc = {
                        "symbol": code6,
                        "report_period": report_period,
                        "data_source": "akshare"
                    }
                    
                    financial_collection.replace_one(filter_doc, doc, upsert=True)
                    success_count += 1
                    print(f"  ✅ 成功: 报告期={report_period}")
                else:
                    print(f"  ⚠️ 未获取到数据")
                
                await asyncio.sleep(1.0)
            except Exception as e:
                print(f"  ❌ 错误: {e}")
        
        print(f"\n✅ 完成: {success_count}/{len(codes)} 成功")
        client.close()
        
    except Exception as e:
        print(f"❌ 同步失败: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="直接同步财务数据")
    parser.add_argument(
        "--symbols",
        nargs="+",
        help="股票代码列表（如：000001 600000）"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="同步股票数量限制（默认10）"
    )
    
    args = parser.parse_args()
    
    if args.symbols:
        await sync_specific_stocks(args.symbols)
    else:
        # 修改为同步指定数量的股票
        print(f"💡 未指定股票，将同步前 {args.limit} 只股票")
        print(f"💡 如需同步所有股票，请使用: py scripts/直接同步财务数据.py --symbols <股票代码>")
        await sync_financial_data_direct()


if __name__ == "__main__":
    asyncio.run(main())

