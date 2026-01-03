#!/usr/bin/env python3
"""
测试工作流配置验证逻辑
直接测试 ConfigBasedGraphBuilder.validate_config 方法，不需要数据库连接
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from tradingagents.graph.config_based_builder import ConfigBasedGraphBuilder
from tradingagents.graph.workflow_config import WorkflowConfig

# 测试用的工作流配置示例
test_workflow_config = {
    "version": "1.0",
    "name": "测试工作流",
    "description": "用于测试验证逻辑的工作流",
    "nodes": [
        {
            "id": "market_analyst",
            "name": "Market Analyst",
            "type": "analyst",
            "category": "analyst",
            "config": {
                "agent_type": "market_analyst",
                "analyst_type": "market_analyst"
            }
        },
        {
            "id": "fundamentals_analyst",
            "name": "Fundamentals Analyst",
            "type": "analyst",
            "category": "analyst",
            "config": {
                "agent_type": "fundamentals_analyst",
                "analyst_type": "fundamentals_analyst"
            }
        },
        {
            "id": "research_manager",
            "name": "Research Manager",
            "type": "manager",
            "category": "manager",
            "config": {
                "agent_type": "research_manager",
                "manager_type": "research"
            }
        },
        {
            "id": "trader",
            "name": "Trader",
            "type": "trader",
            "category": "trader",
            "config": {
                "agent_type": "trader"
            }
        }
    ],
    "edges": [
        {
            "id": "edge1",
            "source": "START",
            "target": "market_analyst",
            "type": "direct"
        },
        {
            "id": "edge2",
            "source": "market_analyst",
            "target": "fundamentals_analyst",
            "type": "direct"
        },
        {
            "id": "edge3",
            "source": "fundamentals_analyst",
            "target": "research_manager",
            "type": "direct"
        },
        {
            "id": "edge4",
            "source": "research_manager",
            "target": "trader",
            "type": "direct"
        },
        {
            "id": "edge5",
            "source": "trader",
            "target": "END",
            "type": "direct"
        }
    ],
    "parameters": {},
    "metadata": {
        "is_default": True,
        "author": "test",
        "created_at": "2026-01-03T00:00:00Z",
        "updated_at": "2026-01-03T00:00:00Z"
    }
}

def test_validation():
    """测试验证逻辑"""
    print("🔍 开始测试工作流配置验证逻辑...")
    
    try:
        # 创建配置对象
        config = WorkflowConfig(**test_workflow_config)
        print("✅ 成功创建 WorkflowConfig 对象")
        
        # 创建验证器
        validator = ConfigBasedGraphBuilder()
        print("✅ 成功创建 ConfigBasedGraphBuilder 对象")
        
        # 执行验证
        errors = validator.validate_config(config)
        
        if errors:
            print(f"❌ 验证失败，发现 {len(errors)} 个错误:")
            for error in errors:
                print(f"   - {error}")
            return False
        else:
            print("✅ 验证通过，未发现错误")
            return True
            
    except Exception as e:
        print(f"💥 测试过程中出现异常: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_validation()
    sys.exit(0 if success else 1)
