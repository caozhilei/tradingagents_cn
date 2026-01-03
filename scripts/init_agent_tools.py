#!/usr/bin/env python3
"""
初始化智能体工具到数据库
扫描Toolkit中的所有工具并注册到数据库
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import get_mongo_db_sync
from app.services.agent_tool_service import AgentToolService

def main():
    """初始化工具"""
    print("=" * 80)
    print("初始化智能体工具到数据库")
    print("=" * 80)
    print()
    
    try:
        # 初始化数据库连接
        print("🔌 正在连接数据库...")
        db = get_mongo_db_sync()
        print("✅ 数据库连接成功")
        print()
        
        # 创建服务实例
        tool_service = AgentToolService()
        
        # 注册工具
        print("📦 正在注册Toolkit中的所有工具...")
        count = tool_service.register_toolkit_tools()
        
        print()
        print(f"✅ 工具注册完成，共注册 {count} 个工具")
        print()
        
        # 显示注册的工具
        print("📋 已注册的工具列表:")
        tools = tool_service.list_tools(is_active=True)
        for tool in tools:
            print(f"  • {tool.tool_display_name} ({tool.tool_name}) -> {tool.agent_type}")
        
        print()
        print("=" * 80)
        print("初始化完成")
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

