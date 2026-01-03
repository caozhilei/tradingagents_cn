#!/usr/bin/env python3
"""验证默认工作流配置"""

import asyncio
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import init_database, db_manager
import json

async def main():
    await init_database()
    db = db_manager.mongo_db
    collection = db["workflow_configs"]
    
    workflow = await collection.find_one({"metadata.is_default": True})
    if not workflow:
        print("❌ 未找到默认工作流")
        return
    
    print(f"✅ 工作流名称: {workflow.get('name')}")
    print(f"✅ 节点数量: {len(workflow.get('nodes', []))}")
    print(f"✅ 边数量: {len(workflow.get('edges', []))}")
    print("\n📊 节点列表:")
    for node in workflow.get('nodes', []):
        print(f"  - {node.get('id')} ({node.get('name', 'N/A')}) [{node.get('type', 'N/A')}]")
    
    print("\n🔗 边列表:")
    for edge in workflow.get('edges', []):
        edge_type = edge.get('type', 'direct')
        source = edge.get('source', 'N/A')
        target = edge.get('target', 'N/A')
        print(f"  - {source} -> {target} [{edge_type}]")
        if edge_type == 'conditional' and edge.get('condition'):
            cond = edge['condition']
            print(f"      条件函数: {cond.get('function', 'N/A')}")
            print(f"      映射: {cond.get('mapping', {})}")

if __name__ == "__main__":
    asyncio.run(main())

