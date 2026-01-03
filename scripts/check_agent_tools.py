#!/usr/bin/env python3
"""
检查已注册的智能体工具
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import get_mongo_db_sync
from app.services.agent_tool_service import AgentToolService

def main():
    """检查工具"""
    print("=" * 80)
    print("检查已注册的智能体工具")
    print("=" * 80)
    print()
    
    db = get_mongo_db_sync()
    tool_service = AgentToolService()
    
    # 统计信息
    total_count = db.agent_tools.count_documents({})
    print(f"📊 工具统计:")
    print(f"  总工具数: {total_count}")
    print()
    
    # 按智能体类型分组
    print("📋 按智能体类型分组:")
    pipeline = [
        {"$group": {
            "_id": "$agent_type",
            "count": {"$sum": 1},
            "default": {"$sum": {"$cond": ["$is_default", 1, 0]}}
        }},
        {"$sort": {"_id": 1}}
    ]
    
    for group in db.agent_tools.aggregate(pipeline):
        agent_type = group["_id"]
        count = group["count"]
        default = group["default"]
        print(f"  {agent_type}:")
        print(f"    总数: {count}, 默认工具: {default}")
    print()
    
    # 显示默认工具
    print("⭐ 默认工具列表:")
    default_tools = tool_service.list_tools(is_active=True)
    default_tools = [t for t in default_tools if t.is_default]
    default_tools.sort(key=lambda x: (x.agent_type, -x.priority))
    
    for tool in default_tools:
        print(f"  • {tool.tool_display_name} ({tool.tool_name})")
        print(f"    -> {tool.agent_type} [优先级: {tool.priority}]")
    print()
    
    print("=" * 80)
    print("检查完成")
    print("=" * 80)

if __name__ == "__main__":
    main()

