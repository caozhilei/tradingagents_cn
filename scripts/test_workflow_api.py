#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试工作流 API 返回格式
"""

import asyncio
import sys
import json
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import init_database, get_mongo_db
from app.routers.workflow_config import WorkflowListItem


async def main():
    await init_database()
    db = get_mongo_db()
    collection = db.workflow_configs
    
    cursor = collection.find(
        {},
        {"name": 1, "description": 1, "metadata": 1, "created_at": 1, "updated_at": 1}
    ).sort("metadata.updated_at", -1)
    
    workflows = []
    async for doc in cursor:
        item = WorkflowListItem(
            id=str(doc["_id"]),
            name=doc.get("name", ""),
            description=doc.get("description"),
            created_at=doc.get("metadata", {}).get("created_at", ""),
            updated_at=doc.get("metadata", {}).get("updated_at", ""),
            author=doc.get("metadata", {}).get("author")
        )
        workflows.append(item)
    
    print("API 返回格式:")
    print(json.dumps([w.model_dump() for w in workflows], indent=2, ensure_ascii=False))
    print(f"\n返回类型: {type(workflows)}")
    print(f"是否为列表: {isinstance(workflows, list)}")
    print(f"列表长度: {len(workflows)}")


if __name__ == "__main__":
    asyncio.run(main())
