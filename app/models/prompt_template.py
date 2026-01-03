"""
智能体提示词模板数据模型
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict
from bson import ObjectId
from .user import PyObjectId


from enum import Enum

class AgentType(str, Enum):
    """智能体类型"""
    # 分析师
    FUNDAMENTALS_ANALYST = "fundamentals_analyst"
    MARKET_ANALYST = "market_analyst"
    NEWS_ANALYST = "news_analyst"
    SOCIAL_MEDIA_ANALYST = "social_media_analyst"
    
    # 研究员
    BULL_RESEARCHER = "bull_researcher"
    BEAR_RESEARCHER = "bear_researcher"
    
    # 交易员
    TRADER = "trader"
    
    # 风险管理
    AGGRESSIVE_DEBATOR = "aggressive_debator"
    CONSERVATIVE_DEBATOR = "conservative_debator"
    NEUTRAL_DEBATOR = "neutral_debator"
    
    # 管理层
    RESEARCH_MANAGER = "research_manager"
    RISK_MANAGER = "risk_manager"


class PromptTemplateContent(BaseModel):
    """提示词模板内容"""
    system_prompt: str = Field(..., description="系统提示词")
    tool_guidance: Optional[str] = Field(None, description="工具调用指导")
    analysis_requirements: Optional[str] = Field(None, description="分析要求")
    output_format: Optional[str] = Field(None, description="输出格式要求")
    constraints: Optional[Dict[str, List[str]]] = Field(None, description="约束条件")
    variables: Optional[Dict[str, str]] = Field(None, description="模板变量说明")


class PromptTemplate(BaseModel):
    """提示词模板模型"""
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    agent_type: str = Field(..., description="智能体类型")
    agent_name: str = Field(..., description="智能体名称（中文）")
    template_name: str = Field(..., description="模板名称")
    template_display_name: str = Field(..., description="模板显示名称")
    description: Optional[str] = Field(None, description="模板描述")
    
    # 模板内容
    content: PromptTemplateContent = Field(..., description="模板内容")
    
    # 元数据
    version: int = Field(default=1, description="版本号")
    is_system: bool = Field(default=True, description="是否为系统模板")
    is_default: bool = Field(default=False, description="是否为默认模板")
    is_active: bool = Field(default=True, description="是否启用")
    
    # 用户信息
    created_by: Optional[PyObjectId] = Field(None, description="创建者ID")
    updated_by: Optional[PyObjectId] = Field(None, description="更新者ID")
    
    # 标签和分类
    tags: List[str] = Field(default_factory=list, description="标签")
    category: Optional[str] = Field(None, description="分类")
    
    # 时间戳
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    # 统计信息
    usage_count: int = Field(default=0, description="使用次数")
    last_used_at: Optional[datetime] = Field(None, description="最后使用时间")
    
    # 工具配置
    tool_configs: Optional[List[str]] = Field(None, description="工具ID列表，覆盖智能体默认配置")
    
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_schema_extra={
            "example": {
                "agent_type": "fundamentals_analyst",
                "agent_name": "基本面分析师",
                "template_name": "default",
                "template_display_name": "默认模板",
                "description": "标准的基本面分析提示词",
                "content": {
                    "system_prompt": "你是一位专业的股票基本面分析师...",
                    "tool_guidance": "立即调用 get_stock_fundamentals_unified 工具...",
                    "analysis_requirements": "- 财务数据分析\n- 估值指标分析",
                    "output_format": "## 公司基本信息\n## 财务数据分析",
                    "constraints": {
                        "forbidden": ["不允许假设数据"],
                        "required": ["必须调用工具"]
                    }
                },
                "is_system": True,
                "is_default": True,
                "tags": ["default", "fundamentals"]
            }
        }
    )


class PromptTemplateVersion(BaseModel):
    """提示词模板版本历史"""
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    template_id: PyObjectId = Field(..., description="模板ID")
    version: int = Field(..., description="版本号")
    content: PromptTemplateContent = Field(..., description="模板内容快照")
    change_description: Optional[str] = Field(None, description="变更说明")
    changed_by: Optional[PyObjectId] = Field(None, description="变更者ID")
    created_at: datetime = Field(default_factory=datetime.now)
    
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True
    )


class AgentTemplateConfig(BaseModel):
    """智能体模板配置（用户选择）"""
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId = Field(..., description="用户ID")
    agent_type: str = Field(..., description="智能体类型")
    template_id: PyObjectId = Field(..., description="选中的模板ID")
    template_name: str = Field(..., description="模板名称（冗余，便于查询）")
    is_active: bool = Field(default=True, description="是否启用")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True
    )


class PromptTemplateCreate(BaseModel):
    """创建模板请求"""
    agent_type: str
    agent_name: str
    template_name: str
    template_display_name: str
    description: Optional[str] = None
    content: PromptTemplateContent
    tags: List[str] = Field(default_factory=list)
    category: Optional[str] = None
    is_default: bool = False
    tool_configs: Optional[List[str]] = Field(None, description="工具ID列表，覆盖智能体默认配置")


class PromptTemplateUpdate(BaseModel):
    """更新模板请求"""
    template_display_name: Optional[str] = None
    description: Optional[str] = None
    content: Optional[PromptTemplateContent] = None
    tags: Optional[List[str]] = None
    category: Optional[str] = None
    is_default: Optional[bool] = None
    is_active: Optional[bool] = None
    change_description: Optional[str] = None
    tool_configs: Optional[List[str]] = Field(None, description="工具ID列表，覆盖智能体默认配置")

