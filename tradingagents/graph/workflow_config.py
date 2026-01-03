# TradingAgents/graph/workflow_config.py

"""
工作流配置数据模型定义
支持基于JSON配置的工作流定义
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from enum import Enum
from datetime import datetime


class NodeType(str, Enum):
    """节点类型枚举"""
    ANALYST = "analyst"
    RESEARCHER = "researcher"
    MANAGER = "manager"
    TRADER = "trader"
    RISK_ANALYST = "risk_analyst"
    TOOL_NODE = "tool_node"
    MESSAGE_CLEAR = "message_clear"


class EdgeType(str, Enum):
    """边类型枚举"""
    DIRECT = "direct"
    CONDITIONAL = "conditional"
    LOOP = "loop"


class ConditionConfig(BaseModel):
    """条件路由配置"""
    function: str = Field(..., description="条件函数名，如 should_continue_market")
    mapping: Dict[str, str] = Field(..., description="返回值到节点ID的映射")


class NodeConfig(BaseModel):
    """节点配置"""
    id: str = Field(..., description="节点唯一标识")
    type: NodeType = Field(..., description="节点类型")
    name: str = Field(..., description="节点名称")
    category: str = Field(..., description="节点分类（analyst/researcher/manager等）")
    config: Dict[str, Any] = Field(default_factory=dict, description="节点特定配置")
    position: Optional[Dict[str, float]] = Field(None, description="节点在画布上的位置 {x, y}")
    tool_configs: Optional[List[str]] = Field(None, description="工具ID列表，独立配置")


class EdgeConfig(BaseModel):
    """边配置"""
    id: str = Field(..., description="边的唯一标识")
    source: str = Field(..., description="源节点ID，可以是节点ID或'START'")
    target: str = Field(..., description="目标节点ID，可以是节点ID或'END'")
    type: EdgeType = Field(..., description="边类型")
    condition: Optional[ConditionConfig] = Field(None, description="条件路由配置（仅conditional类型需要）")


class WorkflowConfig(BaseModel):
    """工作流配置"""
    version: str = Field(default="1.0", description="配置版本")
    name: str = Field(..., description="工作流名称")
    description: Optional[str] = Field(None, description="工作流描述")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据（创建时间、作者等）")
    nodes: List[NodeConfig] = Field(default_factory=list, description="节点列表")
    edges: List[EdgeConfig] = Field(default_factory=list, description="边列表")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="工作流参数（如max_debate_rounds等）")

    def model_post_init(self, __context: Any) -> None:
        """初始化后处理：自动设置元数据"""
        if "created_at" not in self.metadata:
            self.metadata["created_at"] = datetime.now().isoformat()
        if "updated_at" not in self.metadata:
            self.metadata["updated_at"] = datetime.now().isoformat()

    def update_metadata(self) -> None:
        """更新修改时间"""
        self.metadata["updated_at"] = datetime.now().isoformat()

