#!/usr/bin/env python3
"""
重新初始化默认工作流配置脚本
删除现有默认工作流并重新创建
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import init_database, db_manager, init_default_workflow
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger(__name__)


async def main():
    """重新初始化默认工作流"""
    logger.info("=" * 60)
    logger.info("重新初始化默认工作流配置")
    logger.info("=" * 60)
    logger.info("")
    
    try:
        # 初始化数据库连接
        logger.info("🔌 正在初始化数据库连接...")
        await init_database()
        logger.info("✅ 数据库连接成功")
        logger.info("")
        
        # 获取数据库实例
        db = db_manager.mongo_db
        
        # 强制重新创建默认工作流
        logger.info("📋 正在强制重新创建默认工作流配置...")
        await init_default_workflow(db, force_recreate=True)
        
        logger.info("")
        logger.info("=" * 60)
        logger.info("✅ 默认工作流重新初始化完成！")
        logger.info("=" * 60)
        
        # 验证初始化结果
        collection = db["workflow_configs"]
        existing_default = await collection.find_one({"metadata.is_default": True})
        if existing_default:
            logger.info("")
            logger.info("📊 验证结果:")
            logger.info(f"   工作流ID: {existing_default.get('_id')}")
            logger.info(f"   工作流名称: {existing_default.get('name', 'N/A')}")
            logger.info(f"   节点数量: {len(existing_default.get('nodes', []))}")
            logger.info(f"   边数量: {len(existing_default.get('edges', []))}")
        else:
            logger.warning("⚠️ 警告：初始化后未找到默认工作流")
        
    except Exception as e:
        logger.error(f"❌ 初始化失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
