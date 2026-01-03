#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工具初始化脚本
从Toolkit类扫描并初始化工具到数据库
"""

import asyncio
import sys
import argparse
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import init_database, get_mongo_db, close_database
from app.services.tool_config_service import ToolConfigService


async def initialize_tools():
    """初始化工具到数据库"""
    print("=" * 60)
    print("工具初始化脚本")
    print("=" * 60)
    print()
    
    # 初始化数据库
    print("🔌 正在连接数据库...")
    await init_database()
    print("✅ 数据库连接成功")
    print()
    
    # 初始化工具配置服务
    tool_service = ToolConfigService()
    
    # 初始化工具
    print("🔄 开始初始化工具...")
    print()
    
    try:
        result = tool_service.initialize_tools_from_toolkit()
        
        print()
        print("=" * 60)
        print("工具初始化完成")
        print("=" * 60)
        print(f"✅ 成功初始化: {result['initialized']} 个工具")
        print(f"⏭️  跳过: {result['skipped']} 个工具")
        print(f"⚠️  错误: {result['errors']} 个工具")
        print()
        
    except Exception as e:
        print(f"❌ 工具初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # 关闭数据库连接
        await close_database()
    
    return True


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="初始化工具到数据库"
    )
    
    args = parser.parse_args()
    
    success = asyncio.run(initialize_tools())
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
