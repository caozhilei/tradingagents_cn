"""
智能体工具管理服务
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from bson import ObjectId
from app.core.database import get_mongo_db_sync
from app.models.agent_tool import AgentTool, AgentToolCreate, AgentToolUpdate, AgentToolConfig

logger = logging.getLogger(__name__)


class AgentToolService:
    """智能体工具管理服务类"""
    
    def __init__(self):
        db = get_mongo_db_sync()
        self.tools_collection = db.agent_tools
        self.configs_collection = db.agent_tool_configs
        self._create_indexes()
    
    def _create_indexes(self):
        """创建数据库索引"""
        try:
            self.tools_collection.create_index([("agent_type", 1), ("is_active", 1)])
            self.tools_collection.create_index([("tool_name", 1)])
            self.tools_collection.create_index([("tool_category", 1)])
            self.tools_collection.create_index([("is_system", 1)])
            self.tools_collection.create_index([("is_default", 1)])
            
            self.configs_collection.create_index([("user_id", 1), ("agent_type", 1)], unique=True)
            self.configs_collection.create_index([("tool_ids", 1)])
        except Exception as e:
            logger.warning(f"创建索引失败: {e}")
    
    # ========== 工具管理 ==========
    
    def create_tool(self, tool_data: AgentToolCreate, user_id: Optional[ObjectId] = None) -> AgentTool:
        """创建新工具"""
        # 检查工具名称是否已存在
        existing = self.tools_collection.find_one({
            "tool_name": tool_data.tool_name,
            "agent_type": tool_data.agent_type
        })
        if existing:
            raise ValueError(f"工具名称 '{tool_data.tool_name}' 已存在")
        
        # 如果设置为默认工具，取消其他默认工具
        if tool_data.is_default:
            self.tools_collection.update_many(
                {"agent_type": tool_data.agent_type, "is_default": True},
                {"$set": {"is_default": False}}
            )
        
        tool = AgentTool(
            tool_name=tool_data.tool_name,
            tool_display_name=tool_data.tool_display_name,
            description=tool_data.description,
            agent_type=tool_data.agent_type,
            tool_category=tool_data.tool_category,
            tool_module=tool_data.tool_module,
            tool_method=tool_data.tool_method,
            parameters=tool_data.parameters,
            is_system=False,
            is_default=tool_data.is_default,
            priority=tool_data.priority,
            tags=tool_data.tags,
            created_by=user_id,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        result = self.tools_collection.insert_one(tool.model_dump(by_alias=True, exclude={"id"}))
        tool.id = result.inserted_id
        
        logger.info(f"创建工具成功: {tool_data.tool_name}")
        return tool
    
    def get_tool(self, tool_id: ObjectId) -> Optional[AgentTool]:
        """获取工具"""
        doc = self.tools_collection.find_one({"_id": tool_id})
        if doc:
            return AgentTool(**doc)
        return None
    
    def list_tools(
        self,
        agent_type: Optional[str] = None,
        tool_category: Optional[str] = None,
        is_active: Optional[bool] = True,
        is_system: Optional[bool] = None
    ) -> List[AgentTool]:
        """列出工具"""
        query = {}
        if agent_type:
            query["agent_type"] = agent_type
        if tool_category:
            query["tool_category"] = tool_category
        if is_active is not None:
            query["is_active"] = is_active
        if is_system is not None:
            query["is_system"] = is_system
        
        docs = list(self.tools_collection.find(query).sort("priority", -1))
        return [AgentTool(**doc) for doc in docs]
    
    def get_default_tools(self, agent_type: str) -> List[AgentTool]:
        """获取默认工具列表"""
        docs = list(self.tools_collection.find({
            "agent_type": agent_type,
            "is_default": True,
            "is_active": True
        }).sort("priority", -1))
        
        if not docs:
            # 如果没有默认工具，返回所有启用的工具
            docs = list(self.tools_collection.find({
                "agent_type": agent_type,
                "is_active": True
            }).sort("priority", -1))
        
        return [AgentTool(**doc) for doc in docs]
    
    def update_tool(
        self,
        tool_id: ObjectId,
        update_data: AgentToolUpdate,
        user_id: Optional[ObjectId] = None
    ) -> Optional[AgentTool]:
        """更新工具"""
        update_dict = update_data.model_dump(exclude_unset=True)
        update_dict["updated_at"] = datetime.now()
        
        # 如果设置为默认工具，取消其他默认工具
        if update_data.is_default:
            tool = self.get_tool(tool_id)
            if tool:
                self.tools_collection.update_many(
                    {"agent_type": tool.agent_type, "is_default": True, "_id": {"$ne": tool_id}},
                    {"$set": {"is_default": False}}
                )
        
        result = self.tools_collection.update_one(
            {"_id": tool_id},
            {"$set": update_dict}
        )
        
        if result.modified_count > 0:
            return self.get_tool(tool_id)
        return None
    
    def delete_tool(self, tool_id: ObjectId) -> bool:
        """删除工具（软删除）"""
        result = self.tools_collection.update_one(
            {"_id": tool_id},
            {"$set": {"is_active": False, "updated_at": datetime.now()}}
        )
        return result.modified_count > 0
    
    # ========== 工具注册 ==========
    
    def register_toolkit_tools(self) -> int:
        """注册Toolkit中的所有工具到数据库"""
        try:
            from tradingagents.agents.utils.agent_utils import Toolkit
            import inspect
            
            toolkit = Toolkit()
            registered_count = 0
            
            # 从Toolkit实例中获取所有工具属性
            tool_attrs = [attr for attr in dir(toolkit) if attr.startswith('get_') and not attr.startswith('_')]
            
            # 排除已注释掉的工具
            excluded_tools = ['get_china_stock_data', 'get_hk_stock_data_unified', 
                             'get_fundamentals_openai', 'get_china_fundamentals']
            
            # 扫描Toolkit实例中的所有工具属性
            for tool_attr_name in tool_attrs:
                if tool_attr_name in excluded_tools:
                    continue
                
                try:
                    # 获取工具对象
                    tool_obj = getattr(toolkit, tool_attr_name)
                    
                    # 获取工具方法（如果是类方法，需要从类中获取）
                    if hasattr(Toolkit, tool_attr_name):
                        method = getattr(Toolkit, tool_attr_name)
                    else:
                        continue
                    
                    # 检查是否有@tool装饰器
                    # LangChain的@tool装饰器会给函数添加name属性
                    is_tool = False
                    tool_name = tool_attr_name
                    tool_description = ''
                    
                    # 方法1: 检查工具对象是否有name属性（LangChain工具）
                    if hasattr(tool_obj, 'name'):
                        is_tool = True
                        tool_name = tool_obj.name
                        tool_description = getattr(tool_obj, 'description', '')
                    
                    # 方法2: 检查方法是否有name属性
                    elif hasattr(method, 'name'):
                        is_tool = True
                        tool_name = method.name
                        tool_description = getattr(method, 'description', '')
                    
                    # 方法3: 检查__wrapped__属性（装饰器包装，可能有多个装饰器）
                    elif hasattr(method, '__wrapped__'):
                        # 递归检查所有包装层
                        wrapped = method
                        depth = 0
                        while hasattr(wrapped, '__wrapped__') and depth < 5:  # 限制深度避免无限循环
                            wrapped = wrapped.__wrapped__
                            depth += 1
                            if hasattr(wrapped, 'name'):
                                is_tool = True
                                tool_name = wrapped.name
                                tool_description = getattr(wrapped, 'description', '')
                                break
                    
                    # 方法4: 如果工具对象是可调用的，也认为是工具
                    elif callable(tool_obj):
                        is_tool = True
                        tool_name = tool_attr_name
                    
                    if is_tool:
                        # 从文档字符串获取描述
                        if not tool_description:
                            if hasattr(tool_obj, '__doc__') and tool_obj.__doc__:
                                doc_lines = tool_obj.__doc__.strip().split('\n')
                                tool_description = doc_lines[0] if doc_lines else ''
                            elif method.__doc__:
                                doc_lines = method.__doc__.strip().split('\n')
                                tool_description = doc_lines[0] if doc_lines else ''
                        
                        # 根据工具名称推断适用的智能体类型
                        agent_type = self._infer_agent_type(tool_name)
                        
                        # 检查是否已存在（按tool_name和agent_type）
                        existing = self.tools_collection.find_one({
                            "tool_name": tool_name,
                            "agent_type": agent_type
                        })
                        
                        if not existing:
                            logger.info(f"准备注册工具: {tool_name} -> {agent_type}")
                            tool_data = AgentToolCreate(
                                tool_name=tool_name,
                                tool_display_name=self._format_display_name(tool_name),
                                description=tool_description or f"{tool_name}工具",
                                agent_type=agent_type,
                                tool_category=self._infer_category(tool_name),
                                tool_module="tradingagents.agents.utils.agent_utils.Toolkit",
                                tool_method=tool_attr_name,
                                is_system=True,
                                is_default=self._is_default_tool(tool_name),
                                priority=self._get_priority(tool_name)
                            )
                            
                            self.create_tool(tool_data)
                            registered_count += 1
                            logger.info(f"注册工具: {tool_name} -> {agent_type}")
                
                except Exception as e:
                    logger.warning(f"处理工具 {tool_attr_name} 时出错: {e}")
                    continue
            
            logger.info(f"工具注册完成，共注册 {registered_count} 个工具")
            return registered_count
            
        except Exception as e:
            logger.error(f"注册工具失败: {e}", exc_info=True)
            return 0
    
    def _infer_agent_type(self, tool_name: str) -> str:
        """根据工具名称推断适用的智能体类型"""
        if "fundamentals" in tool_name.lower():
            return "fundamentals_analyst"
        elif "market" in tool_name.lower() or "yfin" in tool_name.lower() or "stockstats" in tool_name.lower():
            return "market_analyst"
        elif "news" in tool_name.lower() or "finnhub" in tool_name.lower() or "reddit" in tool_name.lower():
            return "news_analyst"
        elif "sentiment" in tool_name.lower() or "social" in tool_name.lower():
            return "social_media_analyst"
        else:
            return "market_analyst"  # 默认
    
    def _infer_category(self, tool_name: str) -> str:
        """根据工具名称推断工具类别"""
        if "fundamentals" in tool_name.lower():
            return "fundamentals"
        elif "market" in tool_name.lower() or "yfin" in tool_name.lower():
            return "market"
        elif "news" in tool_name.lower():
            return "news"
        elif "sentiment" in tool_name.lower() or "social" in tool_name.lower():
            return "sentiment"
        else:
            return "data"
    
    def _is_default_tool(self, tool_name: str) -> bool:
        """判断是否为默认工具（统一工具）"""
        return "unified" in tool_name.lower()
    
    def _get_priority(self, tool_name: str) -> int:
        """获取工具优先级"""
        if "unified" in tool_name.lower():
            return 100  # 统一工具优先级最高
        elif "online" in tool_name.lower():
            return 50   # 在线工具
        else:
            return 10   # 其他工具
    
    def _format_display_name(self, tool_name: str) -> str:
        """格式化显示名称"""
        # 将snake_case转换为中文显示名称
        name_map = {
            "get_stock_fundamentals_unified": "统一基本面分析",
            "get_stock_market_data_unified": "统一市场数据",
            "get_stock_news_unified": "统一新闻获取",
            "get_stock_sentiment_unified": "统一情绪分析",
            "get_YFin_data_online": "Yahoo Finance在线数据",
            "get_reddit_stock_info": "Reddit股票信息",
            "get_finnhub_news": "Finnhub新闻",
        }
        return name_map.get(tool_name, tool_name.replace("_", " ").title())
    
    # ========== 用户配置 ==========
    
    def set_user_tool_config(
        self,
        user_id: ObjectId,
        agent_type: str,
        tool_ids: List[ObjectId]
    ) -> AgentToolConfig:
        """设置用户工具配置"""
        config = self.configs_collection.find_one({
            "user_id": user_id,
            "agent_type": agent_type
        })
        
        config_data = {
            "user_id": user_id,
            "agent_type": agent_type,
            "tool_ids": tool_ids,
            "updated_at": datetime.now()
        }
        
        if config:
            self.configs_collection.update_one(
                {"_id": config["_id"]},
                {"$set": config_data}
            )
            config_data["_id"] = config["_id"]
        else:
            config_data["created_at"] = datetime.now()
            result = self.configs_collection.insert_one(config_data)
            config_data["_id"] = result.inserted_id
        
        return AgentToolConfig(**config_data)
    
    def get_user_tool_config(
        self,
        user_id: ObjectId,
        agent_type: str
    ) -> Optional[AgentToolConfig]:
        """获取用户工具配置"""
        config = self.configs_collection.find_one({
            "user_id": user_id,
            "agent_type": agent_type
        })
        
        if config:
            return AgentToolConfig(**config)
        return None
    
    def get_tools_for_agent(
        self,
        user_id: Optional[ObjectId],
        agent_type: str
    ) -> List[AgentTool]:
        """获取智能体可用的工具列表"""
        # 如果有用户配置，使用用户配置
        if user_id:
            config = self.get_user_tool_config(user_id, agent_type)
            if config and config.tool_ids:
                tools = []
                for tool_id in config.tool_ids:
                    tool = self.get_tool(tool_id)
                    if tool and tool.is_active:
                        tools.append(tool)
                if tools:
                    return tools
        
        # 否则使用默认工具
        return self.get_default_tools(agent_type)

