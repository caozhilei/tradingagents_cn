#!/usr/bin/env python3
"""
初始化默认工作流配置脚本
用于手动初始化默认工作流到数据库

使用方法:
    python scripts/init_workflow.py
    # 或者在Docker中执行:
    docker-compose exec backend python scripts/init_workflow.py
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import init_default_workflow, init_database
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger(__name__)


async def main():
    """初始化默认工作流"""
    logger.info("=" * 60)
    logger.info("初始化默认工作流配置")
    logger.info("=" * 60)
    logger.info("")
    
    try:
        # 初始化数据库连接
        logger.info("🔌 正在初始化数据库连接...")
        await init_database()
        logger.info("✅ 数据库连接成功")
        logger.info("")
        
        # 从数据库管理器获取数据库实例
        from app.core.database import db_manager
        db = db_manager.mongo_db
        
        # 初始化默认工作流
        logger.info("📋 正在初始化默认工作流配置...")
        await init_default_workflow(db)
        
        logger.info("")
        logger.info("=" * 60)
        logger.info("✅ 默认工作流初始化完成！")
        logger.info("=" * 60)
        
        # 验证初始化结果
        collection = db["workflow_configs"]
        existing_default = await collection.find_one({"metadata.is_default": True})
        if existing_default:
            logger.info(f"✅ 验证成功：默认工作流已存在于数据库")
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

