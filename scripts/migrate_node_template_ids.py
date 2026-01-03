"""
节点模板ID对齐迁移脚本

将数据库中所有工作流节点的 template_id 对齐到对应智能体类型的默认模板。

使用方法：
    python scripts/migrate_node_template_ids.py [--dry-run] [--verbose]

参数：
    --dry-run    仅显示将要更新的内容，不实际修改数据库
    --verbose    显示详细的更新信息
"""

import sys
import os
import argparse
import logging
from typing import Dict, Any, List, Optional
from bson import ObjectId
from datetime import datetime

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

# 强制使用 localhost 连接 Docker 容器内的 MongoDB
# 必须在导入 app 模块之前设置，因为 settings 在导入时就会读取环境变量
os.environ['MONGODB_HOST'] = 'localhost'
os.environ['MONGODB_PORT'] = '27017'
os.environ['MONGODB_USERNAME'] = 'admin'
os.environ['MONGODB_PASSWORD'] = 'tradingagents123'
os.environ['MONGODB_DATABASE'] = 'tradingagents'
os.environ['MONGODB_AUTH_SOURCE'] = 'admin'

# 现在导入 app 模块（此时环境变量已设置）
from app.core.database import get_mongo_db_sync
from app.services.prompt_template_service import PromptTemplateService
from app.models.prompt_template import PromptTemplate

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class NodeTemplateMigrator:
    """节点模板ID迁移器"""
    
    def __init__(self, dry_run: bool = False, verbose: bool = False):
        self.dry_run = dry_run
        self.verbose = verbose
        self.db = get_mongo_db_sync()
        self.workflow_collection = self.db.workflow_configs
        self.template_service = PromptTemplateService()
        
        # 统计信息
        self.stats = {
            'total_workflows': 0,
            'updated_workflows': 0,
            'total_nodes': 0,
            'updated_nodes': 0,
            'skipped_nodes': 0,
            'error_nodes': 0,
            'missing_templates': {}
        }
    
    def get_default_template(self, agent_type: str) -> Optional[PromptTemplate]:
        """获取指定智能体类型的默认模板"""
        try:
            return self.template_service.get_default_template(agent_type)
        except Exception as e:
            logger.error(f"获取智能体类型 {agent_type} 的默认模板失败: {e}")
            return None
    
    def update_node_template(
        self,
        node: Dict[str, Any],
        default_template: PromptTemplate
    ) -> bool:
        """
        更新节点的模板ID和相关信息
        
        Returns:
            bool: 是否实际更新了节点
        """
        updated = False
        config = node.get('config', {})
        
        if not isinstance(config, dict):
            return False
        
        # 获取当前模板ID
        current_template_id = config.get('template_id')
        new_template_id = str(default_template.id)
        
        # 检查是否需要更新 template_id
        if current_template_id != new_template_id:
            config['template_id'] = new_template_id
            updated = True
            
            if self.verbose:
                logger.info(
                    f"  节点 {node.get('id', 'unknown')} ({node.get('name', 'unknown')}): "
                    f"template_id {current_template_id} -> {new_template_id}"
                )
        
        # 检查并更新模板相关信息（确保一致性）
        # 即使 template_id 已经正确，也要确保其他字段是最新的
        current_display_name = config.get('template_display_name')
        new_display_name = default_template.template_display_name
        current_template_name = config.get('template_name')
        new_template_name = default_template.template_name
        
        if current_display_name != new_display_name:
            config['template_display_name'] = new_display_name
            updated = True
            if self.verbose:
                logger.info(
                    f"  节点 {node.get('id', 'unknown')} ({node.get('name', 'unknown')}): "
                    f"template_display_name '{current_display_name}' -> '{new_display_name}'"
                )
        
        if current_template_name != new_template_name:
            config['template_name'] = new_template_name
            updated = True
            if self.verbose:
                logger.info(
                    f"  节点 {node.get('id', 'unknown')} ({node.get('name', 'unknown')}): "
                    f"template_name '{current_template_name}' -> '{new_template_name}'"
                )
        
        # 如果有版本信息，也更新
        if hasattr(default_template, 'version') and default_template.version:
            current_version = config.get('template_version')
            new_version = default_template.version
            if current_version != new_version:
                config['template_version'] = new_version
                updated = True
                if self.verbose:
                    logger.info(
                        f"  节点 {node.get('id', 'unknown')} ({node.get('name', 'unknown')}): "
                        f"template_version {current_version} -> {new_version}"
                    )
        
        # 确保 node['config'] 被更新
        node['config'] = config
        
        return updated
    
    def process_workflow(self, workflow: Dict[str, Any]) -> bool:
        """
        处理单个工作流，更新其中所有节点的模板ID
        
        Returns:
            bool: 是否更新了工作流
        """
        workflow_id = str(workflow.get('_id', 'unknown'))
        workflow_name = workflow.get('name', 'unknown')
        nodes = workflow.get('nodes', [])
        
        if not nodes:
            if self.verbose:
                logger.debug(f"工作流 {workflow_name} ({workflow_id}) 没有节点，跳过")
            return False
        
        workflow_updated = False
        nodes_updated = 0
        
        for node in nodes:
            self.stats['total_nodes'] += 1
            
            # 获取节点配置
            config = node.get('config', {})
            if not isinstance(config, dict):
                self.stats['skipped_nodes'] += 1
                if self.verbose:
                    logger.warning(
                        f"  节点 {node.get('id', 'unknown')} 的 config 不是字典类型，跳过"
                    )
                continue
            
            # 获取 agent_type
            agent_type = config.get('agent_type')
            if not agent_type:
                self.stats['skipped_nodes'] += 1
                if self.verbose:
                    logger.warning(
                        f"  节点 {node.get('id', 'unknown')} ({node.get('name', 'unknown')}) "
                        f"没有 agent_type，跳过"
                    )
                continue
            
            # 获取默认模板
            default_template = self.get_default_template(agent_type)
            if not default_template:
                self.stats['error_nodes'] += 1
                if agent_type not in self.stats['missing_templates']:
                    self.stats['missing_templates'][agent_type] = 0
                self.stats['missing_templates'][agent_type] += 1
                
                logger.warning(
                    f"  节点 {node.get('id', 'unknown')} ({node.get('name', 'unknown')}) "
                    f"的智能体类型 {agent_type} 没有找到默认模板，跳过"
                )
                continue
            
            # 更新节点模板
            if self.update_node_template(node, default_template):
                nodes_updated += 1
                workflow_updated = True
        
        if workflow_updated:
            self.stats['updated_nodes'] += nodes_updated
            
            if not self.dry_run:
                # 更新工作流的 metadata.updated_at 时间戳
                metadata = workflow.get('metadata', {})
                if not isinstance(metadata, dict):
                    metadata = {}
                metadata['updated_at'] = datetime.now().isoformat()
                
                # 保存到数据库
                try:
                    self.workflow_collection.update_one(
                        {'_id': workflow['_id']},
                        {'$set': {'nodes': nodes, 'metadata': metadata}}
                    )
                    logger.info(
                        f"✅ 工作流 {workflow_name} ({workflow_id}): "
                        f"更新了 {nodes_updated} 个节点"
                    )
                except Exception as e:
                    logger.error(
                        f"❌ 保存工作流 {workflow_name} ({workflow_id}) 失败: {e}"
                    )
                    return False
            else:
                logger.info(
                    f"[DRY-RUN] 工作流 {workflow_name} ({workflow_id}): "
                    f"将更新 {nodes_updated} 个节点"
                )
        
        return workflow_updated
    
    def run(self):
        """执行迁移"""
        logger.info("=" * 60)
        logger.info("开始节点模板ID对齐迁移")
        logger.info("=" * 60)
        
        if self.dry_run:
            logger.info("⚠️  运行在 DRY-RUN 模式，不会实际修改数据库")
        else:
            logger.info("⚠️  将实际修改数据库，请确保已备份")
        
        logger.info("")
        
        # 获取所有工作流
        try:
            workflows = list(self.workflow_collection.find({}))
            self.stats['total_workflows'] = len(workflows)
            
            logger.info(f"找到 {len(workflows)} 个工作流配置")
            logger.info("")
            
            if not workflows:
                logger.info("没有找到工作流配置，退出")
                return
            
        except Exception as e:
            logger.error(f"❌ 获取工作流列表失败: {e}")
            return
        
        # 处理每个工作流
        for workflow in workflows:
            workflow_id = str(workflow.get('_id', 'unknown'))
            workflow_name = workflow.get('name', 'unknown')
            
            if self.verbose:
                logger.info(f"处理工作流: {workflow_name} ({workflow_id})")
            
            try:
                if self.process_workflow(workflow):
                    self.stats['updated_workflows'] += 1
            except Exception as e:
                logger.error(
                    f"❌ 处理工作流 {workflow_name} ({workflow_id}) 时出错: {e}"
                )
        
        # 打印统计信息
        self.print_stats()
    
    def print_stats(self):
        """打印迁移统计信息"""
        logger.info("")
        logger.info("=" * 60)
        logger.info("迁移统计信息")
        logger.info("=" * 60)
        logger.info(f"总工作流数: {self.stats['total_workflows']}")
        logger.info(f"更新工作流数: {self.stats['updated_workflows']}")
        logger.info(f"总节点数: {self.stats['total_nodes']}")
        logger.info(f"更新节点数: {self.stats['updated_nodes']}")
        logger.info(f"跳过节点数: {self.stats['skipped_nodes']}")
        logger.info(f"错误节点数: {self.stats['error_nodes']}")
        
        if self.stats['missing_templates']:
            logger.info("")
            logger.warning("以下智能体类型没有找到默认模板:")
            for agent_type, count in self.stats['missing_templates'].items():
                logger.warning(f"  - {agent_type}: {count} 个节点")
        
        logger.info("")
        if self.dry_run:
            logger.info("✅ DRY-RUN 模式完成，未实际修改数据库")
        else:
            logger.info("✅ 迁移完成")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='将工作流节点的 template_id 对齐到默认模板'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='仅显示将要更新的内容，不实际修改数据库'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='显示详细的更新信息'
    )
    
    args = parser.parse_args()
    
    migrator = NodeTemplateMigrator(
        dry_run=args.dry_run,
        verbose=args.verbose
    )
    
    try:
        migrator.run()
    except KeyboardInterrupt:
        logger.info("\n用户中断操作")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ 迁移过程中发生错误: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
