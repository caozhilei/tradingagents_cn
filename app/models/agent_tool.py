"""
智能体工具管理数据模型
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from bson import ObjectId
from app.models.user import PyObjectId


class AgentTool(BaseModel):
    """智能体工具模型"""
    
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    tool_name: str = Field(..., description="工具名称（函数名）")
    tool_display_name: str = Field(..., description="工具显示名称")
    description: str = Field(..., description="工具描述")
    agent_type: str = Field(..., description="适用的智能体类型（如：fundamentals_analyst, market_analyst等）")
    tool_category: str = Field(default="data", description="工具类别（data, analysis, news, sentiment等）")
    tool_module: str = Field(..., description="工具所在模块（如：tradingagents.agents.utils.agent_utils.Toolkit）")
    tool_method: str = Field(..., description="工具方法名（如：get_stock_fundamentals_unified）")
    parameters: Optional[Dict[str, Any]] = Field(default=None, description="工具参数定义")
    is_system: bool = Field(default=True, description="是否为系统工具")
    is_active: bool = Field(default=True, description="是否启用")
    is_default: bool = Field(default=False, description="是否为默认工具")
    priority: int = Field(default=0, description="优先级（数字越大优先级越高）")
    tags: List[str] = Field(default_factory=list, description="标签")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    created_by: Optional[PyObjectId] = Field(default=None, description="创建者ID")
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class AgentToolCreate(BaseModel):
    """创建工具请求模型"""
    tool_name: str
    tool_display_name: str
    description: str
    agent_type: str
    tool_category: str = "data"
    tool_module: str
    tool_method: str
    parameters: Optional[Dict[str, Any]] = None
    is_default: bool = False
    priority: int = 0
    tags: List[str] = []


class AgentToolUpdate(BaseModel):
    """更新工具请求模型"""
    tool_display_name: Optional[str] = None
    description: Optional[str] = None
    agent_type: Optional[str] = None
    tool_category: Optional[str] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None
    priority: Optional[int] = None
    tags: Optional[List[str]] = None


class AgentToolConfig(BaseModel):
    """智能体工具配置（用户配置）"""
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId = Field(..., description="用户ID")
    agent_type: str = Field(..., description="智能体类型")
    tool_ids: List[PyObjectId] = Field(default_factory=list, description="配置的工具ID列表")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

