#!/usr/bin/env python3
"""
修复模板的系统模板标记
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import get_mongo_db_sync

def fix_system_flag():
    """将所有默认模板标记为系统模板"""
    print("=" * 80)
    print("修复模板的系统模板标记")
    print("=" * 80)
    print()
    
    db = get_mongo_db_sync()
    
    # 查找所有默认模板且创建者为空的模板
    query = {"is_default": True, "created_by": None}
    templates = list(db.prompt_templates.find(query))
    
    print(f"找到 {len(templates)} 个需要修复的模板")
    print()
    
    # 更新为系统模板
    result = db.prompt_templates.update_many(
        query,
        {"$set": {"is_system": True}}
    )
    
    print(f"✅ 已更新 {result.modified_count} 个模板为系统模板")
    print()
    
    # 验证
    system_count = db.prompt_templates.count_documents({"is_system": True})
    print(f"📊 当前系统模板数: {system_count}")
    print()
    
    print("=" * 80)
    print("修复完成")
    print("=" * 80)

if __name__ == "__main__":
    fix_system_flag()

