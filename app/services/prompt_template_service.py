"""
提示词模板管理服务
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from bson import ObjectId
from pymongo import MongoClient
from app.core.config import settings
from app.core.database import get_mongo_db_sync
from app.models.prompt_template import (
    PromptTemplate,
    PromptTemplateVersion,
    AgentTemplateConfig,
    PromptTemplateCreate,
    PromptTemplateUpdate
)

logger = logging.getLogger(__name__)


class PromptTemplateService:
    """提示词模板管理服务"""
    
    def __init__(self):
        # 使用统一的数据库连接方式
        try:
            # 优先使用统一的数据库连接
            self.db = get_mongo_db_sync()
            self.templates_collection = self.db.prompt_templates
            self.versions_collection = self.db.prompt_template_versions
            self.configs_collection = self.db.agent_template_configs
        except Exception as e:
            # 降级方案：直接创建连接
            logger.warning(f"使用统一数据库连接失败，使用直接连接: {e}")
            self.client = MongoClient(
                settings.MONGO_URI,
                maxPoolSize=settings.MONGO_MAX_CONNECTIONS,
                minPoolSize=settings.MONGO_MIN_CONNECTIONS,
                serverSelectionTimeoutMS=5000
            )
            self.db = self.client[settings.MONGO_DB]
            self.templates_collection = self.db.prompt_templates
            self.versions_collection = self.db.prompt_template_versions
            self.configs_collection = self.db.agent_template_configs
        
        # 创建索引
        self._create_indexes()
    
    def _create_indexes(self):
        """创建数据库索引"""
        try:
            self.templates_collection.create_index([("agent_type", 1), ("template_name", 1)])
            self.templates_collection.create_index([("agent_type", 1), ("is_default", 1)])
            self.templates_collection.create_index([("is_system", 1)])
            self.templates_collection.create_index([("created_by", 1)])
            self.templates_collection.create_index([("is_active", 1)])
            
            self.versions_collection.create_index([("template_id", 1), ("version", 1)])
            
            self.configs_collection.create_index([("user_id", 1), ("agent_type", 1)], unique=True)
            self.configs_collection.create_index([("template_id", 1)])
        except Exception as e:
            logger.warning(f"创建索引失败: {e}")
    
    # ========== 模板管理 ==========
    
    def create_template(
        self, 
        template_data: PromptTemplateCreate,
        user_id: Optional[ObjectId] = None
    ) -> PromptTemplate:
        """创建新模板"""
        try:
            logger.info(f"📝 [create_template] 开始创建模板: {template_data.agent_type}/{template_data.template_name}")
            
            # 检查模板名称是否已存在
            existing = self.templates_collection.find_one({
                "agent_type": template_data.agent_type,
                "template_name": template_data.template_name
            })
            if existing:
                raise ValueError(f"模板名称 '{template_data.template_name}' 已存在")
            
            # 如果设置为默认模板，取消其他默认模板
            if template_data.is_default:
                self.templates_collection.update_many(
                    {"agent_type": template_data.agent_type, "is_default": True},
                    {"$set": {"is_default": False}}
                )
            
            logger.debug(f"📋 [create_template] 准备创建 PromptTemplate 对象")
            logger.debug(f"📋 [create_template] tool_configs: {template_data.tool_configs}")
            
            # 创建模板对象
            template = PromptTemplate(
                agent_type=template_data.agent_type,
                agent_name=template_data.agent_name,
                template_name=template_data.template_name,
                template_display_name=template_data.template_display_name,
                description=template_data.description,
                content=template_data.content,
                tags=template_data.tags or [],
                category=template_data.category,
                is_system=False,
                is_default=template_data.is_default or False,
                tool_configs=template_data.tool_configs,
                created_by=user_id,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            logger.debug(f"📋 [create_template] PromptTemplate 对象创建成功")
            logger.debug(f"📋 [create_template] 准备序列化为字典")
            
            # 序列化为字典
            template_dict = template.model_dump(by_alias=True, exclude={"id"})
            logger.debug(f"📋 [create_template] 序列化成功，准备插入数据库")
            
            # 插入数据库
            result = self.templates_collection.insert_one(template_dict)
            template.id = result.inserted_id
            
            logger.info(f"✅ 创建模板成功: {template_data.agent_type}/{template_data.template_name}, ID: {template.id}")
            return template
        except ValueError:
            raise
        except Exception as e:
            import traceback
            logger.error(f"❌ [create_template] 创建模板失败: {e}")
            logger.error(f"📋 [create_template] 异常堆栈: {traceback.format_exc()}")
            raise
    
    def get_template(
        self,
        template_id: ObjectId
    ) -> Optional[PromptTemplate]:
        """获取模板"""
        doc = self.templates_collection.find_one({"_id": template_id})
        if doc:
            return PromptTemplate(**doc)
        return None
    
    def get_template_by_name(
        self,
        agent_type: str,
        template_name: str
    ) -> Optional[PromptTemplate]:
        """根据名称获取模板"""
        doc = self.templates_collection.find_one({
            "agent_type": agent_type,
            "template_name": template_name
        })
        if doc:
            return PromptTemplate(**doc)
        return None
    
    def get_default_template(
        self,
        agent_type: str
    ) -> Optional[PromptTemplate]:
        """获取默认模板"""
        doc = self.templates_collection.find_one({
            "agent_type": agent_type,
            "is_default": True,
            "is_active": True
        })
        if doc:
            return PromptTemplate(**doc)
        
        # 如果没有默认模板，返回第一个系统模板
        doc = self.templates_collection.find_one({
            "agent_type": agent_type,
            "is_system": True,
            "is_active": True
        }, sort=[("created_at", 1)])
        if doc:
            return PromptTemplate(**doc)
        
        return None
    
    def list_templates(
        self,
        agent_type: Optional[str] = None,
        is_system: Optional[bool] = None,
        is_active: Optional[bool] = None,
        user_id: Optional[ObjectId] = None
    ) -> List[PromptTemplate]:
        """列出模板"""
        query = {}
        if agent_type:
            query["agent_type"] = agent_type
        if is_system is not None:
            query["is_system"] = is_system
        if is_active is not None:
            query["is_active"] = is_active
        if user_id:
            query["created_by"] = user_id
        
        docs = self.templates_collection.find(query).sort("created_at", -1)
        return [PromptTemplate(**doc) for doc in docs]
    
    def update_template(
        self,
        template_id: ObjectId,
        update_data: PromptTemplateUpdate,
        user_id: Optional[ObjectId] = None
    ) -> Optional[PromptTemplate]:
        """更新模板"""
        template = self.get_template(template_id)
        if not template:
            return None
        
        # 保存当前版本到历史
        self._save_version(template, user_id, update_data.change_description)
        
        # 更新模板
        update_dict = {"updated_at": datetime.now()}
        if update_data.template_display_name is not None:
            update_dict["template_display_name"] = update_data.template_display_name
        if update_data.description is not None:
            update_dict["description"] = update_data.description
        if update_data.content is not None:
            update_dict["content"] = update_data.content.model_dump()
        if update_data.tags is not None:
            update_dict["tags"] = update_data.tags
        if update_data.category is not None:
            update_dict["category"] = update_data.category
        if update_data.is_default is not None:
            update_dict["is_default"] = update_data.is_default
            # 如果设置为默认，取消其他默认
            if update_data.is_default:
                self.templates_collection.update_many(
                    {"agent_type": template.agent_type, "is_default": True, "_id": {"$ne": template_id}},
                    {"$set": {"is_default": False}}
                )
        if update_data.is_active is not None:
            update_dict["is_active"] = update_data.is_active
        if update_data.tool_configs is not None:
            update_dict["tool_configs"] = update_data.tool_configs
        if user_id:
            update_dict["updated_by"] = user_id
        
        # 版本号递增
        update_dict["version"] = template.version + 1
        
        self.templates_collection.update_one(
            {"_id": template_id},
            {"$set": update_dict}
        )
        
        logger.info(f"更新模板成功: {template_id}")
        return self.get_template(template_id)
    
    def delete_template(
        self,
        template_id: ObjectId
    ) -> bool:
        """删除模板（软删除）"""
        result = self.templates_collection.update_one(
            {"_id": template_id},
            {"$set": {"is_active": False, "updated_at": datetime.now()}}
        )
        return result.modified_count > 0
    
    # ========== 版本管理 ==========
    
    def _save_version(
        self,
        template: PromptTemplate,
        user_id: Optional[ObjectId],
        change_description: Optional[str] = None
    ):
        """保存模板版本"""
        version = PromptTemplateVersion(
            template_id=template.id,
            version=template.version,
            content=template.content,
            change_description=change_description,
            changed_by=user_id,
            created_at=datetime.now()
        )
        self.versions_collection.insert_one(version.model_dump(by_alias=True, exclude={"id"}))
    
    def get_template_versions(
        self,
        template_id: ObjectId
    ) -> List[PromptTemplateVersion]:
        """获取模板版本历史"""
        docs = self.versions_collection.find(
            {"template_id": template_id}
        ).sort("version", -1)
        return [PromptTemplateVersion(**doc) for doc in docs]
    
    def restore_version(
        self,
        template_id: ObjectId,
        version: int,
        user_id: Optional[ObjectId] = None
    ) -> Optional[PromptTemplate]:
        """恢复指定版本"""
        version_doc = self.versions_collection.find_one({
            "template_id": template_id,
            "version": version
        })
        if not version_doc:
            return None
        
        template = self.get_template(template_id)
        if not template:
            return None
        
        # 保存当前版本
        self._save_version(template, user_id, f"恢复版本 {version}")
        
        # 恢复版本内容
        update_dict = {
            "content": version_doc["content"],
            "version": template.version + 1,
            "updated_at": datetime.now()
        }
        if user_id:
            update_dict["updated_by"] = user_id
        
        self.templates_collection.update_one(
            {"_id": template_id},
            {"$set": update_dict}
        )
        
        return self.get_template(template_id)
    
    # ========== 用户配置 ==========
    
    def set_user_template_config(
        self,
        user_id: ObjectId,
        agent_type: str,
        template_id: ObjectId,
        template_name: str
    ) -> AgentTemplateConfig:
        """设置用户模板配置"""
        config = AgentTemplateConfig(
            user_id=user_id,
            agent_type=agent_type,
            template_id=template_id,
            template_name=template_name,
            updated_at=datetime.now()
        )
        
        # 使用 upsert 更新或插入
        self.configs_collection.update_one(
            {"user_id": user_id, "agent_type": agent_type},
            {"$set": config.model_dump(by_alias=True, exclude={"id", "created_at"})},
            upsert=True
        )
        
        # 更新模板使用统计
        self.templates_collection.update_one(
            {"_id": template_id},
            {
                "$inc": {"usage_count": 1},
                "$set": {"last_used_at": datetime.now()}
            }
        )
        
        return config
    
    def get_user_template_config(
        self,
        user_id: ObjectId,
        agent_type: str
    ) -> Optional[AgentTemplateConfig]:
        """获取用户模板配置"""
        doc = self.configs_collection.find_one({
            "user_id": user_id,
            "agent_type": agent_type
        })
        if doc:
            return AgentTemplateConfig(**doc)
        return None
    
    def get_user_template(
        self,
        user_id: ObjectId,
        agent_type: str
    ) -> Optional[PromptTemplate]:
        """获取用户配置的模板"""
        config = self.get_user_template_config(user_id, agent_type)
        if config:
            return self.get_template(config.template_id)
        
        # 如果没有用户配置，返回默认模板
        return self.get_default_template(agent_type)
    
    # ========== 模板渲染 ==========
    
    def render_template(
        self,
        template: PromptTemplate,
        variables: Dict[str, Any]
    ) -> Dict[str, str]:
        """渲染模板（替换变量）"""
        rendered = {}
        
        # 渲染系统提示词
        rendered["system_prompt"] = template.content.system_prompt.format(**variables)
        
        # 渲染其他字段
        if template.content.tool_guidance:
            rendered["tool_guidance"] = template.content.tool_guidance.format(**variables)
        if template.content.analysis_requirements:
            rendered["analysis_requirements"] = template.content.analysis_requirements.format(**variables)
        if template.content.output_format:
            rendered["output_format"] = template.content.output_format.format(**variables)
        
        return rendered

