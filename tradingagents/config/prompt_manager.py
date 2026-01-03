"""
提示词模板管理器 - 用于在智能体中加载和使用模板
"""

import logging
from typing import Dict, Any, Optional
from app.services.prompt_template_service import PromptTemplateService
from app.models.prompt_template import PromptTemplate
from bson import ObjectId

logger = logging.getLogger(__name__)


class PromptTemplateManager:
    """提示词模板管理器 - 用于运行时加载模板"""
    
    def __init__(self):
        self.service = PromptTemplateService()
        self._cache: Dict[str, PromptTemplate] = {}
    
    def get_template(
        self,
        agent_type: str,
        user_id: Optional[ObjectId] = None,
        template_name: Optional[str] = None
    ) -> Optional[PromptTemplate]:
        """
        获取模板
        
        Args:
            agent_type: 智能体类型
            user_id: 用户ID（可选，如果提供则优先使用用户配置）
            template_name: 模板名称（可选，如果提供则使用指定模板）
        
        Returns:
            提示词模板对象
        """
        cache_key = f"{agent_type}:{user_id}:{template_name}"
        
        # 检查缓存
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        template = None
        
        # 优先级：用户指定模板 > 用户配置模板 > 默认模板
        if template_name:
            template = self.service.get_template_by_name(agent_type, template_name)
        elif user_id:
            template = self.service.get_user_template(user_id, agent_type)
        
        # 如果没有找到，使用默认模板
        if not template:
            template = self.service.get_default_template(agent_type)
        
        if template:
            self._cache[cache_key] = template
        
        return template
    
    def render_template(
        self,
        template: PromptTemplate,
        variables: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        渲染模板（替换变量）
        
        Args:
            template: 模板对象
            variables: 变量字典
        
        Returns:
            渲染后的内容字典
        """
        return self.service.render_template(template, variables)
    
    def clear_cache(self, agent_type: Optional[str] = None):
        """清除缓存"""
        if agent_type:
            # 清除特定智能体的缓存
            keys_to_remove = [k for k in self._cache.keys() if k.startswith(f"{agent_type}:")]
            for key in keys_to_remove:
                del self._cache[key]
        else:
            # 清除所有缓存
            self._cache.clear()
    
    def get_system_prompt(
        self,
        agent_type: str,
        variables: Dict[str, Any],
        user_id: Optional[ObjectId] = None,
        template_name: Optional[str] = None
    ) -> str:
        """
        获取渲染后的系统提示词
        
        Args:
            agent_type: 智能体类型
            variables: 变量字典
            user_id: 用户ID（可选）
            template_name: 模板名称（可选）
        
        Returns:
            渲染后的系统提示词
        """
        template = self.get_template(agent_type, user_id, template_name)
        if not template:
            logger.warning(f"未找到模板: {agent_type}, 使用默认提示词")
            return self._get_default_prompt(agent_type, variables)
        
        rendered = self.render_template(template, variables)
        return rendered.get("system_prompt", "")
    
    def _get_default_prompt(self, agent_type: str, variables: Dict[str, Any]) -> str:
        """获取默认提示词（当模板不存在时使用）"""
        # 这里可以返回硬编码的默认提示词
        # 或者从代码中提取原有的提示词
        return f"你是一位专业的{agent_type}分析师。"


# 全局单例
_prompt_manager: Optional[PromptTemplateManager] = None


def get_prompt_manager() -> PromptTemplateManager:
    """获取全局提示词管理器实例"""
    global _prompt_manager
    if _prompt_manager is None:
        _prompt_manager = PromptTemplateManager()
    return _prompt_manager

