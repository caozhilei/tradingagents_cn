"""
工具配置数据模型
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict
from bson import ObjectId
from .user import PyObjectId


class ToolParameter(BaseModel):
    """工具参数定义"""
    name: str = Field(..., description="参数名称")
    type: str = Field(..., description="参数类型")
    description: str = Field(..., description="参数描述")
    required: bool = Field(default=True, description="是否必需")
    default: Optional[Any] = Field(None, description="默认值")


class ToolConfig(BaseModel):
    """工具配置模型"""
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    tool_name: str = Field(..., description="工具函数名，如 'get_stock_market_data_unified'")
    tool_display_name: str = Field(..., description="工具显示名称")
    description: str = Field(..., description="工具描述")
    category: str = Field(..., description="工具分类：market_data, fundamentals, news, sentiment, other")
    tool_type: str = Field(..., description="工具类型：unified, online, offline")
    supported_markets: List[str] = Field(default_factory=list, description="支持的市场：A股, 港股, 美股")
    parameters: List[ToolParameter] = Field(default_factory=list, description="工具参数定义")
    default_config: Dict[str, Any] = Field(default_factory=dict, description="默认配置（超时、重试等）")
    enabled: bool = Field(default=True, description="是否启用")
    priority: int = Field(default=100, description="优先级（数字越小优先级越高）")
    is_system: bool = Field(default=True, description="是否为系统工具")
    
    # 时间戳
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    # 统计信息
    usage_count: int = Field(default=0, description="使用次数")
    last_used_at: Optional[datetime] = Field(None, description="最后使用时间")
    
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_schema_extra={
            "example": {
                "tool_name": "get_stock_market_data_unified",
                "tool_display_name": "统一市场数据工具",
                "description": "统一的股票市场数据工具，自动识别股票类型",
                "category": "market_data",
                "tool_type": "unified",
                "supported_markets": ["A股", "港股", "美股"],
                "parameters": [
                    {
                        "name": "ticker",
                        "type": "str",
                        "description": "股票代码",
                        "required": True
                    }
                ],
                "default_config": {
                    "timeout": 30,
                    "retry_times": 3
                },
                "enabled": True,
                "priority": 1
            }
        }
    )


class AgentToolConfig(BaseModel):
    """智能体工具配置模型"""
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    agent_type: str = Field(..., description="智能体类型")
    tool_configs: List[str] = Field(default_factory=list, description="工具ID列表")
    default_tools: List[str] = Field(default_factory=list, description="默认工具ID列表")
    tool_priorities: Dict[str, int] = Field(default_factory=dict, description="工具优先级映射")
    
    # 时间戳
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_schema_extra={
            "example": {
                "agent_type": "market_analyst",
                "tool_configs": ["tool_id_1", "tool_id_2"],
                "default_tools": ["tool_id_1"],
                "tool_priorities": {
                    "tool_id_1": 1,
                    "tool_id_2": 2
                }
            }
        }
    )


# API请求/响应模型
class ToolConfigCreate(BaseModel):
    """创建工具配置请求"""
    tool_name: str
    tool_display_name: str
    description: str
    category: str
    tool_type: str
    supported_markets: List[str] = []
    parameters: List[Dict[str, Any]] = []
    default_config: Dict[str, Any] = {}
    enabled: bool = True
    priority: int = 100


class ToolConfigUpdate(BaseModel):
    """更新工具配置请求"""
    tool_display_name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    tool_type: Optional[str] = None
    supported_markets: Optional[List[str]] = None
    parameters: Optional[List[Dict[str, Any]]] = None
    default_config: Optional[Dict[str, Any]] = None
    enabled: Optional[bool] = None
    priority: Optional[int] = None


class AgentToolConfigCreate(BaseModel):
    """创建智能体工具配置请求"""
    agent_type: str
    tool_configs: List[str] = []
    default_tools: List[str] = []
    tool_priorities: Dict[str, int] = {}


class AgentToolConfigUpdate(BaseModel):
    """更新智能体工具配置请求"""
    tool_configs: Optional[List[str]] = None
    default_tools: Optional[List[str]] = None
    tool_priorities: Optional[Dict[str, int]] = None
