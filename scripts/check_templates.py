#!/usr/bin/env python3
"""
检查数据库中的提示词模板，并对比硬编码的提示词
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import get_mongo_db_sync
from app.services.prompt_template_service import PromptTemplateService
from bson import ObjectId

def check_templates():
    """检查数据库中的模板"""
    print("=" * 80)
    print("检查数据库中的提示词模板")
    print("=" * 80)
    print()
    
    db = get_mongo_db_sync()
    template_service = PromptTemplateService()
    
    # 统计信息
    total_count = db.prompt_templates.count_documents({})
    system_count = db.prompt_templates.count_documents({"is_system": True})
    default_count = db.prompt_templates.count_documents({"is_default": True})
    active_count = db.prompt_templates.count_documents({"is_active": True})
    
    print(f"📊 模板统计:")
    print(f"  总模板数: {total_count}")
    print(f"  系统模板数: {system_count}")
    print(f"  默认模板数: {default_count}")
    print(f"  启用模板数: {active_count}")
    print()
    
    # 按智能体类型分组
    print("📋 按智能体类型分组:")
    pipeline = [
        {"$group": {
            "_id": "$agent_type",
            "count": {"$sum": 1},
            "system": {"$sum": {"$cond": ["$is_system", 1, 0]}},
            "default": {"$sum": {"$cond": ["$is_default", 1, 0]}}
        }},
        {"$sort": {"_id": 1}}
    ]
    
    for group in db.prompt_templates.aggregate(pipeline):
        agent_type = group["_id"]
        count = group["count"]
        system = group["system"]
        default = group["default"]
        print(f"  {agent_type}:")
        print(f"    总数: {count}, 系统模板: {system}, 默认模板: {default}")
    print()
    
    # 列出所有模板
    print("📝 所有模板列表:")
    templates = list(db.prompt_templates.find({}).sort("agent_type", 1))
    
    for i, template in enumerate(templates, 1):
        print(f"\n模板 {i}:")
        print(f"  ID: {template.get('_id')}")
        print(f"  智能体类型: {template.get('agent_type')}")
        print(f"  智能体名称: {template.get('agent_name')}")
        print(f"  模板名称: {template.get('template_name')}")
        print(f"  显示名称: {template.get('template_display_name')}")
        print(f"  描述: {template.get('description', '无')}")
        print(f"  版本: {template.get('version', 1)}")
        print(f"  系统模板: {template.get('is_system', False)}")
        print(f"  默认模板: {template.get('is_default', False)}")
        print(f"  启用: {template.get('is_active', True)}")
        print(f"  创建者: {template.get('created_by', '系统')}")
        
        # 检查内容
        content = template.get('content', {})
        if content:
            system_prompt = content.get('system_prompt', '')
            if system_prompt:
                preview = system_prompt[:100] + "..." if len(system_prompt) > 100 else system_prompt
                print(f"  系统提示词预览: {preview}")
    
    print()
    print("=" * 80)
    print("检查完成")
    print("=" * 80)

if __name__ == "__main__":
    check_templates()

