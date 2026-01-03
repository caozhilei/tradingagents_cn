#!/usr/bin/env python3
"""
数据库迁移脚本：将所有简短形式的智能体类型转换为完整形式

迁移内容：
1. 工作流配置（workflow_configs）中的 analyst_type 字段
2. 工作流配置中的条件函数名
3. 工具配置（agent_tool_configs）中的 agent_type 字段
4. 工具定义（agent_tools）中的 agent_type 字段
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import get_mongo_db_sync
from tradingagents.utils.logging_init import get_logger
import sys
import io

# 设置标准输出编码为UTF-8，避免Windows控制台编码问题
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

logger = get_logger("migration")

# 类型映射表
TYPE_MAPPING = {
    # 分析师类型
    "market": "market_analyst",
    "fundamentals": "fundamentals_analyst",
    "news": "news_analyst",
    "social": "social_media_analyst",
    # 研究员类型
    "bull": "bull_researcher",
    "bear": "bear_researcher",
    # 管理者类型
    "research": "research_manager",
    "risk": "risk_manager",
    # 风险分析师类型
    "risky": "aggressive_debator",
    "safe": "conservative_debator",
    "neutral": "neutral_debator"
}

# 条件函数名映射表
FUNCTION_MAPPING = {
    "should_continue_market": "should_continue_market_analyst",
    "should_continue_fundamentals": "should_continue_fundamentals_analyst",
    "should_continue_news": "should_continue_news_analyst",
    "should_continue_social": "should_continue_social_media_analyst"
}


def migrate_workflow_configs(db):
    """迁移工作流配置"""
    logger.info("开始迁移工作流配置...")
    
    workflow_configs = db["workflow_configs"]
    workflows = list(workflow_configs.find({}))
    
    updated_count = 0
    
    for workflow in workflows:
        updated = False
        
        # 更新节点配置
        for node in workflow.get("nodes", []):
            node_config = node.get("config", {})
            
            # 更新 analyst_type
            if node.get("type") == "analyst":
                old_type = node_config.get("analyst_type")
                if old_type in TYPE_MAPPING:
                    new_type = TYPE_MAPPING[old_type]
                    node_config["analyst_type"] = new_type
                    node_config["agent_type"] = new_type
                    updated = True
                    logger.debug(f"  节点 {node.get('id')}: {old_type} -> {new_type}")
            
            # 更新工具节点和消息清理节点的 analyst_type
            elif node.get("type") in ["tool_node", "message_clear"]:
                old_type = node_config.get("analyst_type")
                if old_type in TYPE_MAPPING:
                    new_type = TYPE_MAPPING[old_type]
                    node_config["analyst_type"] = new_type
                    updated = True
                    logger.debug(f"  节点 {node.get('id')}: {old_type} -> {new_type}")
            
            # 更新 researcher_type
            elif node.get("type") == "researcher":
                old_type = node_config.get("researcher_type")
                if old_type in TYPE_MAPPING:
                    new_type = TYPE_MAPPING[old_type]
                    node_config["researcher_type"] = new_type
                    node_config["agent_type"] = new_type
                    updated = True
                    logger.debug(f"  节点 {node.get('id')}: {old_type} -> {new_type}")
            
            # 更新 manager_type
            elif node.get("type") == "manager":
                old_type = node_config.get("manager_type")
                if old_type in TYPE_MAPPING:
                    new_type = TYPE_MAPPING[old_type]
                    node_config["manager_type"] = new_type
                    node_config["agent_type"] = new_type
                    updated = True
                    logger.debug(f"  节点 {node.get('id')}: {old_type} -> {new_type}")
            
            # 更新 risk_type
            elif node.get("type") == "risk_analyst":
                old_type = node_config.get("risk_type")
                if old_type in TYPE_MAPPING:
                    new_type = TYPE_MAPPING[old_type]
                    node_config["risk_type"] = new_type
                    node_config["agent_type"] = new_type
                    updated = True
                    logger.debug(f"  节点 {node.get('id')}: {old_type} -> {new_type}")
            
            # 更新 trader 节点的 agent_type（如果缺失）
            elif node.get("type") == "trader":
                if not node_config.get("agent_type"):
                    node_config["agent_type"] = "trader"
                    updated = True
                    logger.debug(f"  节点 {node.get('id')}: 添加 agent_type = trader")
        
        # 更新条件函数名
        for edge in workflow.get("edges", []):
            if edge.get("type") == "conditional":
                condition = edge.get("condition", {})
                old_func = condition.get("function")
                if old_func in FUNCTION_MAPPING:
                    new_func = FUNCTION_MAPPING[old_func]
                    condition["function"] = new_func
                    updated = True
                    logger.debug(f"  边 {edge.get('id')}: {old_func} -> {new_func}")
        
        # 更新 selected_analysts 参数
        parameters = workflow.get("parameters", {})
        if "selected_analysts" in parameters:
            old_analysts = parameters["selected_analysts"]
            new_analysts = [TYPE_MAPPING.get(a, a) for a in old_analysts]
            if new_analysts != old_analysts:
                parameters["selected_analysts"] = new_analysts
                updated = True
                logger.debug(f"  参数 selected_analysts: {old_analysts} -> {new_analysts}")
        
        if updated:
            workflow_configs.update_one(
                {"_id": workflow["_id"]},
                {"$set": workflow}
            )
            updated_count += 1
            logger.info(f"✅ 已更新工作流: {workflow.get('name', workflow.get('_id'))}")
    
    logger.info(f"✅ 工作流配置迁移完成，共更新 {updated_count} 个工作流")
    return updated_count


def migrate_agent_tool_configs(db):
    """迁移工具配置"""
    logger.info("开始迁移工具配置...")
    
    agent_tool_configs = db["agent_tool_configs"]
    configs = list(agent_tool_configs.find({}))
    
    updated_count = 0
    
    for config in configs:
        old_type = config.get("agent_type")
        if old_type in TYPE_MAPPING:
            new_type = TYPE_MAPPING[old_type]
            agent_tool_configs.update_one(
                {"_id": config["_id"]},
                {"$set": {"agent_type": new_type}}
            )
            updated_count += 1
            logger.debug(f"  工具配置 {config.get('_id')}: {old_type} -> {new_type}")
    
    logger.info(f"✅ 工具配置迁移完成，共更新 {updated_count} 个配置")
    return updated_count


def migrate_agent_tools(db):
    """迁移工具定义"""
    logger.info("开始迁移工具定义...")
    
    agent_tools = db["agent_tools"]
    tools = list(agent_tools.find({}))
    
    updated_count = 0
    
    for tool in tools:
        old_type = tool.get("agent_type")
        if old_type in TYPE_MAPPING:
            new_type = TYPE_MAPPING[old_type]
            agent_tools.update_one(
                {"_id": tool["_id"]},
                {"$set": {"agent_type": new_type}}
            )
            updated_count += 1
            logger.debug(f"  工具定义 {tool.get('_id')}: {old_type} -> {new_type}")
    
    logger.info(f"✅ 工具定义迁移完成，共更新 {updated_count} 个工具")
    return updated_count


def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("开始迁移：简短形式 -> 完整形式")
    logger.info("=" * 60)
    
    try:
        # 获取同步数据库连接
        logger.info("正在连接数据库...")
        db = get_mongo_db_sync()
        logger.info("数据库连接成功")
        
        # 执行迁移
        workflow_count = migrate_workflow_configs(db)
        tool_config_count = migrate_agent_tool_configs(db)
        tool_count = migrate_agent_tools(db)
        
        logger.info("=" * 60)
        logger.info("迁移完成！")
        logger.info(f"  - 工作流配置: {workflow_count} 个")
        logger.info(f"  - 工具配置: {tool_config_count} 个")
        logger.info(f"  - 工具定义: {tool_count} 个")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"迁移失败: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
