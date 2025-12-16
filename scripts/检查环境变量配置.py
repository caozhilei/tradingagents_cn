#!/usr/bin/env python3
"""
检查环境变量配置脚本

验证MongoDB等关键配置是否正确设置
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


def check_env_file():
    """检查.env文件"""
    print("="*70)
    print("📋 检查环境变量配置文件")
    print("="*70)
    
    env_file = project_root / ".env"
    env_example = project_root / ".env.example"
    
    # 检查.env.example
    if env_example.exists():
        print(f"\n✅ .env.example 存在: {env_example}")
    else:
        print(f"\n❌ .env.example 不存在")
        print(f"💡 建议: 创建 .env.example 作为配置模板")
    
    # 检查.env
    if env_file.exists():
        print(f"✅ .env 文件存在: {env_file}")
        
        # 读取并显示关键配置（隐藏敏感信息）
        print("\n📊 当前配置（隐藏敏感信息）:")
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # 隐藏敏感信息
                    if any(sensitive in key.upper() for sensitive in ['PASSWORD', 'SECRET', 'KEY', 'TOKEN']):
                        if value:
                            print(f"  • {key}=***（已设置）")
                        else:
                            print(f"  • {key}=（未设置）")
                    else:
                        print(f"  • {key}={value}")
    else:
        print(f"\n⚠️  .env 文件不存在")
        print(f"💡 建议:")
        print(f"  1. 复制 .env.example 为 .env: cp .env.example .env")
        print(f"  2. 编辑 .env 文件，配置MongoDB等信息")


def check_mongodb_config():
    """检查MongoDB配置"""
    print("\n" + "="*70)
    print("📊 检查MongoDB配置")
    print("="*70)
    
    try:
        from app.core.config import settings
        
        print(f"\nMongoDB配置:")
        print(f"  • Host: {settings.MONGODB_HOST}")
        print(f"  • Port: {settings.MONGODB_PORT}")
        print(f"  • Database: {settings.MONGODB_DATABASE}")
        print(f"  • Username: {settings.MONGODB_USERNAME or '(无)'}")
        print(f"  • Auth Source: {settings.MONGODB_AUTH_SOURCE}")
        
        # 检查配置合理性
        issues = []
        
        if settings.MONGODB_HOST == "mongodb" and not os.getenv("DOCKER_CONTAINER"):
            issues.append("⚠️  Host设置为'mongodb'，但不在Docker容器内，应该使用'localhost'")
        
        if not settings.MONGODB_USERNAME and settings.MONGODB_PASSWORD:
            issues.append("⚠️  设置了密码但未设置用户名")
        
        if settings.MONGODB_USERNAME and not settings.MONGODB_PASSWORD:
            issues.append("⚠️  设置了用户名但未设置密码")
        
        if issues:
            print("\n⚠️  配置问题:")
            for issue in issues:
                print(f"  {issue}")
        else:
            print("\n✅ MongoDB配置看起来正常")
        
        # 显示连接字符串（隐藏密码）
        uri = settings.MONGO_URI
        if settings.MONGODB_PASSWORD:
            # 隐藏密码
            uri = uri.replace(settings.MONGODB_PASSWORD, "***")
        print(f"\n连接字符串: {uri}")
        
    except Exception as e:
        print(f"\n❌ 检查配置失败: {e}")
        import traceback
        traceback.print_exc()


def check_financial_sync_config():
    """检查财务数据同步配置"""
    print("\n" + "="*70)
    print("🔄 检查财务数据同步配置")
    print("="*70)
    
    try:
        from app.core.config import settings
        
        print("\nAKShare配置:")
        print(f"  • AKSHARE_UNIFIED_ENABLED: {settings.AKSHARE_UNIFIED_ENABLED}")
        print(f"  • AKSHARE_FINANCIAL_SYNC_ENABLED: {settings.AKSHARE_FINANCIAL_SYNC_ENABLED}")
        print(f"  • AKSHARE_FINANCIAL_SYNC_CRON: {settings.AKSHARE_FINANCIAL_SYNC_CRON}")
        
        print("\nTushare配置:")
        print(f"  • TUSHARE_UNIFIED_ENABLED: {getattr(settings, 'TUSHARE_UNIFIED_ENABLED', '未配置')}")
        print(f"  • TUSHARE_FINANCIAL_SYNC_ENABLED: {getattr(settings, 'TUSHARE_FINANCIAL_SYNC_ENABLED', '未配置')}")
        print(f"  • TUSHARE_FINANCIAL_SYNC_CRON: {getattr(settings, 'TUSHARE_FINANCIAL_SYNC_CRON', '未配置')}")
        
        # 检查是否启用了同步
        if settings.AKSHARE_UNIFIED_ENABLED and settings.AKSHARE_FINANCIAL_SYNC_ENABLED:
            print("\n✅ AKShare财务数据同步已启用")
        else:
            print("\n⚠️  AKShare财务数据同步未启用")
            print("💡 建议: 在.env文件中设置")
            print("  AKSHARE_UNIFIED_ENABLED=true")
            print("  AKSHARE_FINANCIAL_SYNC_ENABLED=true")
        
    except Exception as e:
        print(f"\n❌ 检查同步配置失败: {e}")


def test_mongodb_connection():
    """测试MongoDB连接"""
    print("\n" + "="*70)
    print("🔌 测试MongoDB连接")
    print("="*70)
    
    try:
        from app.core.config import settings
        from pymongo import MongoClient
        
        # 智能检测host
        mongodb_host = settings.MONGODB_HOST
        if mongodb_host == "mongodb":
            mongodb_host = "localhost"
            print(f"💡 检测到宿主机环境，使用 localhost 替代 mongodb")
        
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
        print("✅ MongoDB连接成功")
        
        # 检查数据库
        db = client[settings.MONGODB_DATABASE]
        collections = db.list_collection_names()
        print(f"✅ 数据库 '{settings.MONGODB_DATABASE}' 存在")
        print(f"  • 集合数量: {len(collections)}")
        
        # 检查财务数据集合
        if "stock_financial_data" in collections:
            count = db["stock_financial_data"].count_documents({})
            print(f"  • stock_financial_data: {count} 条记录")
        else:
            print(f"  • stock_financial_data: 集合不存在（首次运行正常）")
        
        client.close()
        
    except Exception as e:
        print(f"❌ MongoDB连接失败: {e}")
        print(f"\n💡 可能的原因:")
        print(f"  1. MongoDB未启动")
        print(f"  2. 配置的host/port不正确")
        print(f"  3. 用户名/密码错误")
        print(f"  4. 网络连接问题")


def main():
    """主函数"""
    print("="*70)
    print("🔍 环境变量配置检查工具")
    print("="*70)
    
    # 检查.env文件
    check_env_file()
    
    # 检查MongoDB配置
    check_mongodb_config()
    
    # 检查财务数据同步配置
    check_financial_sync_config()
    
    # 测试MongoDB连接
    test_mongodb_connection()
    
    print("\n" + "="*70)
    print("✅ 检查完成")
    print("="*70)
    
    print("\n💡 下一步:")
    print("  1. 如果.env文件不存在，创建并配置")
    print("  2. 如果MongoDB连接失败，检查配置和MongoDB服务")
    print("  3. 如果财务数据同步未启用，在.env中启用")
    print("  4. 运行财务数据同步: py scripts/批量同步财务数据.py")


if __name__ == "__main__":
    main()


