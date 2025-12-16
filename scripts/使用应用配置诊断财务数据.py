#!/usr/bin/env python3
"""
使用应用配置诊断财务数据 - 通过应用配置连接MongoDB
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 设置环境变量，避免配置验证错误
os.environ.setdefault("TUSHARE_ENABLED", "false")
os.environ.setdefault("AKSHARE_UNIFIED_ENABLED", "true")

def check_with_app_config():
    """使用应用配置检查数据库"""
    print("="*70)
    print("📊 使用应用配置检查MongoDB数据库")
    print("="*70)
    
    try:
        # 导入应用配置
        from app.core.config import settings
        
        print(f"\nMongoDB配置:")
        print(f"  - Host: {settings.MONGODB_HOST}")
        print(f"  - Port: {settings.MONGODB_PORT}")
        print(f"  - Database: {settings.MONGODB_DATABASE}")
        print(f"  - Username: {settings.MONGODB_USERNAME or '(无)'}")
        print(f"  - Auth Source: {settings.MONGODB_AUTH_SOURCE}")
        
        # 🔥 智能检测：如果在宿主机运行，将mongodb改为localhost
        mongodb_host = settings.MONGODB_HOST
        if mongodb_host == "mongodb":
            # 尝试连接localhost（宿主机环境）
            from pymongo import MongoClient
            try:
                test_client = MongoClient("localhost", 27017, serverSelectionTimeoutMS=2000)
                test_client.admin.command('ping')
                test_client.close()
                mongodb_host = "localhost"
                print(f"\n💡 检测到宿主机环境，使用 localhost 替代 mongodb")
            except:
                print(f"\n💡 保持使用配置的 host: {mongodb_host}")
        
        # 使用应用的数据库连接，但使用修正后的host
        from pymongo import MongoClient
        
        print(f"\n连接MongoDB ({mongodb_host})...")
        
        # 构建连接参数
        connect_kwargs = {
            "host": mongodb_host,
            "port": settings.MONGODB_PORT,
            "serverSelectionTimeoutMS": 5000
        }
        
        # 如果有用户名和密码，添加认证信息
        if settings.MONGODB_USERNAME and settings.MONGODB_PASSWORD:
            connect_kwargs.update({
                "username": settings.MONGODB_USERNAME,
                "password": settings.MONGODB_PASSWORD,
                "authSource": settings.MONGODB_AUTH_SOURCE
            })
        
        client = MongoClient(**connect_kwargs)
        client.admin.command('ping')
        db = client[settings.MONGODB_DATABASE]
        
        if db is None:
            print("❌ 无法获取数据库连接")
            return
        
        print("✅ MongoDB连接成功")
        
        # 检查财务数据集合
        collection = db["stock_financial_data"]
        
        # 统计总数
        print(f"\n📊 统计财务数据...")
        total_count = collection.count_documents({})
        print(f"✅ 财务数据总记录数: {total_count}")
        
        if total_count == 0:
            print("\n❌ 警告：数据库中没有财务数据！")
            print("💡 建议：运行财务数据同步任务")
            print("   命令: python scripts/快速同步财务数据.py")
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
        
        found_count = 0
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
                found_count += 1
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
        
        # 总结
        print("\n" + "="*70)
        print("📊 诊断总结")
        print("="*70)
        print(f"  • 总记录数: {total_count}")
        print(f"  • 测试股票找到数据: {found_count}/{len(test_codes)}")
        
        if found_count == 0:
            print("\n⚠️ 问题: 测试股票都没有财务数据")
            print("💡 建议: 运行财务数据同步")
        elif found_count < len(test_codes):
            print("\n⚠️ 问题: 部分股票缺少财务数据")
            print("💡 建议: 检查同步任务配置或手动同步缺失的股票")
        else:
            print("\n✅ 测试股票都有财务数据")
            print("💡 如果分析时仍然数据不足，可能是查询逻辑问题")
        
    except Exception as e:
        print(f"\n❌ 检查失败: {e}")
        import traceback
        traceback.print_exc()


def main():
    """主函数"""
    print("="*70)
    print("🔍 基本面数据问题 - 使用应用配置诊断")
    print("="*70)
    
    try:
        check_with_app_config()
        
        print("\n" + "="*70)
        print("✅ 诊断完成")
        print("="*70)
        
    except Exception as e:
        print(f"\n❌ 诊断过程出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

