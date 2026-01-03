#!/usr/bin/env python3
"""
数据库迁移脚本：清理多余的特定类型字段
删除 analyst_type、researcher_type、manager_type、risk_type 字段，只保留 agent_type

迁移内容：
1. 工作流配置（workflow_configs）中所有节点的 config 字段
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

# 需要删除的字段列表
REDUNDANT_FIELDS = [
    "analyst_type",
    "researcher_type",
    "manager_type",
    "risk_type"
]


def clean_node_config(node_config: dict) -> dict:
    """
    清理节点配置，移除多余的特定类型字段
    
    Args:
        node_config: 节点配置字典
        
    Returns:
        清理后的节点配置字典
    """
    if not isinstance(node_config, dict):
        return node_config
    
    cleaned = node_config.copy()
    config = cleaned.get("config", {})
    
    if isinstance(config, dict):
        # 移除特定类型字段
        config_cleaned = config.copy()
        for field in REDUNDANT_FIELDS:
            config_cleaned.pop(field, None)
        cleaned["config"] = config_cleaned
    
    return cleaned


def migrate_workflow_configs(db):
    """迁移工作流配置，清理多余的特定类型字段"""
    logger.info("开始清理工作流配置中的多余字段...")
    
    workflow_configs = db["workflow_configs"]
    workflows = list(workflow_configs.find({}))
    
    updated_count = 0
    cleaned_nodes_count = 0
    
    for workflow in workflows:
        updated = False
        nodes = workflow.get("nodes", [])
        
        # 清理每个节点的配置
        cleaned_nodes = []
        for node in nodes:
            original_config = node.get("config", {})
            
            # 检查是否有需要清理的字段
            has_redundant_fields = any(
                field in original_config 
                for field in REDUNDANT_FIELDS
            )
            
            if has_redundant_fields:
                cleaned_node = clean_node_config(node)
                cleaned_nodes.append(cleaned_node)
                cleaned_nodes_count += 1
                
                # 记录清理的字段
                removed_fields = [
                    field for field in REDUNDANT_FIELDS 
                    if field in original_config
                ]
                logger.debug(
                    f"  节点 {node.get('id')}: 移除字段 {', '.join(removed_fields)}"
                )
                updated = True
            else:
                cleaned_nodes.append(node)
        
        if updated:
            workflow["nodes"] = cleaned_nodes
            workflow_configs.update_one(
                {"_id": workflow["_id"]},
                {"$set": {"nodes": cleaned_nodes}}
            )
            updated_count += 1
            logger.info(f"[OK] 已清理工作流: {workflow.get('name', workflow.get('_id'))}")
    
    logger.info(f"[OK] 工作流配置清理完成，共更新 {updated_count} 个工作流，清理 {cleaned_nodes_count} 个节点")
    return updated_count, cleaned_nodes_count


def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("开始清理：删除多余的特定类型字段")
    logger.info("=" * 60)
    
    try:
        # 获取同步数据库连接
        logger.info("正在连接数据库...")
        db = get_mongo_db_sync()
        logger.info("数据库连接成功")
        
        # 执行迁移
        workflow_count, nodes_count = migrate_workflow_configs(db)
        
        logger.info("=" * 60)
        logger.info("清理完成！")
        logger.info(f"  - 工作流配置: {workflow_count} 个")
        logger.info(f"  - 清理节点: {nodes_count} 个")
        logger.info(f"  - 删除字段: {', '.join(REDUNDANT_FIELDS)}")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"清理失败: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
