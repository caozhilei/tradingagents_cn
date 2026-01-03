#!/usr/bin/env python3
"""
验证脚本：检查数据库中是否还有多余的特定类型字段
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import get_mongo_db_sync
import sys
import io

# 设置标准输出编码为UTF-8，避免Windows控制台编码问题
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 需要检查的字段列表
REDUNDANT_FIELDS = [
    "analyst_type",
    "researcher_type",
    "manager_type",
    "risk_type"
]


def check_workflow_configs(db):
    """检查工作流配置中是否还有多余的特定类型字段"""
    print("检查工作流配置...")
    
    workflow_configs = db["workflow_configs"]
    workflows = list(workflow_configs.find({}))
    
    found_redundant = False
    total_nodes_checked = 0
    nodes_with_redundant_fields = 0
    
    for workflow in workflows:
        workflow_name = workflow.get("name", str(workflow.get("_id")))
        nodes = workflow.get("nodes", [])
        
        for node in nodes:
            total_nodes_checked += 1
            config = node.get("config", {})
            
            # 检查是否有需要清理的字段
            redundant_in_node = []
            for field in REDUNDANT_FIELDS:
                if field in config:
                    redundant_in_node.append(field)
            
            if redundant_in_node:
                found_redundant = True
                nodes_with_redundant_fields += 1
                node_id = node.get("id", "unknown")
                print(f"  [X] 工作流 '{workflow_name}' 节点 '{node_id}' 仍包含字段: {', '.join(redundant_in_node)}")
    
    if not found_redundant:
        print(f"  [OK] 所有 {total_nodes_checked} 个节点配置都已清理，没有多余的特定类型字段")
    else:
        print(f"  [X] 发现 {nodes_with_redundant_fields} 个节点仍包含多余的特定类型字段")
    
    return not found_redundant


def main():
    """主函数"""
    print("=" * 60)
    print("验证：检查多余的特定类型字段是否已删除")
    print("=" * 60)
    
    try:
        # 获取同步数据库连接
        print("正在连接数据库...")
        db = get_mongo_db_sync()
        print("数据库连接成功\n")
        
        # 检查工作流配置
        all_clean = check_workflow_configs(db)
        
        print("\n" + "=" * 60)
        if all_clean:
            print("验证通过：所有多余的特定类型字段已成功删除")
        else:
            print("验证失败：仍有节点包含多余的特定类型字段")
            sys.exit(1)
        print("=" * 60)
        
    except Exception as e:
        print(f"验证失败: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
