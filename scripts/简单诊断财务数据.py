#!/usr/bin/env python3
"""
简单诊断财务数据问题 - 不依赖完整应用配置
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def check_database_directly():
    """直接检查数据库"""
    print("="*70)
    print("📊 直接检查MongoDB数据库")
    print("="*70)
    
    try:
        from pymongo import MongoClient
        import os
        
        # 从环境变量或默认值获取MongoDB连接信息
        mongodb_host = os.getenv("MONGODB_HOST", "localhost")
        mongodb_port = int(os.getenv("MONGODB_PORT", "27017"))
        mongodb_database = os.getenv("MONGODB_DATABASE", "tradingagents")
        mongodb_username = os.getenv("MONGODB_USERNAME", "")
        mongodb_password = os.getenv("MONGODB_PASSWORD", "")
        mongodb_auth_source = os.getenv("MONGODB_AUTH_SOURCE", "admin")
        
        print(f"\n连接MongoDB: {mongodb_host}:{mongodb_port}/{mongodb_database}")
        if mongodb_username:
            print(f"认证: {mongodb_username}@{mongodb_auth_source}")
        
        # 构建连接参数
        connect_kwargs = {
            "host": mongodb_host,
            "port": mongodb_port,
            "serverSelectionTimeoutMS": 5000
        }
        
        # 如果有用户名和密码，添加认证信息
        if mongodb_username and mongodb_password:
            connect_kwargs.update({
                "username": mongodb_username,
                "password": mongodb_password,
                "authSource": mongodb_auth_source
            })
        
        client = MongoClient(**connect_kwargs)
        db = client[mongodb_database]
        
        # 测试连接
        client.admin.command('ping')
        print("✅ MongoDB连接成功")
        
        # 检查财务数据集合
        collection = db["stock_financial_data"]
        
        # 统计总数
        total_count = collection.count_documents({})
        print(f"\n📊 财务数据总记录数: {total_count}")
        
        if total_count == 0:
            print("❌ 警告：数据库中没有财务数据！")
            print("💡 建议：运行财务数据同步任务")
            return
        
        # 按数据源统计
        print("\n按数据源统计:")
        pipeline = [
            {
                "$group": {
                    "_id": "$data_source",
                    "count": {"$sum": 1},
                    "symbols": {"$addToSet": "$symbol"}
                }
            }
        ]
        
        results = list(collection.aggregate(pipeline))
        
        for result in results:
            data_source = result["_id"] or "未知"
            count = result["count"]
            symbol_count = len(result["symbols"])
            print(f"  • {data_source}: {count} 条记录, {symbol_count} 只股票")
        
        # 按报告期统计
        print("\n最新报告期（前5个）:")
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
        
        results = list(collection.aggregate(pipeline))
        
        for result in results:
            period = result["_id"] or "未知"
            count = result["count"]
            print(f"  • {period}: {count} 条记录")
        
        # 检查示例股票（使用修复后的查询方式）
        print("\n检查示例股票（使用修复后的查询）:")
        test_codes = ["000001", "600000", "000002"]
        
        for code in test_codes:
            code6 = code.zfill(6)
            
            # 使用修复后的查询方式（$or查询）
            doc = collection.find_one({
                "$or": [
                    {"code": code6},
                    {"symbol": code6}
                ]
            }, {"_id": 0}, sort=[("report_period", -1)])
            
            if doc:
                data_source = doc.get("data_source", "未知")
                period = doc.get("report_period", "未知")
                has_roe = "roe" in doc or "financial_indicators" in doc
                print(f"  ✅ {code}: 数据源={data_source}, 报告期={period}, 有ROE={has_roe}")
            else:
                print(f"  ❌ {code}: 未找到财务数据")
        
        # 检查字段使用情况
        print("\n字段使用情况检查:")
        sample_doc = collection.find_one({})
        if sample_doc:
            has_code = "code" in sample_doc
            has_symbol = "symbol" in sample_doc
            print(f"  - 使用code字段: {has_code}")
            print(f"  - 使用symbol字段: {has_symbol}")
            if has_code and has_symbol:
                print(f"  - 两个字段的值: code={sample_doc.get('code')}, symbol={sample_doc.get('symbol')}")
        
        client.close()
        
    except Exception as e:
        print(f"❌ 检查失败: {e}")
        import traceback
        traceback.print_exc()


def check_data_source_files():
    """检查数据源文件"""
    print("\n" + "="*70)
    print("📁 检查数据源文件")
    print("="*70)
    
    files_to_check = [
        "tradingagents/dataflows/cache/mongodb_cache_adapter.py",
        "tradingagents/dataflows/data_source_manager.py",
        "app/services/financial_data_service.py",
        "app/worker/financial_data_sync_service.py"
    ]
    
    for file_path in files_to_check:
        full_path = project_root / file_path
        if full_path.exists():
            print(f"  ✅ {file_path}")
        else:
            print(f"  ❌ {file_path} (不存在)")


def main():
    """主函数"""
    print("="*70)
    print("🔍 基本面数据问题 - 简单诊断")
    print("="*70)
    
    # 检查数据库
    check_database_directly()
    
    # 检查文件
    check_data_source_files()
    
    print("\n" + "="*70)
    print("✅ 诊断完成")
    print("="*70)
    
    print("\n💡 下一步:")
    print("  1. 如果数据库中没有数据，运行: python scripts/快速同步财务数据.py")
    print("  2. 如果查询失败，检查MongoDB连接配置")
    print("  3. 查看完整诊断报告: docs/故障排除/基本面数据问题深度排查报告.md")


if __name__ == "__main__":
    main()

