#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
更新默认工作流的智能体节点版本和中文名称

这个脚本会：
1. 将所有智能体节点的模板版本设置为用户在提示词设置中选择的默认版本
2. 将所有节点名称更新为中文显示名称

使用方法:
    python scripts/update_default_workflow.py [--user-id USER_ID]
"""

import asyncio
import sys
import argparse
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
from bson import ObjectId

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import init_database, get_mongo_db, close_database
from app.services.prompt_template_service import PromptTemplateService
from tradingagents.graph.workflow_config import WorkflowConfig, NodeConfig

# 智能体类型和中文名称映射（与 API 保持一致）
AGENT_TYPES_MAP = {
    "analysts": [
        {"type": "fundamentals_analyst", "name": "基本面分析师"},
        {"type": "market_analyst", "name": "市场分析师"},
        {"type": "news_analyst", "name": "新闻分析师"},
        {"type": "social_media_analyst", "name": "社媒分析师"},
    ],
    "researchers": [
        {"type": "bull_researcher", "name": "看涨研究员"},
        {"type": "bear_researcher", "name": "看跌研究员"},
    ],
    "trader": [
        {"type": "trader", "name": "交易员"},
    ],
    "risk_management": [
        {"type": "aggressive_debator", "name": "激进辩手"},
        {"type": "conservative_debator", "name": "保守辩手"},
        {"type": "neutral_debator", "name": "中立辩手"},
    ],
    "managers": [
        {"type": "research_manager", "name": "研究经理"},
        {"type": "risk_manager", "name": "风险经理"},
    ]
}


# 节点名称到 agent_type 的映射
NODE_NAME_TO_AGENT_TYPE = {
    # 分析师
    "Market Analyst": "market_analyst",
    "Social Analyst": "social_media_analyst",
    "News Analyst": "news_analyst",
    "Fundamentals Analyst": "fundamentals_analyst",
    # 研究员
    "Bull Researcher": "bull_researcher",
    "Bear Researcher": "bear_researcher",
    # 交易员
    "Trader": "trader",
    # 风险管理
    "Risky Analyst": "aggressive_debator",
    "Safe Analyst": "conservative_debator",
    "Neutral Analyst": "neutral_debator",
    # 管理者
    "Research Manager": "research_manager",
    "Risk Judge": "risk_manager",
}


def infer_agent_type_from_config(node_name: str, node_type: str, config: dict) -> Optional[str]:
    """
    从节点名称和配置推断 agent_type
    
    Args:
        node_name: 节点名称（如 'Market Analyst', 'Bull Researcher' 等）
        node_type: 节点类型（如 'analyst', 'researcher' 等）
        config: 节点配置字典
        
    Returns:
        agent_type 字符串，如果无法推断则返回 None
    """
    # 如果 config.agent_type 存在，直接返回
    if config.get("agent_type"):
        return config["agent_type"]
    
    # 首先尝试从节点名称推断
    if node_name in NODE_NAME_TO_AGENT_TYPE:
        return NODE_NAME_TO_AGENT_TYPE[node_name]
    
    # 根据 node_type 和配置字段推断
    if node_type == "analyst" and config.get("analyst_type"):
        analyst_type = config["analyst_type"]
        # 映射简写形式到完整形式
        analyst_type_map = {
            "market": "market_analyst",
            "social": "social_media_analyst",
            "news": "news_analyst",
            "fundamentals": "fundamentals_analyst",
        }
        return analyst_type_map.get(analyst_type, analyst_type)
    if node_type == "researcher" and config.get("researcher_type"):
        researcher_type = config["researcher_type"]
        researcher_type_map = {
            "bull": "bull_researcher",
            "bear": "bear_researcher",
        }
        return researcher_type_map.get(researcher_type, researcher_type)
    if node_type == "trader":
        # trader 类型通常只有一个，返回 'trader' 作为默认值
        return config.get("trader_type", "trader")
    if node_type == "risk_analyst" and config.get("risk_type"):
        risk_type = config["risk_type"]
        risk_type_map = {
            "risky": "aggressive_debator",
            "safe": "conservative_debator",
            "neutral": "neutral_debator",
        }
        return risk_type_map.get(risk_type, risk_type)
    if node_type == "manager" and config.get("manager_type"):
        manager_type = config["manager_type"]
        manager_type_map = {
            "research": "research_manager",
            "risk": "risk_manager",
        }
        return manager_type_map.get(manager_type, manager_type)
    
    # 无法推断
    return None


def get_agent_chinese_name(agent_type: str) -> Optional[str]:
    """
    获取智能体的中文名称
    
    Args:
        agent_type: 智能体类型
        
    Returns:
        中文名称，如果找不到则返回 None
    """
    # 遍历所有类别查找匹配的智能体
    for category, agents in AGENT_TYPES_MAP.items():
        for agent in agents:
            if agent["type"] == agent_type:
                return agent["name"]
    return None


def get_default_template_for_agent(
    template_service: PromptTemplateService,
    agent_type: str,
    user_id: Optional[ObjectId] = None
) -> Optional[Dict[str, Any]]:
    """
    获取智能体的默认模板
    
    Args:
        template_service: 模板服务实例
        agent_type: 智能体类型
        user_id: 用户ID（可选，如果提供则优先获取用户配置的模板）
        
    Returns:
        包含 id, version, template_display_name 的字典，如果找不到则返回 None
    """
    try:
        template = None
        
        # 首先尝试获取用户配置的模板
        if user_id:
            template = template_service.get_user_template(user_id, agent_type)
        
        # 如果没有用户配置，获取系统默认模板
        if not template:
            template = template_service.get_default_template(agent_type)
        
        if template:
            return {
                "id": str(template.id),
                "version": template.version,
                "template_display_name": template.template_display_name
            }
        
        return None
    except Exception as e:
        print(f"⚠️  获取智能体 {agent_type} 的默认模板失败: {e}")
        return None


async def update_default_workflow(user_id: Optional[str] = None):
    """
    更新默认工作流的智能体节点版本和中文名称
    
    Args:
        user_id: 用户ID（可选），如果提供则使用该用户的模板配置
    """
    print("=" * 60)
    print("更新默认工作流的智能体节点版本和中文名称")
    print("=" * 60)
    print()
    
    # 初始化数据库
    print("🔌 正在连接数据库...")
    await init_database()
    db = get_mongo_db()
    collection = db.workflow_configs
    print("✅ 数据库连接成功")
    print()
    
    # 初始化模板服务
    template_service = PromptTemplateService()
    
    # 转换 user_id
    user_object_id = None
    if user_id:
        try:
            user_object_id = ObjectId(user_id)
            print(f"👤 使用用户ID: {user_id}")
        except Exception:
            print(f"⚠️  无效的用户ID格式: {user_id}，将使用系统默认模板")
            user_object_id = None
    else:
        print("🌐 使用系统默认模板")
    print()
    
    # 查找默认工作流
    print("📋 正在查找默认工作流...")
    doc = await collection.find_one({"metadata.is_default": True})
    
    if not doc:
        print("❌ 未找到默认工作流")
        return
    
    workflow_id = doc["_id"]
    workflow_name = doc.get("name", "未知")
    print(f"✅ 找到默认工作流: {workflow_name} (ID: {workflow_id})")
    print()
    
    # 解析工作流配置
    try:
        config = WorkflowConfig(**doc)
    except Exception as e:
        print(f"❌ 解析工作流配置失败: {e}")
        return
    
    # 统计信息
    updated_nodes = 0
    skipped_nodes = 0
    error_nodes = 0
    
    print("🔄 开始更新节点...")
    print()
    
    # 遍历每个节点
    for i, node in enumerate(config.nodes, 1):
        # 处理 NodeType 枚举
        if hasattr(node.type, 'value'):
            node_type = node.type.value
        elif isinstance(node.type, str):
            node_type = node.type
        else:
            node_type = str(node.type)
        
        node_id = node.id
        node_name = node.name
        
        print(f"[{i}/{len(config.nodes)}] 节点: {node_name} (类型: {node_type})")
        
        # 判断是否为智能体节点
        if node_type not in ["analyst", "researcher", "trader", "risk_analyst", "manager"]:
            print(f"  ⏭️  跳过非智能体节点")
            skipped_nodes += 1
            print()
            continue
        
        # 推断 agent_type
        node_config = node.config or {}
        agent_type = infer_agent_type_from_config(node_name, node_type, node_config)
        
        if not agent_type:
            print(f"  ⚠️  无法推断 agent_type，跳过")
            error_nodes += 1
            print()
            continue
        
        print(f"  🔍 推断的 agent_type: {agent_type}")
        
        # 获取默认模板
        template_info = get_default_template_for_agent(
            template_service,
            agent_type,
            user_object_id
        )
        
        if not template_info:
            print(f"  ⚠️  未找到默认模板，跳过")
            error_nodes += 1
            print()
            continue
        
        print(f"  📝 模板: {template_info['template_display_name']} (版本: {template_info['version']})")
        
        # 获取中文名称
        chinese_name = get_agent_chinese_name(agent_type)
        if not chinese_name:
            print(f"  ⚠️  未找到中文名称，保持原有名称: {node_name}")
            chinese_name = node_name
        
        # 更新节点配置
        node.config = node_config.copy()
        node.config["template_id"] = template_info["id"]
        node.config["template_version"] = template_info["version"]
        node.config["template_name"] = template_info["template_display_name"]
        node.name = chinese_name
        
        print(f"  ✅ 已更新: 名称={chinese_name}, template_id={template_info['id']}, version={template_info['version']}")
        updated_nodes += 1
        print()
    
    # 保存更新后的工作流配置
    print("💾 正在保存更新后的工作流配置...")
    
    # 更新数据库
    # 将节点转换为字典格式
    nodes_data = []
    for node in config.nodes:
        node_dict = {
            "id": node.id,
            "type": node.type.value if hasattr(node.type, 'value') else str(node.type),
            "name": node.name,
            "category": node.category,
            "config": node.config,
            "position": node.position
        }
        nodes_data.append(node_dict)
    
    # 获取现有 metadata
    existing_metadata = doc.get("metadata", {})
    if not isinstance(existing_metadata, dict):
        existing_metadata = {}
    existing_metadata["updated_at"] = datetime.now().isoformat()
    
    update_data = {
        "nodes": nodes_data,
        "metadata": existing_metadata
    }
    
    result = await collection.update_one(
        {"_id": workflow_id},
        {"$set": update_data}
    )
    
    if result.modified_count > 0:
        print("✅ 工作流配置已保存")
    else:
        print("⚠️  工作流配置未更改")
    
    print()
    print("=" * 60)
    print("更新完成")
    print("=" * 60)
    print(f"✅ 成功更新: {updated_nodes} 个节点")
    print(f"⏭️  跳过: {skipped_nodes} 个节点")
    print(f"⚠️  错误: {error_nodes} 个节点")
    print()
    
    # 关闭数据库连接
    await close_database()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="更新默认工作流的智能体节点版本和中文名称"
    )
    parser.add_argument(
        "--user-id",
        type=str,
        help="用户ID（可选），如果提供则使用该用户的模板配置"
    )
    
    args = parser.parse_args()
    
    asyncio.run(update_default_workflow(user_id=args.user_id))


if __name__ == "__main__":
    main()
