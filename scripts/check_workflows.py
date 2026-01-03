#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
查询工作流列表脚本
"""

import asyncio
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import init_database, get_mongo_db


async def main():
    await init_database()
    db = get_mongo_db()
    collection = db.workflow_configs
    
    count = await collection.count_documents({})
    print(f"Total workflows: {count}")
    
    if count == 0:
        print("No workflows found")
        return
    
    cursor = collection.find({}, {"name": 1, "description": 1, "metadata": 1})
    workflows = []
    async for doc in cursor:
        workflows.append({
            "id": str(doc["_id"]),
            "name": doc.get("name", ""),
            "description": doc.get("description"),
            "updated_at": doc.get("metadata", {}).get("updated_at", "")
        })
    
    print(f"\nFound {len(workflows)} workflows:")
    for i, w in enumerate(workflows, 1):
        print(f"{i}. {w['name']}")
        print(f"   ID: {w['id']}")
        if w.get('description'):
            print(f"   Description: {w['description']}")
        print(f"   Updated: {w.get('updated_at', 'N/A')}")
        print()


if __name__ == "__main__":
    asyncio.run(main())
