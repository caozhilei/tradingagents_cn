"""
智能体工具管理API路由
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from bson import ObjectId
from app.models.agent_tool import (
    AgentTool,
    AgentToolCreate,
    AgentToolUpdate,
    AgentToolConfig
)
from app.services.agent_tool_service import AgentToolService
from app.models.user import User, PyObjectId
from app.routers.auth_db import get_current_user

router = APIRouter(prefix="/api/agent-tools", tags=["智能体工具"])

# 初始化服务
tool_service = AgentToolService()


@router.post("", response_model=AgentTool, status_code=status.HTTP_201_CREATED)
async def create_tool(
    tool_data: AgentToolCreate,
    current_user: dict = Depends(get_current_user)
):
    """创建新工具"""
    try:
        user_id = ObjectId(current_user["id"]) if isinstance(current_user.get("id"), str) else current_user.get("id")
        tool = tool_service.create_tool(tool_data, user_id=user_id)
        return tool
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建工具失败: {str(e)}")


@router.get("", response_model=List[AgentTool])
async def list_tools(
    agent_type: Optional[str] = None,
    tool_category: Optional[str] = None,
    is_active: Optional[bool] = True
):
    """列出工具"""
    tools = tool_service.list_tools(
        agent_type=agent_type,
        tool_category=tool_category,
        is_active=is_active
    )
    return tools


@router.get("/{tool_id}", response_model=AgentTool)
async def get_tool(tool_id: str):
    """获取工具详情"""
    try:
        obj_id = ObjectId(tool_id)
    except Exception:
        raise HTTPException(status_code=400, detail="无效的工具ID")
    
    tool = tool_service.get_tool(obj_id)
    if not tool:
        raise HTTPException(status_code=404, detail="工具不存在")
    return tool


@router.put("/{tool_id}", response_model=AgentTool)
async def update_tool(
    tool_id: str,
    update_data: AgentToolUpdate,
    current_user: User = Depends(get_current_user)
):
    """更新工具"""
    try:
        obj_id = ObjectId(tool_id)
    except Exception:
        raise HTTPException(status_code=400, detail="无效的工具ID")
    
    tool = tool_service.update_tool(obj_id, update_data, user_id=current_user.id)
    if not tool:
        raise HTTPException(status_code=404, detail="工具不存在")
    return tool


@router.delete("/{tool_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tool(tool_id: str):
    """删除工具（软删除）"""
    try:
        obj_id = ObjectId(tool_id)
    except Exception:
        raise HTTPException(status_code=400, detail="无效的工具ID")
    
    success = tool_service.delete_tool(obj_id)
    if not success:
        raise HTTPException(status_code=404, detail="工具不存在")


@router.get("/agent/{agent_type}/default", response_model=List[AgentTool])
async def get_default_tools(agent_type: str):
    """获取默认工具列表"""
    tools = tool_service.get_default_tools(agent_type)
    return tools


@router.post("/register", summary="注册Toolkit中的所有工具")
async def register_tools():
    """注册Toolkit中的所有工具到数据库"""
    count = tool_service.register_toolkit_tools()
    return {"message": f"成功注册 {count} 个工具", "count": count}


# ========== 用户配置 ==========

@router.post("/user-config", response_model=AgentToolConfig)
async def set_user_tool_config(
    agent_type: str,
    tool_ids: List[str],
    current_user: dict = Depends(get_current_user)
):
    """设置用户工具配置"""
    try:
        tool_object_ids = [ObjectId(tid) for tid in tool_ids]
        user_id = ObjectId(current_user["id"]) if isinstance(current_user.get("id"), str) else current_user.get("id")
    except Exception:
        raise HTTPException(status_code=400, detail="无效的工具ID或用户ID")
    
    config = tool_service.set_user_tool_config(
        user_id,
        agent_type,
        tool_object_ids
    )
    return config


@router.get("/user-config/{agent_type}", response_model=Optional[AgentToolConfig])
async def get_user_tool_config(
    agent_type: str,
    current_user: dict = Depends(get_current_user)
):
    """获取用户工具配置"""
    user_id = ObjectId(current_user["id"]) if isinstance(current_user.get("id"), str) else current_user.get("id")
    config = tool_service.get_user_tool_config(user_id, agent_type)
    return config


@router.get("/agent/{agent_type}/available", response_model=List[AgentTool])
async def get_available_tools(
    agent_type: str,
    current_user: Optional[dict] = Depends(get_current_user)
):
    """获取智能体可用的工具列表（考虑用户配置）"""
    user_id = None
    if current_user and current_user.get("id"):
        user_id = ObjectId(current_user["id"]) if isinstance(current_user.get("id"), str) else current_user.get("id")
    tools = tool_service.get_tools_for_agent(user_id, agent_type)
    return tools

