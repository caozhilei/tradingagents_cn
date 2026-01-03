# TradingAgents/graph/node_registry.py

"""
节点注册表，管理所有可用的节点类型和工厂方法
根据配置创建对应的节点实例
"""

from typing import Dict, Callable, Any
from .workflow_config import NodeConfig, NodeType
from tradingagents.agents import (
    create_market_analyst,
    create_social_media_analyst,
    create_news_analyst,
    create_fundamentals_analyst,
    create_bull_researcher,
    create_bear_researcher,
    create_research_manager,
    create_risk_manager,
    create_trader,
    create_risky_debator,
    create_safe_debator,
    create_neutral_debator,
    create_msg_delete,
)

from tradingagents.utils.logging_init import get_logger
logger = get_logger("default")


class NodeRegistry:
    """节点注册表，管理所有可用的节点类型和工厂方法"""
    
    def __init__(self, graph_setup_instance):
        """
        初始化节点注册表
        
        Args:
            graph_setup_instance: GraphSetup实例，包含所有创建节点所需的资源
        """
        self.graph_setup = graph_setup_instance
        self._factories: Dict[str, Callable] = {}
        self._register_default_nodes()
    
    def _register_default_nodes(self):
        """注册所有默认节点类型的工厂方法"""
        # 注册分析师节点
        self._factories[NodeType.ANALYST.value] = self._create_analyst_node
        # 注册工具节点
        self._factories[NodeType.TOOL_NODE.value] = self._create_tool_node
        # 注册消息清理节点
        self._factories[NodeType.MESSAGE_CLEAR.value] = self._create_message_clear
        # 注册研究员节点
        self._factories[NodeType.RESEARCHER.value] = self._create_researcher_node
        # 注册管理节点
        self._factories[NodeType.MANAGER.value] = self._create_manager_node
        # 注册交易员节点
        self._factories[NodeType.TRADER.value] = self._create_trader_node
        # 注册风险分析师节点
        self._factories[NodeType.RISK_ANALYST.value] = self._create_risk_analyst_node
    
    def create_node(self, node_config: NodeConfig):
        """
        根据配置创建节点实例
        
        Args:
            node_config: 节点配置对象
            
        Returns:
            节点函数（可调用对象）
        """
        factory = self._factories.get(node_config.type.value)
        if not factory:
            raise ValueError(f"Unknown node type: {node_config.type}")
        return factory(node_config)
    
    def _create_analyst_node(self, config: NodeConfig):
        """创建分析师节点"""
        # 优先使用 agent_type，向后兼容支持 analyst_type
        agent_type = config.config.get("agent_type") or config.config.get("analyst_type")
        if not agent_type:
            raise ValueError("Analyst node requires agent_type in config")
        
        llm_type = config.config.get("llm_type", "quick_thinking")
        
        # 根据llm_type选择合适的LLM
        llm = self.graph_setup.quick_thinking_llm if llm_type == "quick_thinking" else self.graph_setup.deep_thinking_llm
        
        # 直接使用完整形式进行判断
        if agent_type == "market_analyst":
            return create_market_analyst(llm, self.graph_setup.toolkit)
        elif agent_type == "social_media_analyst":
            return create_social_media_analyst(llm, self.graph_setup.toolkit)
        elif agent_type == "news_analyst":
            return create_news_analyst(llm, self.graph_setup.toolkit)
        elif agent_type == "fundamentals_analyst":
            return create_fundamentals_analyst(llm, self.graph_setup.toolkit)
        else:
            raise ValueError(f"Unknown analyst type: {agent_type}")
    
    def _create_researcher_node(self, config: NodeConfig):
        """创建研究员节点"""
        # 优先使用 agent_type，向后兼容支持 researcher_type
        agent_type = config.config.get("agent_type") or config.config.get("researcher_type") or "bull_researcher"
        
        # 支持完整形式和简短形式（向后兼容）
        if agent_type == "bull_researcher" or agent_type == "bull":
            return create_bull_researcher(
                self.graph_setup.quick_thinking_llm,
                self.graph_setup.bull_memory
            )
        elif agent_type == "bear_researcher" or agent_type == "bear":
            return create_bear_researcher(
                self.graph_setup.quick_thinking_llm,
                self.graph_setup.bear_memory
            )
        else:
            raise ValueError(f"Unknown researcher type: {agent_type}")
    
    def _create_manager_node(self, config: NodeConfig):
        """创建管理节点"""
        # 优先使用 agent_type，向后兼容支持 manager_type
        agent_type = config.config.get("agent_type") or config.config.get("manager_type") or "research_manager"
        
        # 支持完整形式和简短形式（向后兼容）
        if agent_type == "research_manager" or agent_type == "research":
            return create_research_manager(
                self.graph_setup.deep_thinking_llm,
                self.graph_setup.invest_judge_memory
            )
        elif agent_type == "risk_manager" or agent_type == "risk":
            return create_risk_manager(
                self.graph_setup.deep_thinking_llm,
                self.graph_setup.risk_manager_memory
            )
        else:
            raise ValueError(f"Unknown manager type: {agent_type}")
    
    def _create_trader_node(self, config: NodeConfig):
        """创建交易员节点"""
        return create_trader(
            self.graph_setup.quick_thinking_llm,
            self.graph_setup.trader_memory
        )
    
    def _create_risk_analyst_node(self, config: NodeConfig):
        """创建风险分析师节点"""
        # 优先使用 agent_type，向后兼容支持 risk_type
        agent_type = config.config.get("agent_type") or config.config.get("risk_type") or "aggressive_debator"
        
        # 支持完整形式和简短形式（向后兼容）
        if agent_type == "aggressive_debator" or agent_type == "risky":
            return create_risky_debator(self.graph_setup.quick_thinking_llm)
        elif agent_type == "conservative_debator" or agent_type == "safe":
            return create_safe_debator(self.graph_setup.quick_thinking_llm)
        elif agent_type == "neutral_debator" or agent_type == "neutral":
            return create_neutral_debator(self.graph_setup.quick_thinking_llm)
        else:
            raise ValueError(f"Unknown risk analyst type: {agent_type}")
    
    def _create_tool_node(self, config: NodeConfig):
        """创建工具节点"""
        # 优先使用 agent_type，向后兼容支持 analyst_type
        agent_type = config.config.get("agent_type") or config.config.get("analyst_type")
        if not agent_type:
            raise ValueError("Tool node requires agent_type in config")
        
        # 从完整形式转换为简短形式（工具节点字典使用简短形式作为键）
        short_type = agent_type.replace("_analyst", "").replace("social_media", "social")
        
        # 先尝试使用完整形式查找，如果找不到则使用简短形式
        tool_node = self.graph_setup.tool_nodes.get(agent_type)
        if not tool_node:
            tool_node = self.graph_setup.tool_nodes.get(short_type)
        
        if not tool_node:
            raise ValueError(f"Tool node not found for agent type: {agent_type} (tried: {agent_type}, {short_type})")
        
        return tool_node
    
    def _create_message_clear(self, config: NodeConfig):
        """创建消息清理节点"""
        # 消息清理节点不需要额外参数
        return create_msg_delete()

