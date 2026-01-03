#!/usr/bin/env python3
"""
验证迁移结果：检查数据库中的智能体类型是否已转换为完整形式
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import get_mongo_db_sync

def main():
    db = get_mongo_db_sync()
    
    # 检查工作流配置
    workflows = list(db.workflow_configs.find({}))
    print(f"找到 {len(workflows)} 个工作流配置")
    
    for wf in workflows:
        print(f"\n工作流: {wf.get('name', 'Unknown')}")
        nodes = wf.get('nodes', [])
        print(f"  节点数量: {len(nodes)}")
        
        short_forms_found = []
        for node in nodes:
            config = node.get('config', {})
            node_type = node.get('type')
            node_id = node.get('id', 'unknown')
            
            # 检查各种类型字段
            for field in ['analyst_type', 'researcher_type', 'manager_type', 'risk_type', 'agent_type']:
                value = config.get(field)
                if value:
                    # 检查是否是简短形式
                    short_forms = ['market', 'fundamentals', 'news', 'social', 'bull', 'bear', 
                                  'research', 'risk', 'risky', 'safe', 'neutral']
                    if value in short_forms:
                        short_forms_found.append(f"{node_id}.{field}={value}")
                    else:
                        print(f"    [OK] {node_id}.{field} = {value} (完整形式)")
        
        if short_forms_found:
            print(f"  [WARN] 发现简短形式: {', '.join(short_forms_found)}")
        else:
            print(f"  [OK] 所有类型字段都是完整形式")
    
    # 检查工具配置
    tool_configs = list(db.agent_tool_configs.find({}))
    print(f"\n找到 {len(tool_configs)} 个工具配置")
    for tc in tool_configs:
        agent_type = tc.get('agent_type')
        if agent_type:
            short_forms = ['market', 'fundamentals', 'news', 'social', 'bull', 'bear', 
                          'research', 'risk', 'risky', 'safe', 'neutral']
            if agent_type in short_forms:
                print(f"  [WARN] {tc.get('_id')}: agent_type={agent_type} (简短形式)")
            else:
                print(f"  [OK] {tc.get('_id')}: agent_type={agent_type} (完整形式)")
    
    # 检查工具定义
    tools = list(db.agent_tools.find({}))
    print(f"\n找到 {len(tools)} 个工具定义")
    for tool in tools:
        agent_type = tool.get('agent_type')
        if agent_type:
            short_forms = ['market', 'fundamentals', 'news', 'social', 'bull', 'bear', 
                          'research', 'risk', 'risky', 'safe', 'neutral']
            if agent_type in short_forms:
                print(f"  [WARN] {tool.get('_id')}: agent_type={agent_type} (简短形式)")
            else:
                print(f"  [OK] {tool.get('_id')}: agent_type={agent_type} (完整形式)")

if __name__ == "__main__":
    main()
