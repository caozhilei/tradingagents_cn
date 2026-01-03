"""
工具配置管理服务
"""

import logging
import inspect
from typing import List, Optional, Dict, Any
from datetime import datetime
from bson import ObjectId
from app.core.database import get_mongo_db_sync
from app.models.tool_config import (
    ToolConfig,
    AgentToolConfig,
    ToolConfigCreate,
    ToolConfigUpdate,
    AgentToolConfigCreate,
    AgentToolConfigUpdate,
    ToolParameter
)

logger = logging.getLogger(__name__)


class ToolConfigService:
    """工具配置管理服务"""
    
    def __init__(self):
        try:
            self.db = get_mongo_db_sync()
            self.tools_collection = self.db.tool_configs
            self.agent_tools_collection = self.db.agent_tool_configs
        except Exception as e:
            logger.warning(f"使用统一数据库连接失败，使用直接连接: {e}")
            from pymongo import MongoClient
            from app.core.config import settings
            self.client = MongoClient(
                settings.MONGO_URI,
                maxPoolSize=settings.MONGO_MAX_CONNECTIONS,
                minPoolSize=settings.MONGO_MIN_CONNECTIONS,
                serverSelectionTimeoutMS=5000
            )
            self.db = self.client[settings.MONGO_DB]
            self.tools_collection = self.db.tool_configs
            self.agent_tools_collection = self.db.agent_tool_configs
        
        # 创建索引
        self._create_indexes()
    
    def _create_indexes(self):
        """创建数据库索引"""
        try:
            self.tools_collection.create_index([("tool_name", 1)], unique=True)
            self.tools_collection.create_index([("category", 1)])
            self.tools_collection.create_index([("tool_type", 1)])
            self.tools_collection.create_index([("enabled", 1)])
            self.tools_collection.create_index([("is_system", 1)])
            
            self.agent_tools_collection.create_index([("agent_type", 1)], unique=True)
        except Exception as e:
            logger.warning(f"创建索引失败: {e}")
    
    # ========== 工具配置管理 ==========
    
    def get_all_tools(
        self,
        category: Optional[str] = None,
        tool_type: Optional[str] = None,
        enabled: Optional[bool] = None
    ) -> List[ToolConfig]:
        """获取所有工具列表"""
        query = {}
        if category:
            query["category"] = category
        if tool_type:
            query["tool_type"] = tool_type
        if enabled is not None:
            query["enabled"] = enabled
        
        tools = list(self.tools_collection.find(query).sort("priority", 1))
        return [ToolConfig(**tool) for tool in tools]
    
    def get_tool_by_id(self, tool_id: str) -> Optional[ToolConfig]:
        """根据ID获取工具"""
        tool = self.tools_collection.find_one({"_id": ObjectId(tool_id)})
        return ToolConfig(**tool) if tool else None
    
    def get_tool_by_name(self, tool_name: str) -> Optional[ToolConfig]:
        """根据名称获取工具"""
        tool = self.tools_collection.find_one({"tool_name": tool_name})
        return ToolConfig(**tool) if tool else None
    
    def create_tool_config(self, tool_data: ToolConfigCreate) -> ToolConfig:
        """创建工具配置"""
        # 检查工具名称是否已存在
        existing = self.tools_collection.find_one({"tool_name": tool_data.tool_name})
        if existing:
            raise ValueError(f"工具名称 '{tool_data.tool_name}' 已存在")
        
        # 转换参数
        parameters = [
            ToolParameter(**param) if isinstance(param, dict) else param
            for param in tool_data.parameters
        ]
        
        tool = ToolConfig(
            tool_name=tool_data.tool_name,
            tool_display_name=tool_data.tool_display_name,
            description=tool_data.description,
            category=tool_data.category,
            tool_type=tool_data.tool_type,
            supported_markets=tool_data.supported_markets,
            parameters=parameters,
            default_config=tool_data.default_config,
            enabled=tool_data.enabled,
            priority=tool_data.priority,
            is_system=False
        )
        
        result = self.tools_collection.insert_one(tool.model_dump(exclude={"id"}))
        tool.id = result.inserted_id
        return tool
    
    def update_tool_config(self, tool_id: str, updates: ToolConfigUpdate) -> Optional[ToolConfig]:
        """更新工具配置"""
        update_data = updates.model_dump(exclude_unset=True)
        
        if "parameters" in update_data and update_data["parameters"]:
            update_data["parameters"] = [
                ToolParameter(**param) if isinstance(param, dict) else param
                for param in update_data["parameters"]
            ]
        
        update_data["updated_at"] = datetime.now()
        
        result = self.tools_collection.update_one(
            {"_id": ObjectId(tool_id)},
            {"$set": update_data}
        )
        
        if result.modified_count > 0:
            return self.get_tool_by_id(tool_id)
        return None
    
    def delete_tool_config(self, tool_id: str) -> bool:
        """删除工具配置"""
        tool = self.get_tool_by_id(tool_id)
        if tool and tool.is_system:
            raise ValueError("不能删除系统工具")
        
        result = self.tools_collection.delete_one({"_id": ObjectId(tool_id)})
        return result.deleted_count > 0
    
    # ========== 智能体工具配置管理 ==========
    
    def get_agent_tool_config(self, agent_type: str) -> Optional[AgentToolConfig]:
        """获取智能体工具配置"""
        config = self.agent_tools_collection.find_one({"agent_type": agent_type})
        return AgentToolConfig(**config) if config else None
    
    def create_agent_tool_config(self, config_data: AgentToolConfigCreate) -> AgentToolConfig:
        """创建智能体工具配置"""
        # 检查是否已存在
        existing = self.agent_tools_collection.find_one({"agent_type": config_data.agent_type})
        if existing:
            raise ValueError(f"智能体 '{config_data.agent_type}' 的工具配置已存在")
        
        config = AgentToolConfig(
            agent_type=config_data.agent_type,
            tool_configs=config_data.tool_configs,
            default_tools=config_data.default_tools,
            tool_priorities=config_data.tool_priorities
        )
        
        result = self.agent_tools_collection.insert_one(config.model_dump(exclude={"id"}))
        config.id = result.inserted_id
        return config
    
    def update_agent_tool_config(
        self,
        agent_type: str,
        updates: AgentToolConfigUpdate
    ) -> Optional[AgentToolConfig]:
        """更新智能体工具配置"""
        update_data = updates.model_dump(exclude_unset=True)
        update_data["updated_at"] = datetime.now()
        
        result = self.agent_tools_collection.update_one(
            {"agent_type": agent_type},
            {"$set": update_data},
            upsert=True
        )
        
        if result.modified_count > 0 or result.upserted_id:
            return self.get_agent_tool_config(agent_type)
        return None
    
    # ========== 工具初始化 ==========
    
    def initialize_tools_from_toolkit(self) -> Dict[str, Any]:
        """从Toolkit类初始化工具到数据库"""
        try:
            from tradingagents.agents.utils.agent_utils import Toolkit
            
            initialized_count = 0
            skipped_count = 0
            error_count = 0
            
            # 获取Toolkit类的所有成员（包括方法和工具对象）
            toolkit_instance = Toolkit()
            # 获取所有成员（不仅仅是可调用的，因为工具可能是对象）
            members = inspect.getmembers(toolkit_instance)
            
            # 智能体默认工具映射
            agent_default_tools = {
                "market_analyst": "get_stock_market_data_unified",
                "fundamentals_analyst": "get_stock_fundamentals_unified",
                "news_analyst": "get_stock_news_unified",
                "social_media_analyst": "get_stock_sentiment_unified"
            }
            
            for member_name, member in members:
                # 跳过私有方法和特殊方法
                if member_name.startswith('_'):
                    continue
                
                # 跳过非工具方法（工具方法通常以get_开头）
                if not member_name.startswith('get_'):
                    continue
                
                # 检查是否是工具方法
                # 工具方法通常有name属性（来自@tool装饰器）
                is_tool = False
                
                # 获取实际的函数对象
                if inspect.ismethod(member):
                    func = getattr(member, '__func__', member)
                elif inspect.isfunction(member):
                    func = member
                else:
                    func = member
                
                # 方法1: 检查成员本身是否有name属性（LangChain工具）
                if hasattr(member, 'name'):
                    is_tool = True
                # 方法2: 检查函数是否有name属性
                elif hasattr(func, 'name'):
                    is_tool = True
                # 方法3: 检查是否被@tool装饰（通过检查__wrapped__和name属性）
                elif hasattr(func, '__wrapped__'):
                    # 递归检查所有包装层
                    wrapped = func
                    depth = 0
                    while hasattr(wrapped, '__wrapped__') and depth < 10:  # 防止无限循环
                        wrapped = wrapped.__wrapped__
                        if hasattr(wrapped, 'name'):
                            is_tool = True
                            break
                        depth += 1
                
                # 方法4: 检查函数是否有工具相关的特征
                # LangChain的@tool装饰器会给函数添加特定属性
                if not is_tool:
                    # 检查是否有args_schema属性（LangChain工具的特征）
                    if hasattr(member, 'args_schema') or hasattr(func, 'args_schema'):
                        is_tool = True
                    # 检查是否有description属性（LangChain工具的特征）
                    elif hasattr(member, 'description') or hasattr(func, 'description'):
                        is_tool = True
                
                # 方法5: 如果方法名以get_开头且有文档字符串，认为是工具（备用方案）
                if not is_tool and member_name.startswith('get_'):
                    # 检查是否有文档字符串（工具通常有文档）
                    if hasattr(func, '__doc__') and func.__doc__:
                        # 如果方法名符合工具命名规范且有文档，认为是工具
                        is_tool = True
                
                if not is_tool:
                    continue
                
                # 使用member_name作为工具名称
                method_name = member_name
                
                try:
                    # 检查工具是否已存在
                    existing = self.get_tool_by_name(method_name)
                    if existing:
                        skipped_count += 1
                        continue
                    
                    # 提取工具元数据
                    tool_meta = self._extract_tool_metadata(method_name, member)
                    
                    # 创建工具配置
                    tool_config = ToolConfigCreate(**tool_meta)
                    self.create_tool_config(tool_config)
                    initialized_count += 1
                    
                    logger.info(f"✅ 初始化工具: {method_name}")
                    
                except Exception as e:
                    logger.error(f"❌ 初始化工具 {method_name} 失败: {e}")
                    error_count += 1
            
            # 为每个智能体类型创建默认工具配置
            for agent_type, default_tool_name in agent_default_tools.items():
                default_tool = self.get_tool_by_name(default_tool_name)
                if default_tool:
                    try:
                        agent_config = self.get_agent_tool_config(agent_type)
                        if not agent_config:
                            self.create_agent_tool_config(AgentToolConfigCreate(
                                agent_type=agent_type,
                                tool_configs=[str(default_tool.id)],
                                default_tools=[str(default_tool.id)],
                                tool_priorities={str(default_tool.id): 1}
                            ))
                            logger.info(f"✅ 创建智能体 {agent_type} 的默认工具配置")
                    except Exception as e:
                        logger.error(f"❌ 创建智能体 {agent_type} 工具配置失败: {e}")
            
            return {
                "initialized": initialized_count,
                "skipped": skipped_count,
                "errors": error_count
            }
            
        except Exception as e:
            logger.error(f"❌ 工具初始化失败: {e}", exc_info=True)
            raise
    
    def _extract_tool_metadata(self, method_name: str, method: Any) -> Dict[str, Any]:
        """提取工具元数据"""
        # 检查是否是StructuredTool对象
        from langchain_core.tools import StructuredTool
        if isinstance(method, StructuredTool):
            # 直接从StructuredTool对象提取元数据
            tool_name = method.name if hasattr(method, 'name') else method_name
            tool_description = method.description if hasattr(method, 'description') else ""
            
            # 提取参数信息
            parameters = []
            if hasattr(method, 'args_schema') and method.args_schema:
                schema = method.args_schema
                if hasattr(schema, 'model_fields'):
                    for param_name, field_info in schema.model_fields.items():
                        param_type = str(field_info.annotation) if hasattr(field_info, 'annotation') else "str"
                        param_desc = field_info.description if hasattr(field_info, 'description') and field_info.description else ""
                        param_required = field_info.is_required() if hasattr(field_info, 'is_required') else True
                        param_default = field_info.default if hasattr(field_info, 'default') and field_info.default != inspect.Parameter.empty else None
                        
                        parameters.append({
                            "name": param_name,
                            "type": param_type,
                            "description": param_desc,
                            "required": param_required,
                            "default": param_default
                        })
            
            # 推断工具类型和支持的市场
            tool_type = self._infer_tool_type(tool_name)
            supported_markets = self._infer_supported_markets(tool_name, tool_description)
            
            return {
                "tool_name": tool_name,
                "tool_display_name": self._generate_display_name(tool_name),
                "description": tool_description,
                "category": self._infer_category(tool_name),
                "tool_type": tool_type,
                "supported_markets": supported_markets,
                "parameters": parameters,
                "default_config": {
                    "timeout": 30,
                    "retry_times": 3
                },
                "enabled": True,
                "priority": 1 if tool_type == "unified" else 100
            }
        
        # 获取工具函数（对于普通方法）
        # 对于方法，需要获取__func__
        if inspect.ismethod(method) and hasattr(method, '__func__'):
            tool_func = method.__func__
        elif inspect.isfunction(method):
            tool_func = method
        else:
            tool_func = method
        
        # 处理装饰器包装（@tool装饰器会包装函数）
        while hasattr(tool_func, '__wrapped__'):
            tool_func = tool_func.__wrapped__
        
        # 获取文档字符串
        docstring = inspect.getdoc(tool_func) or ""
        
        # 获取函数签名
        try:
            sig = inspect.signature(tool_func)
        except (ValueError, TypeError) as e:
            # 如果无法获取签名，使用默认值
            logger.warning(f"无法获取工具 {method_name} 的函数签名: {e}")
            sig = None
        
        # 提取参数
        parameters = []
        if sig:
            for param_name, param in sig.parameters.items():
                if param_name == 'self':
                    continue
                
                param_type = "str"
                param_desc = ""
                param_required = param.default == inspect.Parameter.empty
                
                # 从Annotated类型中提取信息
                if param.annotation != inspect.Parameter.empty:
                    try:
                        # 处理Annotated类型
                        if hasattr(param.annotation, '__origin__'):
                            # 检查是否是Annotated类型
                            import typing
                            if typing.get_origin(param.annotation) is typing.Annotated:
                                # 提取类型和描述
                                args = typing.get_args(param.annotation)
                                if args:
                                    param_type = str(args[0])
                                    if len(args) > 1 and isinstance(args[1], str):
                                        param_desc = args[1]
                            else:
                                param_type = str(param.annotation)
                        else:
                            param_type = str(param.annotation)
                    except Exception:
                        param_type = "str"
                
                # 尝试从docstring中提取参数描述
                if not param_desc and param_name in docstring:
                    # 简单提取，实际可以更复杂
                    pass
                
                parameters.append({
                    "name": param_name,
                    "type": param_type,
                    "description": param_desc,
                    "required": param_required,
                    "default": param.default if param.default != inspect.Parameter.empty else None
                })
        
        # 推断工具分类和类型
        category = self._infer_category(method_name)
        tool_type = self._infer_tool_type(method_name)
        supported_markets = self._infer_supported_markets(method_name, docstring)
        
        # 生成显示名称
        display_name = self._generate_display_name(method_name)
        
        return {
            "tool_name": method_name,
            "tool_display_name": display_name,
            "description": docstring,
            "category": category,
            "tool_type": tool_type,
            "supported_markets": supported_markets,
            "parameters": parameters,
            "default_config": {
                "timeout": 30,
                "retry_times": 3
            },
            "enabled": True,
            "priority": 1 if tool_type == "unified" else 100
        }
    
    def _infer_category(self, tool_name: str) -> str:
        """推断工具分类"""
        if "market" in tool_name.lower():
            return "market_data"
        elif "fundamental" in tool_name.lower():
            return "fundamentals"
        elif "news" in tool_name.lower():
            return "news"
        elif "sentiment" in tool_name.lower() or "social" in tool_name.lower():
            return "sentiment"
        else:
            return "other"
    
    def _infer_tool_type(self, tool_name: str) -> str:
        """推断工具类型"""
        if "unified" in tool_name.lower():
            return "unified"
        elif "online" in tool_name.lower():
            return "online"
        else:
            return "offline"
    
    def _infer_supported_markets(self, tool_name: str, docstring: str) -> List[str]:
        """推断支持的市场"""
        markets = []
        docstring_lower = docstring.lower()
        tool_name_lower = tool_name.lower()
        
        if "a股" in docstring_lower or "china" in tool_name_lower or "chinese" in tool_name_lower:
            markets.append("A股")
        if "港股" in docstring_lower or "hk" in tool_name_lower or "hongkong" in tool_name_lower:
            markets.append("港股")
        if "美股" in docstring_lower or "us" in tool_name_lower or "stock" in tool_name_lower:
            markets.append("美股")
        
        # 如果包含unified，通常支持所有市场
        if "unified" in tool_name_lower and not markets:
            markets = ["A股", "港股", "美股"]
        
        return markets if markets else ["A股", "港股", "美股"]
    
    def _generate_display_name(self, tool_name: str) -> str:
        """生成显示名称"""
        # 移除get_前缀
        name = tool_name.replace("get_", "")
        
        # 替换下划线为空格并首字母大写
        words = name.split("_")
        display_name = " ".join(word.capitalize() for word in words)
        
        # 特殊处理
        if "unified" in name:
            display_name = display_name.replace("Unified", "统一工具")
        if "online" in name:
            display_name = display_name.replace("Online", "在线工具")
        
        return display_name
