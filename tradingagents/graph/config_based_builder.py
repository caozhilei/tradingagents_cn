# TradingAgents/graph/config_based_builder.py

"""
基于配置的图构建器
根据WorkflowConfig动态构建LangGraph
"""

from langgraph.graph import StateGraph, START, END
from typing import Dict
from .workflow_config import WorkflowConfig, EdgeConfig, NodeType, EdgeType
from .node_registry import NodeRegistry
from tradingagents.agents.utils.agent_states import AgentState

from tradingagents.utils.logging_init import get_logger
logger = get_logger("default")


class ConfigBasedGraphBuilder:
    """基于配置的图构建器"""
    
    def __init__(self, graph_setup_instance):
        """
        初始化图构建器
        
        Args:
            graph_setup_instance: GraphSetup实例
        """
        self.graph_setup = graph_setup_instance
        self.node_registry = NodeRegistry(graph_setup_instance)
    
    def build_graph(self, config: WorkflowConfig):
        """
        根据配置构建LangGraph
        
        Args:
            config: 工作流配置对象
            
        Returns:
            编译后的LangGraph实例
        """
        logger.info(f"🏗️ 开始构建工作流图: {config.name}")
        
        # 创建StateGraph
        workflow = StateGraph(AgentState)
        
        # 1. 创建所有节点并添加到图中
        node_id_to_name: Dict[str, str] = {}
        node_instances: Dict[str, any] = {}
        
        for node_config in config.nodes:
            # 生成节点显示名称
            node_name = self._generate_node_name(node_config)
            node_id_to_name[node_config.id] = node_name
            
            # 创建节点实例
            try:
                node_instance = self.node_registry.create_node(node_config)
                node_instances[node_config.id] = node_instance
                
                # 添加到图中
                workflow.add_node(node_name, node_instance)
                logger.debug(f"✅ 添加节点: {node_name} (id: {node_config.id})")
            except Exception as e:
                logger.error(f"❌ 创建节点失败 {node_config.id}: {e}")
                raise ValueError(f"Failed to create node {node_config.id}: {e}")
        
        # 2. 添加边
        for edge_config in config.edges:
            try:
                source = self._resolve_node_name(edge_config.source, node_id_to_name, is_source=True)
                target = self._resolve_node_name(edge_config.target, node_id_to_name, is_source=False)
                
                if edge_config.type == EdgeType.DIRECT:
                    workflow.add_edge(source, target)
                    logger.debug(f"✅ 添加直接边: {source} -> {target}")
                    
                elif edge_config.type == EdgeType.CONDITIONAL:
                    if not edge_config.condition:
                        raise ValueError(f"Conditional edge {edge_config.id} requires condition config")
                    
                    condition_func = self._get_condition_function(edge_config.condition)
                    # 将mapping中的节点ID转换为节点名称
                    mapped_routes = {}
                    for key, node_id in edge_config.condition.mapping.items():
                        mapped_routes[key] = self._resolve_node_name(node_id, node_id_to_name, is_source=False)
                    
                    workflow.add_conditional_edges(
                        source,
                        condition_func,
                        mapped_routes
                    )
                    logger.debug(f"✅ 添加条件边: {source} -> {target} (条件: {edge_config.condition.function})")
                    
                elif edge_config.type == EdgeType.LOOP:
                    # Loop边实际上也是直接边，但可以用于标记循环结构
                    workflow.add_edge(source, target)
                    logger.debug(f"✅ 添加循环边: {source} -> {target}")
                else:
                    raise ValueError(f"Unknown edge type: {edge_config.type}")
                    
            except Exception as e:
                logger.error(f"❌ 添加边失败 {edge_config.id}: {e}")
                raise ValueError(f"Failed to add edge {edge_config.id}: {e}")
        
        logger.info(f"✅ 工作流图构建完成: {config.name}")
        
        # 编译并返回
        return workflow.compile()
    
    def _generate_node_name(self, node_config) -> str:
        """
        生成节点显示名称
        
        Args:
            node_config: 节点配置
            
        Returns:
            节点名称字符串
        """
        # 如果配置中已有名称，使用配置的名称
        if node_config.name:
            return node_config.name
        
        # 否则根据类型和配置生成名称
        # 优先使用 agent_type，向后兼容支持特定类型字段
        agent_type = node_config.config.get("agent_type")
        
        if node_config.type == NodeType.ANALYST:
            # 向后兼容：如果没有 agent_type，尝试从 analyst_type 读取
            if not agent_type:
                agent_type = node_config.config.get("analyst_type", "unknown")
            # 从完整形式转换为显示名称
            if agent_type == "market_analyst":
                return "Market Analyst"
            elif agent_type == "fundamentals_analyst":
                return "Fundamentals Analyst"
            elif agent_type == "news_analyst":
                return "News Analyst"
            elif agent_type == "social_media_analyst":
                return "Social Media Analyst"
            else:
                return f"{agent_type.replace('_', ' ').title()}"
        elif node_config.type == NodeType.RESEARCHER:
            # 向后兼容：如果没有 agent_type，尝试从 researcher_type 读取
            if not agent_type:
                agent_type = node_config.config.get("researcher_type", "unknown")
            # 支持完整形式和简短形式
            if agent_type == "bull_researcher" or agent_type == "bull":
                return "Bull Researcher"
            elif agent_type == "bear_researcher" or agent_type == "bear":
                return "Bear Researcher"
            else:
                # 从完整形式提取显示名称
                short_type = agent_type.replace("_researcher", "")
                return f"{short_type.capitalize()} Researcher"
        elif node_config.type == NodeType.MANAGER:
            # 向后兼容：如果没有 agent_type，尝试从 manager_type 读取
            if not agent_type:
                agent_type = node_config.config.get("manager_type", "unknown")
            # 支持完整形式和简短形式
            if agent_type == "research_manager" or agent_type == "research":
                return "Research Manager"
            elif agent_type == "risk_manager" or agent_type == "risk":
                return "Risk Manager"
            else:
                # 从完整形式提取显示名称
                short_type = agent_type.replace("_manager", "")
                return f"{short_type.capitalize()} Manager"
        elif node_config.type == NodeType.TRADER:
            return "Trader"
        elif node_config.type == NodeType.RISK_ANALYST:
            # 向后兼容：如果没有 agent_type，尝试从 risk_type 读取
            if not agent_type:
                agent_type = node_config.config.get("risk_type", "unknown")
            # 支持完整形式和简短形式
            if agent_type == "aggressive_debator" or agent_type == "risky":
                return "Risky Analyst"
            elif agent_type == "conservative_debator" or agent_type == "safe":
                return "Safe Analyst"
            elif agent_type == "neutral_debator" or agent_type == "neutral":
                return "Neutral Analyst"
            else:
                # 从完整形式提取显示名称
                short_type = agent_type.replace("_debator", "")
                return f"{short_type.capitalize()} Analyst"
        elif node_config.type == NodeType.TOOL_NODE:
            # 向后兼容：如果没有 agent_type，尝试从 analyst_type 读取
            if not agent_type:
                agent_type = node_config.config.get("analyst_type", "unknown")
            # 从完整形式提取简短部分
            short_type = agent_type.replace("_analyst", "").replace("social_media", "social")
            return f"tools_{short_type}"
        elif node_config.type == NodeType.MESSAGE_CLEAR:
            # 向后兼容：如果没有 agent_type，尝试从 analyst_type 读取
            if not agent_type:
                agent_type = node_config.config.get("analyst_type", "unknown")
            # 从完整形式转换为显示名称
            if agent_type == "market_analyst":
                return "Msg Clear Market"
            elif agent_type == "fundamentals_analyst":
                return "Msg Clear Fundamentals"
            elif agent_type == "news_analyst":
                return "Msg Clear News"
            elif agent_type == "social_media_analyst":
                return "Msg Clear Social"
            else:
                short_type = agent_type.replace("_analyst", "").replace("social_media", "social")
                return f"Msg Clear {short_type.capitalize()}"
        else:
            return node_config.id
    
    def _resolve_node_name(self, node_id: str, node_id_to_name: Dict[str, str], is_source: bool = True) -> any:
        """
        解析节点名称，支持START和END特殊节点
        
        Args:
            node_id: 节点ID或"START"/"END"
            node_id_to_name: 节点ID到名称的映射
            is_source: 是否为源节点
            
        Returns:
            START/END常量或节点名称字符串
        """
        if node_id == "START":
            return START
        elif node_id == "END":
            if is_source:
                raise ValueError("END cannot be a source node")
            return END
        else:
            node_name = node_id_to_name.get(node_id)
            if not node_name:
                raise ValueError(f"Node not found: {node_id}")
            return node_name
    
    def _get_condition_function(self, condition_config):
        """
        获取条件路由函数
        
        Args:
            condition_config: 条件配置对象
            
        Returns:
            条件函数
        """
        func_name = condition_config.function
        conditional_logic = self.graph_setup.conditional_logic
        
        if not hasattr(conditional_logic, func_name):
            raise ValueError(f"Condition function not found: {func_name}")
        
        func = getattr(conditional_logic, func_name)
        logger.debug(f"📋 获取条件函数: {func_name}")
        return func

