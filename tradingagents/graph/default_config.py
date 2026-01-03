# TradingAgents/graph/default_config.py

"""
默认工作流配置生成器
将当前的静态实现转换为默认配置JSON
"""

from .workflow_config import WorkflowConfig, NodeConfig, EdgeConfig, NodeType, EdgeType, ConditionConfig


def generate_default_config(selected_analysts=None) -> WorkflowConfig:
    """
    生成默认的工作流配置（对应当前的静态实现）
    
    Args:
        selected_analysts: 选中的分析师列表，默认为全部
        
    Returns:
        WorkflowConfig对象
    """
    if selected_analysts is None:
        selected_analysts = ["market_analyst", "social_media_analyst", "news_analyst", "fundamentals_analyst"]
    
    nodes = []
    edges = []
    
    # 1. 创建分析师节点（包括对应的工具节点和消息清理节点）
    for i, analyst_type in enumerate(selected_analysts):
        # 从完整形式中提取简短部分用于生成ID（保持向后兼容）
        short_type = analyst_type.replace("_analyst", "").replace("social_media", "social")
        analyst_id = f"{short_type}_analyst"
        tool_id = f"tools_{short_type}"
        clear_id = f"msg_clear_{short_type}"
        
        # 生成节点显示名称
        if analyst_type == "market_analyst":
            display_name = "Market Analyst"
            tool_name = "tools_market"
            clear_name = "Msg Clear Market"
        elif analyst_type == "fundamentals_analyst":
            display_name = "Fundamentals Analyst"
            tool_name = "tools_fundamentals"
            clear_name = "Msg Clear Fundamentals"
        elif analyst_type == "news_analyst":
            display_name = "News Analyst"
            tool_name = "tools_news"
            clear_name = "Msg Clear News"
        elif analyst_type == "social_media_analyst":
            display_name = "Social Media Analyst"
            tool_name = "tools_social"
            clear_name = "Msg Clear Social"
        else:
            display_name = f"{analyst_type.replace('_', ' ').title()}"
            tool_name = f"tools_{short_type}"
            clear_name = f"Msg Clear {short_type.capitalize()}"
        
        # 分析师节点（注意：name字段会被config_based_builder使用，需要与实际节点名称匹配）
        nodes.append(NodeConfig(
            id=analyst_id,
            type=NodeType.ANALYST,
            name=display_name,  # 与实际节点名称匹配
            category="analyst",
            config={
                "agent_type": analyst_type,  # 统一使用 agent_type
                "llm_type": "quick_thinking",
                "max_tool_calls": 3 if analyst_type != "fundamentals_analyst" else 1
            },
            position={"x": 100 + i * 200, "y": 100}
        ))
        
        # 工具节点
        nodes.append(NodeConfig(
            id=tool_id,
            type=NodeType.TOOL_NODE,
            name=tool_name,  # 与实际节点名称匹配
            category="tool",
            config={
                "agent_type": analyst_type  # 统一使用 agent_type
            },
            position={"x": 100 + i * 200, "y": 250}
        ))
        
        # 消息清理节点
        nodes.append(NodeConfig(
            id=clear_id,
            type=NodeType.MESSAGE_CLEAR,
            name=clear_name,  # 与实际节点名称匹配
            category="utility",
            config={
                "agent_type": analyst_type  # 统一使用 agent_type
            },
            position={"x": 100 + i * 200, "y": 400}
        ))
        
        # 连接START到第一个分析师
        if i == 0:
            edges.append(EdgeConfig(
                id=f"start_to_{analyst_id}",
                source="START",
                target=analyst_id,
                type=EdgeType.DIRECT
            ))
        
        # 分析师到工具/清理节点的条件边
        # 注意：条件函数返回的是节点名称（如 "tools_market", "Msg Clear Market"）
        # mapping的键是条件函数返回的值，值是节点ID（会被转换为节点名称）
        # 条件函数名使用完整形式
        condition_func_name = f"should_continue_{analyst_type}"
        edges.append(EdgeConfig(
            id=f"{analyst_id}_to_{tool_id}_conditional",
            source=analyst_id,
            target=tool_id,
            type=EdgeType.CONDITIONAL,
            condition=ConditionConfig(
                function=condition_func_name,
                mapping={
                    tool_name: tool_id,  # 键是条件函数返回的节点名称，值是节点ID
                    clear_name: clear_id
                }
            )
        ))
        
        # 工具节点回到分析师节点
        edges.append(EdgeConfig(
            id=f"{tool_id}_to_{analyst_id}",
            source=tool_id,
            target=analyst_id,
            type=EdgeType.DIRECT
        ))
        
        # 清理节点连接到下一个分析师或研究员
        if i < len(selected_analysts) - 1:
            next_analyst_type = selected_analysts[i+1]
            next_short_type = next_analyst_type.replace("_analyst", "").replace("social_media", "social")
            next_analyst_id = f"{next_short_type}_analyst"
            edges.append(EdgeConfig(
                id=f"{clear_id}_to_{next_analyst_id}",
                source=clear_id,
                target=next_analyst_id,
                type=EdgeType.DIRECT
            ))
        else:
            # 最后一个清理节点连接到看涨研究员
            edges.append(EdgeConfig(
                id=f"{clear_id}_to_bull_researcher",
                source=clear_id,
                target="bull_researcher",
                type=EdgeType.DIRECT
            ))
    
    # 2. 创建研究员节点
    nodes.append(NodeConfig(
        id="bull_researcher",
        type=NodeType.RESEARCHER,
        name="Bull Researcher",  # 与实际节点名称匹配
        category="researcher",
        config={
            "agent_type": "bull_researcher"
        },
        position={"x": 100, "y": 550}
    ))
    
    nodes.append(NodeConfig(
        id="bear_researcher",
        type=NodeType.RESEARCHER,
        name="Bear Researcher",  # 与实际节点名称匹配
        category="researcher",
        config={
            "agent_type": "bear_researcher"
        },
        position={"x": 300, "y": 550}
    ))
    
    # 3. 创建研究经理节点
    nodes.append(NodeConfig(
        id="research_manager",
        type=NodeType.MANAGER,
        name="Research Manager",  # 与实际节点名称匹配
        category="manager",
        config={
            "agent_type": "research_manager"
        },
        position={"x": 200, "y": 700}
    ))
    
    # 4. 研究员之间的条件边（辩论循环）
    # 注意：条件函数should_continue_debate返回的是节点名称（如 "Bear Researcher", "Research Manager"）
    # mapping的键是条件函数返回的值，值是节点ID（会被转换为节点名称）
    edges.append(EdgeConfig(
        id="bull_to_bear_conditional",
        source="bull_researcher",
        target="bear_researcher",
        type=EdgeType.CONDITIONAL,
        condition=ConditionConfig(
            function="should_continue_debate",
            mapping={
                "Bear Researcher": "bear_researcher",  # 键是条件函数返回的节点名称，值是节点ID
                "Research Manager": "research_manager"
            }
        )
    ))
    
    edges.append(EdgeConfig(
        id="bear_to_bull_conditional",
        source="bear_researcher",
        target="bull_researcher",
        type=EdgeType.CONDITIONAL,
        condition=ConditionConfig(
            function="should_continue_debate",
            mapping={
                "Bull Researcher": "bull_researcher",  # 键是条件函数返回的节点名称，值是节点ID
                "Research Manager": "research_manager"
            }
        )
    ))
    
    # 5. 研究经理到交易员
    nodes.append(NodeConfig(
        id="trader",
        type=NodeType.TRADER,
        name="Trader",
        category="trader",
        config={
            "agent_type": "trader"
        },
        position={"x": 200, "y": 850}
    ))
    
    edges.append(EdgeConfig(
        id="research_manager_to_trader",
        source="research_manager",
        target="trader",
        type=EdgeType.DIRECT
    ))
    
    # 6. 创建风险分析师节点
    nodes.append(NodeConfig(
        id="risky_analyst",
        type=NodeType.RISK_ANALYST,
        name="Risky Analyst",
        category="risk_analyst",
        config={
            "agent_type": "aggressive_debator"
        },
        position={"x": 100, "y": 1000}
    ))
    
    nodes.append(NodeConfig(
        id="safe_analyst",
        type=NodeType.RISK_ANALYST,
        name="Safe Analyst",
        category="risk_analyst",
        config={
            "agent_type": "conservative_debator"
        },
        position={"x": 300, "y": 1000}
    ))
    
    nodes.append(NodeConfig(
        id="neutral_analyst",
        type=NodeType.RISK_ANALYST,
        name="Neutral Analyst",
        category="risk_analyst",
        config={
            "agent_type": "neutral_debator"
        },
        position={"x": 500, "y": 1000}
    ))
    
    # 7. 交易员到风险分析师
    edges.append(EdgeConfig(
        id="trader_to_risky_analyst",
        source="trader",
        target="risky_analyst",
        type=EdgeType.DIRECT
    ))
    
    # 8. 风险分析师之间的条件边（风险讨论循环）
    # 注意：条件函数should_continue_risk_analysis返回的是节点名称（如 "Safe Analyst", "Risk Judge"）
    # mapping的键是条件函数返回的值，值是节点ID（会被转换为节点名称）
    edges.append(EdgeConfig(
        id="risky_to_safe_conditional",
        source="risky_analyst",
        target="safe_analyst",
        type=EdgeType.CONDITIONAL,
        condition=ConditionConfig(
            function="should_continue_risk_analysis",
            mapping={
                "Safe Analyst": "safe_analyst",  # 键是条件函数返回的节点名称，值是节点ID
                "Risk Judge": "risk_judge"
            }
        )
    ))
    
    edges.append(EdgeConfig(
        id="safe_to_neutral_conditional",
        source="safe_analyst",
        target="neutral_analyst",
        type=EdgeType.CONDITIONAL,
        condition=ConditionConfig(
            function="should_continue_risk_analysis",
            mapping={
                "Neutral Analyst": "neutral_analyst",  # 键是条件函数返回的节点名称，值是节点ID
                "Risk Judge": "risk_judge"
            }
        )
    ))
    
    edges.append(EdgeConfig(
        id="neutral_to_risky_conditional",
        source="neutral_analyst",
        target="risky_analyst",
        type=EdgeType.CONDITIONAL,
        condition=ConditionConfig(
            function="should_continue_risk_analysis",
            mapping={
                "Risky Analyst": "risky_analyst",  # 键是条件函数返回的节点名称，值是节点ID
                "Risk Judge": "risk_judge"
            }
        )
    ))
    
    # 9. 创建风险经理节点
    nodes.append(NodeConfig(
        id="risk_judge",
        type=NodeType.MANAGER,
        name="Risk Judge",  # 与实际节点名称匹配（注意：这里不是"Risk Manager"）
        category="manager",
        config={
            "agent_type": "risk_manager"
        },
        position={"x": 200, "y": 1150}
    ))
    
    # 10. 风险经理到END
    edges.append(EdgeConfig(
        id="risk_judge_to_end",
        source="risk_judge",
        target="END",
        type=EdgeType.DIRECT
    ))
    
    return WorkflowConfig(
        name="默认股票分析流程",
        description="标准的多智能体股票分析工作流",
        nodes=nodes,
        edges=edges,
        parameters={
            "selected_analysts": selected_analysts,
            "max_debate_rounds": 1,
            "max_risk_discuss_rounds": 1
        },
        metadata={
            "author": "system",
            "is_default": True
        }
    )

