"""
工具配置管理API路由
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from bson import ObjectId

from app.routers.auth_db import get_current_user
from app.services.tool_config_service import ToolConfigService
from app.models.tool_config import (
    ToolConfig,
    AgentToolConfig,
    ToolConfigCreate,
    ToolConfigUpdate,
    AgentToolConfigCreate,
    AgentToolConfigUpdate
)
from app.models.user import User

router = APIRouter(prefix="/api/tools", tags=["工具配置"])
logger = logging.getLogger("webapi")

# 初始化服务
tool_service = ToolConfigService()


# ========== 工具配置API ==========

@router.get("", response_model=List[ToolConfig], summary="获取所有工具列表")
async def get_all_tools(
    category: Optional[str] = Query(None, description="工具分类筛选"),
    tool_type: Optional[str] = Query(None, description="工具类型筛选"),
    enabled: Optional[bool] = Query(None, description="是否启用筛选"),
    current_user: User = Depends(get_current_user)
):
    """获取所有工具列表"""
    try:
        tools = tool_service.get_all_tools(
            category=category,
            tool_type=tool_type,
            enabled=enabled
        )
        return tools
    except Exception as e:
        logger.error(f"获取工具列表失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取工具列表失败: {str(e)}"
        )


@router.get("/{tool_id}", response_model=ToolConfig, summary="获取工具详情")
async def get_tool(
    tool_id: str,
    current_user: User = Depends(get_current_user)
):
    """获取工具详情"""
    try:
        tool = tool_service.get_tool_by_id(tool_id)
        if not tool:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="工具不存在"
            )
        return tool
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取工具详情失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取工具详情失败: {str(e)}"
        )


@router.post("", response_model=ToolConfig, summary="创建工具配置")
async def create_tool(
    tool_data: ToolConfigCreate,
    current_user: User = Depends(get_current_user)
):
    """创建工具配置"""
    try:
        tool = tool_service.create_tool_config(tool_data)
        return tool
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"创建工具配置失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建工具配置失败: {str(e)}"
        )


@router.put("/{tool_id}", response_model=ToolConfig, summary="更新工具配置")
async def update_tool(
    tool_id: str,
    updates: ToolConfigUpdate,
    current_user: User = Depends(get_current_user)
):
    """更新工具配置"""
    try:
        tool = tool_service.update_tool_config(tool_id, updates)
        if not tool:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="工具不存在"
            )
        return tool
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新工具配置失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新工具配置失败: {str(e)}"
        )


@router.delete("/{tool_id}", summary="删除工具配置")
async def delete_tool(
    tool_id: str,
    current_user: User = Depends(get_current_user)
):
    """删除工具配置"""
    try:
        success = tool_service.delete_tool_config(tool_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="工具不存在"
            )
        return {"message": "工具配置已删除"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除工具配置失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除工具配置失败: {str(e)}"
        )


# ========== 智能体工具配置API ==========

@router.get("/agent/{agent_type}", response_model=AgentToolConfig, summary="获取智能体工具配置")
async def get_agent_tool_config(
    agent_type: str,
    current_user: User = Depends(get_current_user)
):
    """获取智能体的工具配置"""
    try:
        config = tool_service.get_agent_tool_config(agent_type)
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"智能体 '{agent_type}' 的工具配置不存在"
            )
        return config
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取智能体工具配置失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取智能体工具配置失败: {str(e)}"
        )


@router.put("/agent/{agent_type}", response_model=AgentToolConfig, summary="更新智能体工具配置")
async def update_agent_tool_config(
    agent_type: str,
    updates: AgentToolConfigUpdate,
    current_user: User = Depends(get_current_user)
):
    """更新智能体的工具配置"""
    try:
        config = tool_service.update_agent_tool_config(agent_type, updates)
        if not config:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="更新智能体工具配置失败"
            )
        return config
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新智能体工具配置失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新智能体工具配置失败: {str(e)}"
        )


@router.post("/agent", response_model=AgentToolConfig, summary="创建智能体工具配置")
async def create_agent_tool_config(
    config_data: AgentToolConfigCreate,
    current_user: User = Depends(get_current_user)
):
    """创建智能体工具配置"""
    try:
        config = tool_service.create_agent_tool_config(config_data)
        return config
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"创建智能体工具配置失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建智能体工具配置失败: {str(e)}"
        )


# ========== 工具初始化API ==========

@router.post("/initialize", summary="初始化工具到数据库")
async def initialize_tools(
    current_user: User = Depends(get_current_user)
):
    """从Toolkit类初始化工具到数据库"""
    try:
        result = tool_service.initialize_tools_from_toolkit()
        return {
            "message": "工具初始化完成",
            "initialized": result["initialized"],
            "skipped": result["skipped"],
            "errors": result["errors"]
        }
    except Exception as e:
        logger.error(f"工具初始化失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"工具初始化失败: {str(e)}"
        )
