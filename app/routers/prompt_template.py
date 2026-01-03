"""
提示词模板管理API路由
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from bson import ObjectId
from app.models.prompt_template import (
    PromptTemplate,
    PromptTemplateCreate,
    PromptTemplateUpdate,
    AgentTemplateConfig
)
from app.services.prompt_template_service import PromptTemplateService
from app.routers.auth_db import get_current_user

router = APIRouter(prefix="/api/prompt-templates", tags=["提示词模板"])

# 初始化服务
template_service = PromptTemplateService()


@router.get("/agents", summary="获取所有智能体类型")
async def get_agent_types():
    """获取所有智能体类型列表"""
    return {
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


@router.post("", response_model=PromptTemplate, status_code=status.HTTP_201_CREATED)
async def create_template(
    template_data: PromptTemplateCreate,
    current_user: dict = Depends(get_current_user)
):
    """创建新模板"""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"📝 创建模板请求: agent_type={template_data.agent_type}, template_name={template_data.template_name}")
        logger.debug(f"📋 模板数据: {template_data.model_dump()}")
        
        # 从字典中获取 user_id（current_user 是字典类型）
        user_id = current_user.get("id")
        if isinstance(user_id, str):
            from bson import ObjectId
            try:
                user_id = ObjectId(user_id)
            except Exception:
                logger.warning(f"⚠️ 无法转换 user_id 为 ObjectId: {user_id}")
                user_id = None
        elif user_id is None:
            logger.warning(f"⚠️ user_id 为空，使用 None")
            user_id = None
        
        template = template_service.create_template(
            template_data,
            user_id=user_id
        )
        logger.info(f"✅ 模板创建成功: {template.id}")
        return template
    except ValueError as e:
        logger.error(f"❌ 模板创建验证失败: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import traceback
        logger.error(f"❌ 创建模板失败: {e}")
        logger.error(f"📋 异常堆栈: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"创建模板失败: {str(e)}")


@router.get("", response_model=List[PromptTemplate])
async def list_templates(
    agent_type: Optional[str] = None,
    is_system: Optional[bool] = None,
    is_active: Optional[bool] = True
):
    """列出模板"""
    templates = template_service.list_templates(
        agent_type=agent_type,
        is_system=is_system,
        is_active=is_active
    )
    return templates


@router.get("/{template_id}", response_model=PromptTemplate)
async def get_template(template_id: str):
    """获取模板详情"""
    try:
        # 验证并转换ObjectId
        if not ObjectId.is_valid(template_id):
            raise HTTPException(
                status_code=400, 
                detail=f"无效的模板ID格式: {template_id}"
            )
        obj_id = ObjectId(template_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=400, 
            detail=f"无效的模板ID: {template_id}, 错误: {str(e)}"
        )
    
    template = template_service.get_template(obj_id)
    if not template:
        raise HTTPException(
            status_code=404, 
            detail=f"模板不存在: {template_id}"
        )
    return template


@router.put("/{template_id}", response_model=PromptTemplate)
async def update_template(
    template_id: str,
    update_data: PromptTemplateUpdate,
    current_user: dict = Depends(get_current_user)
):
    """更新模板"""
    try:
        obj_id = ObjectId(template_id)
    except Exception:
        raise HTTPException(status_code=400, detail="无效的模板ID")
    
    # 从字典中获取 user_id（current_user 是字典类型）
    user_id = current_user.get("id")
    if isinstance(user_id, str):
        try:
            user_id = ObjectId(user_id)
        except Exception:
            user_id = None
    
    template = template_service.update_template(
        obj_id,
        update_data,
        user_id=user_id
    )
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    return template


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(template_id: str):
    """删除模板（软删除）"""
    try:
        obj_id = ObjectId(template_id)
    except Exception:
        raise HTTPException(status_code=400, detail="无效的模板ID")
    
    success = template_service.delete_template(obj_id)
    if not success:
        raise HTTPException(status_code=404, detail="模板不存在")


@router.get("/{template_id}/versions", response_model=List[dict])
async def get_template_versions(template_id: str):
    """获取模板版本历史"""
    try:
        obj_id = ObjectId(template_id)
    except Exception:
        raise HTTPException(status_code=400, detail="无效的模板ID")
    
    versions = template_service.get_template_versions(obj_id)
    return [v.model_dump() for v in versions]


@router.post("/{template_id}/restore/{version}", response_model=PromptTemplate)
async def restore_version(
    template_id: str,
    version: int,
    current_user: dict = Depends(get_current_user)
):
    """恢复指定版本"""
    try:
        obj_id = ObjectId(template_id)
    except Exception:
        raise HTTPException(status_code=400, detail="无效的模板ID")
    
    # 从字典中获取 user_id
    user_id = current_user.get("id")
    if isinstance(user_id, str):
        try:
            user_id = ObjectId(user_id)
        except Exception:
            user_id = None
    
    template = template_service.restore_version(
        obj_id,
        version,
        user_id=user_id
    )
    if not template:
        raise HTTPException(status_code=404, detail="版本不存在")
    return template


@router.get("/agent/{agent_type}/default", response_model=PromptTemplate)
async def get_default_template(agent_type: str):
    """获取默认模板"""
    template = template_service.get_default_template(agent_type)
    if not template:
        raise HTTPException(status_code=404, detail="未找到默认模板")
    return template


# ========== 用户配置 ==========

@router.post("/user-config", response_model=AgentTemplateConfig)
async def set_user_template_config(
    agent_type: str,
    template_id: str,
    current_user: dict = Depends(get_current_user)
):
    """设置用户模板配置"""
    try:
        template_obj_id = ObjectId(template_id)
    except Exception:
        raise HTTPException(status_code=400, detail="无效的模板ID")
    
    # 验证模板存在
    template = template_service.get_template(template_obj_id)
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    # 从字典中获取 user_id
    user_id = current_user.get("id")
    if isinstance(user_id, str):
        try:
            user_id = ObjectId(user_id)
        except Exception:
            raise HTTPException(status_code=400, detail="无效的用户ID")
    
    config = template_service.set_user_template_config(
        user_id,
        agent_type,
        template_obj_id,
        template.template_name
    )
    return config


@router.get("/user-config/{agent_type}", response_model=Optional[PromptTemplate])
async def get_user_template(
    agent_type: str,
    current_user: dict = Depends(get_current_user)
):
    """获取用户配置的模板"""
    # 从字典中获取 user_id
    user_id = current_user.get("id")
    if isinstance(user_id, str):
        try:
            user_id = ObjectId(user_id)
        except Exception:
            raise HTTPException(status_code=400, detail="无效的用户ID")
    
    template = template_service.get_user_template(
        user_id,
        agent_type
    )
    return template


@router.get("/user-configs", response_model=List[AgentTemplateConfig])
async def get_user_template_configs(
    current_user: dict = Depends(get_current_user)
):
    """获取用户所有模板配置"""
    # 这里需要扩展服务方法
    # 暂时返回空列表
    return []

