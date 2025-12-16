#!/usr/bin/env python3
"""快速创建管理员用户脚本"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from motor.motor_asyncio import AsyncIOMotorClient
import hashlib
from datetime import datetime

def hash_password(password: str) -> str:
    """密码哈希 - 使用 SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def now_tz():
    """获取当前时间"""
    return datetime.utcnow()

async def create_admin_user():
    """创建管理员用户"""
    try:
        # 连接 MongoDB
        client = AsyncIOMotorClient(
            "mongodb://admin:tradingagents123@mongodb:27017/tradingagents?authSource=admin"
        )
        db = client["tradingagents"]
        
        # 检查是否已存在管理员用户
        existing = await db.users.find_one({"username": "admin"})
        if existing:
            print("✓ 管理员用户已存在")
            print(f"  用户名: admin")
            # 检查密码字段
            if "hashed_password" in existing:
                print("  密码: admin123 (已加密)")
            elif "password" in existing:
                print(f"  密码: {existing.get('password', '未知')}")
            return
        
        # 创建管理员用户
        admin_user = {
            "username": "admin",
            "email": "admin@tradingagents.cn",
            "hashed_password": hash_password("admin123"),
            "full_name": "系统管理员",
            "role": "admin",
            "is_active": True,
            "is_superuser": True,
            "is_admin": True,
            "is_verified": True,
            "created_at": now_tz(),
            "updated_at": now_tz(),
            "preferences": {
                "default_market": "A股",
                "default_depth": "深度",
                "ui_theme": "light",
                "language": "zh-CN",
                "notifications_enabled": True,
                "email_notifications": False
            },
            "daily_quota": 10000,
            "concurrent_limit": 10,
            "total_analyses": 0,
            "successful_analyses": 0,
            "failed_analyses": 0,
            "favorite_stocks": []
        }
        
        result = await db.users.insert_one(admin_user)
        print("✅ 创建管理员用户成功！")
        print("  用户名: admin")
        print("  密码: admin123")
        print("  ⚠️  请在首次登录后立即修改密码！")
        
    except Exception as e:
        print(f"❌ 创建管理员用户失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        if 'client' in locals():
            client.close()

if __name__ == "__main__":
    asyncio.run(create_admin_user())

