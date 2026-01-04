// MongoDB初始化脚本 - TradingAgents-CN v1.0.0-preview
// 用于在容器首次启动时初始化数据库和用户

// 连接到admin数据库
conn = new Mongo();
db = conn.getDB("admin");

// 登录管理员账号
db.auth("admin", "tradingagents123");

// 创建主数据库
db = conn.getDB("tradingagents");

// 创建数据库用户
// 注意：只在用户不存在时创建
// 用户名：tradingagents
// 密码：tradingagents123
// 角色：readWrite

// 检查用户是否已存在
var userExists = db.getUser("tradingagents");
if (!userExists) {
    db.createUser({
        user: "tradingagents",
        pwd: "tradingagents123",
        roles: [
            {
                role: "readWrite",
                db: "tradingagents"
            }
        ]
    });
    print("✅ [MongoDB初始化] 用户 'tradingagents' 创建成功");
} else {
    print("ℹ️ [MongoDB初始化] 用户 'tradingagents' 已存在，跳过创建");
}

// 创建集合和索引（如果不存在）
// 优化查询性能

// 通用函数：创建集合（如果不存在）
function createCollectionIfNotExists(collectionName) {
    if (!db[collectionName].exists()) {
        db.createCollection(collectionName);
        print(`✅ [MongoDB初始化] 集合 '${collectionName}' 创建成功`);
        return true;
    }
    return false;
}

// 1. 用户相关集合
print("\n📋 [MongoDB初始化] 创建用户相关集合和索引...");
createCollectionIfNotExists("users");
db.users.createIndex({ "username": 1 }, { unique: true });
db.users.createIndex({ "email": 1 }, { unique: true });

createCollectionIfNotExists("user_sessions");
db.user_sessions.createIndex({ "user_id": 1 });
db.user_sessions.createIndex({ "created_at": -1 });
db.user_sessions.createIndex({ "expires_at": 1 }, { expireAfterSeconds: 0 });

createCollectionIfNotExists("user_activities");
db.user_activities.createIndex({ "user_id": 1, "created_at": -1 });

// 2. 股票数据集合（A股）
print("\n📋 [MongoDB初始化] 创建A股数据集合和索引...");
createCollectionIfNotExists("stock_basic_info");
db.stock_basic_info.createIndex({ "code": 1, "source": 1 }, { unique: true });
db.stock_basic_info.createIndex({ "code": 1 });
db.stock_basic_info.createIndex({ "source": 1 });
db.stock_basic_info.createIndex({ "market": 1 });
db.stock_basic_info.createIndex({ "industry": 1 });
db.stock_basic_info.createIndex({ "total_mv": -1 });
db.stock_basic_info.createIndex({ "pe": 1 });
db.stock_basic_info.createIndex({ "pb": 1 });

createCollectionIfNotExists("market_quotes");
db.market_quotes.createIndex({ "code": 1 }, { unique: true });
db.market_quotes.createIndex({ "symbol": 1, "timestamp": -1 });
db.market_quotes.createIndex({ "pct_chg": -1 });
db.market_quotes.createIndex({ "amount": -1 });
db.market_quotes.createIndex({ "updated_at": -1 });

createCollectionIfNotExists("stock_daily_quotes");
db.stock_daily_quotes.createIndex({ "stock_code": 1, "trade_date": -1 });
db.stock_daily_quotes.createIndex({ "trade_date": -1 });
db.stock_daily_quotes.createIndex({ "created_at": -1 });

createCollectionIfNotExists("stock_financial_data");
db.stock_financial_data.createIndex({ "stock_code": 1, "report_date": -1 });
db.stock_financial_data.createIndex({ "report_type": 1 });
db.stock_financial_data.createIndex({ "created_at": -1 });

createCollectionIfNotExists("stock_news");
db.stock_news.createIndex({ "code": 1, "published_at": -1 });

// 3. 港股数据集合
print("\n📋 [MongoDB初始化] 创建港股数据集合和索引...");
createCollectionIfNotExists("stock_basic_info_hk");
db.stock_basic_info_hk.createIndex({ "code": 1, "source": 1 }, { unique: true });
db.stock_basic_info_hk.createIndex({ "code": 1 });
db.stock_basic_info_hk.createIndex({ "source": 1 });
db.stock_basic_info_hk.createIndex({ "market": 1 });
db.stock_basic_info_hk.createIndex({ "industry": 1 });
db.stock_basic_info_hk.createIndex({ "updated_at": 1 });

createCollectionIfNotExists("market_quotes_hk");
db.market_quotes_hk.createIndex({ "code": 1 }, { unique: true });
db.market_quotes_hk.createIndex({ "updated_at": 1 });

createCollectionIfNotExists("stock_daily_quotes_hk");
db.stock_daily_quotes_hk.createIndex({ "code": 1, "trade_date": -1 });
db.stock_daily_quotes_hk.createIndex({ "updated_at": 1 });

createCollectionIfNotExists("stock_financial_data_hk");
db.stock_financial_data_hk.createIndex({ "code": 1, "report_date": -1 });
db.stock_financial_data_hk.createIndex({ "updated_at": 1 });

createCollectionIfNotExists("stock_news_hk");
db.stock_news_hk.createIndex({ "code": 1, "published_at": -1 });

// 4. 美股数据集合
print("\n📋 [MongoDB初始化] 创建美股数据集合和索引...");
createCollectionIfNotExists("stock_basic_info_us");
db.stock_basic_info_us.createIndex({ "code": 1, "source": 1 }, { unique: true });
db.stock_basic_info_us.createIndex({ "code": 1 });
db.stock_basic_info_us.createIndex({ "source": 1 });
db.stock_basic_info_us.createIndex({ "market": 1 });
db.stock_basic_info_us.createIndex({ "industry": 1 });
db.stock_basic_info_us.createIndex({ "sector": 1 });
db.stock_basic_info_us.createIndex({ "updated_at": 1 });

createCollectionIfNotExists("market_quotes_us");
db.market_quotes_us.createIndex({ "code": 1 }, { unique: true });
db.market_quotes_us.createIndex({ "updated_at": 1 });

createCollectionIfNotExists("stock_daily_quotes_us");
db.stock_daily_quotes_us.createIndex({ "code": 1, "trade_date": -1 });
db.stock_daily_quotes_us.createIndex({ "updated_at": 1 });

createCollectionIfNotExists("stock_financial_data_us");
db.stock_financial_data_us.createIndex({ "code": 1, "report_date": -1 });
db.stock_financial_data_us.createIndex({ "updated_at": 1 });

createCollectionIfNotExists("stock_news_us");
db.stock_news_us.createIndex({ "code": 1, "published_at": -1 });

// 5. 分析相关集合
print("\n📋 [MongoDB初始化] 创建分析相关集合和索引...");
createCollectionIfNotExists("analysis_tasks");
db.analysis_tasks.createIndex({ "task_id": 1 }, { unique: true });
db.analysis_tasks.createIndex({ "user_id": 1 });
db.analysis_tasks.createIndex({ "status": 1 });
db.analysis_tasks.createIndex({ "created_at": -1 });
db.analysis_tasks.createIndex({ "analysis_date": 1 });

createCollectionIfNotExists("analysis_results");
db.analysis_results.createIndex({ "analysis_id": 1 }, { unique: true });
db.analysis_results.createIndex({ "stock_code": 1 });
db.analysis_results.createIndex({ "analysis_date": 1 });
db.analysis_results.createIndex({ "created_at": -1 });

createCollectionIfNotExists("analysis_reports");
db.analysis_reports.createIndex({ "task_id": 1 });
db.analysis_reports.createIndex({ "created_at": -1 });

// 6. 提示词模板相关集合
print("\n📋 [MongoDB初始化] 创建提示词模板相关集合和索引...");
createCollectionIfNotExists("prompt_templates");
db.prompt_templates.createIndex({ "agent_type": 1, "template_name": 1 });
db.prompt_templates.createIndex({ "agent_type": 1, "is_default": 1 });
db.prompt_templates.createIndex({ "is_system": 1 });
db.prompt_templates.createIndex({ "created_by": 1 });
db.prompt_templates.createIndex({ "is_active": 1 });

createCollectionIfNotExists("prompt_template_versions");
db.prompt_template_versions.createIndex({ "template_id": 1, "version": 1 });

createCollectionIfNotExists("user_template_configs");
db.user_template_configs.createIndex({ "user_id": 1, "agent_type": 1 }, { unique: true });
db.user_template_configs.createIndex({ "template_id": 1 });

// 7. 工具配置相关集合
print("\n📋 [MongoDB初始化] 创建工具配置相关集合和索引...");
createCollectionIfNotExists("agent_tools");
db.agent_tools.createIndex({ "agent_type": 1, "is_active": 1 });
db.agent_tools.createIndex({ "tool_name": 1 });
db.agent_tools.createIndex({ "tool_category": 1 });
db.agent_tools.createIndex({ "is_system": 1 });
db.agent_tools.createIndex({ "is_default": 1 });

createCollectionIfNotExists("agent_tool_configs");
db.agent_tool_configs.createIndex({ "user_id": 1, "agent_type": 1 }, { unique: true });
db.agent_tool_configs.createIndex({ "tool_ids": 1 });

createCollectionIfNotExists("tool_configs");
db.tool_configs.createIndex({ "tool_name": 1 }, { unique: true });
db.tool_configs.createIndex({ "category": 1 });
db.tool_configs.createIndex({ "tool_type": 1 });
db.tool_configs.createIndex({ "enabled": 1 });
db.tool_configs.createIndex({ "is_system": 1 });

// 8. 工作流配置集合
print("\n📋 [MongoDB初始化] 创建工作流配置相关集合和索引...");
createCollectionIfNotExists("workflow_configs");
db.workflow_configs.createIndex({ "name": 1 }, { unique: true });
db.workflow_configs.createIndex({ "metadata.created_at": -1 });
db.workflow_configs.createIndex({ "metadata.author": 1 });

// 9. 系统配置相关集合
print("\n📋 [MongoDB初始化] 创建系统配置相关集合和索引...");
createCollectionIfNotExists("system_config");
db.system_config.createIndex({ "key": 1 }, { unique: true });

createCollectionIfNotExists("system_configs");
db.system_configs.createIndex({ "version": 1 });
db.system_configs.createIndex({ "is_active": 1 });

createCollectionIfNotExists("operation_logs");
db.operation_logs.createIndex({ "user_id": 1 });
db.operation_logs.createIndex({ "action": 1 });
db.operation_logs.createIndex({ "created_at": -1 });

// 10. 多市场统一字典集合
print("\n📋 [MongoDB初始化] 创建多市场统一字典集合和索引...");
createCollectionIfNotExists("market_metadata");
db.market_metadata.createIndex({ "market_type": 1 });
db.market_metadata.createIndex({ "exchange_code": 1 });

createCollectionIfNotExists("industry_mapping");
db.industry_mapping.createIndex({ "source_industry": 1, "source_type": 1 });
db.industry_mapping.createIndex({ "target_industry": 1 });

createCollectionIfNotExists("symbol_registry");
db.symbol_registry.createIndex({ "symbol": 1, "market": 1 }, { unique: true });
db.symbol_registry.createIndex({ "code": 1 });

// 11. 社交媒体相关集合
print("\n📋 [MongoDB初始化] 创建社交媒体相关集合和索引...");
createCollectionIfNotExists("social_media_posts");
db.social_media_posts.createIndex({ "platform": 1, "verified": 1, "created_at": -1 });
db.social_media_posts.createIndex({ "hashtags": 1 });
db.social_media_posts.createIndex({ "keywords": 1 });
db.social_media_posts.createIndex({ "topics": 1 });
db.social_media_posts.createIndex({ "data_source": 1 });

// 12. 数据源配置集合
print("\n📋 [MongoDB初始化] 创建数据源配置集合和索引...");
createCollectionIfNotExists("data_source_configs");
db.data_source_configs.createIndex({ "source_name": 1 }, { unique: true });
db.data_source_configs.createIndex({ "source_type": 1 });
db.data_source_configs.createIndex({ "status": 1 });

createCollectionIfNotExists("data_sync_logs");
db.data_sync_logs.createIndex({ "source_name": 1, "created_at": -1 });
db.data_sync_logs.createIndex({ "status": 1 });

// 13. 模型目录集合
print("\n📋 [MongoDB初始化] 创建模型目录集合和索引...");
createCollectionIfNotExists("model_catalog");
db.model_catalog.createIndex({ "provider": 1 });
db.model_catalog.createIndex({ "model_name": 1, "provider": 1 }, { unique: true });

// 14. 系统状态集合
print("\n📋 [MongoDB初始化] 创建系统状态集合和索引...");
createCollectionIfNotExists("system_status");
db.system_status.createIndex({ "component": 1 });
db.system_status.createIndex({ "created_at": -1 });

// 15. 分析偏好集合
print("\n📋 [MongoDB初始化] 创建分析偏好集合和索引...");
createCollectionIfNotExists("analysis_preferences");
db.analysis_preferences.createIndex({ "name": 1 });
db.analysis_preferences.createIndex({ "category": 1 });

// 16. 系统通知集合
print("\n📋 [MongoDB初始化] 创建系统通知集合和索引...");
createCollectionIfNotExists("notifications");
db.notifications.createIndex({ "user_id": 1 });
db.notifications.createIndex({ "is_read": 1 });
db.notifications.createIndex({ "created_at": -1 });

// 17. 添加默认动态图工作流
print("\n📋 [MongoDB初始化] 添加默认动态图工作流...");

// 检查默认工作流是否已存在
var defaultWorkflowExists = db.workflow_configs.findOne({ "name": "默认股票分析流程" });
if (!defaultWorkflowExists) {
    db.workflow_configs.insertOne({
        "name": "默认股票分析流程",
        "description": "标准的多智能体股票分析工作流",
        "version": "1.0.0",
        "status": "active",
        "parameters": {
            "selected_analysts": ["market_analyst", "social_media_analyst", "news_analyst", "fundamentals_analyst"],
            "max_debate_rounds": 1,
            "max_risk_discuss_rounds": 1
        },
        "nodes": [
            {
                "id": "market_analyst",
                "type": "analyst",
                "name": "Market Analyst",
                "category": "analyst",
                "config": {
                    "agent_type": "market_analyst",
                    "llm_type": "quick_thinking",
                    "max_tool_calls": 3
                },
                "position": { "x": 100, "y": 100 }
            },
            {
                "id": "tools_market",
                "type": "tool_node",
                "name": "tools_market",
                "category": "tool",
                "config": {
                    "agent_type": "market_analyst"
                },
                "position": { "x": 100, "y": 250 }
            },
            {
                "id": "msg_clear_market",
                "type": "message_clear",
                "name": "Msg Clear Market",
                "category": "utility",
                "config": {
                    "agent_type": "market_analyst"
                },
                "position": { "x": 100, "y": 400 }
            },
            {
                "id": "social_analyst",
                "type": "analyst",
                "name": "Social Media Analyst",
                "category": "analyst",
                "config": {
                    "agent_type": "social_media_analyst",
                    "llm_type": "quick_thinking",
                    "max_tool_calls": 3
                },
                "position": { "x": 300, "y": 100 }
            },
            {
                "id": "tools_social",
                "type": "tool_node",
                "name": "tools_social",
                "category": "tool",
                "config": {
                    "agent_type": "social_media_analyst"
                },
                "position": { "x": 300, "y": 250 }
            },
            {
                "id": "msg_clear_social",
                "type": "message_clear",
                "name": "Msg Clear Social",
                "category": "utility",
                "config": {
                    "agent_type": "social_media_analyst"
                },
                "position": { "x": 300, "y": 400 }
            },
            {
                "id": "news_analyst",
                "type": "analyst",
                "name": "News Analyst",
                "category": "analyst",
                "config": {
                    "agent_type": "news_analyst",
                    "llm_type": "quick_thinking",
                    "max_tool_calls": 3
                },
                "position": { "x": 500, "y": 100 }
            },
            {
                "id": "tools_news",
                "type": "tool_node",
                "name": "tools_news",
                "category": "tool",
                "config": {
                    "agent_type": "news_analyst"
                },
                "position": { "x": 500, "y": 250 }
            },
            {
                "id": "msg_clear_news",
                "type": "message_clear",
                "name": "Msg Clear News",
                "category": "utility",
                "config": {
                    "agent_type": "news_analyst"
                },
                "position": { "x": 500, "y": 400 }
            },
            {
                "id": "fundamentals_analyst",
                "type": "analyst",
                "name": "Fundamentals Analyst",
                "category": "analyst",
                "config": {
                    "agent_type": "fundamentals_analyst",
                    "llm_type": "quick_thinking",
                    "max_tool_calls": 1
                },
                "position": { "x": 700, "y": 100 }
            },
            {
                "id": "tools_fundamentals",
                "type": "tool_node",
                "name": "tools_fundamentals",
                "category": "tool",
                "config": {
                    "agent_type": "fundamentals_analyst"
                },
                "position": { "x": 700, "y": 250 }
            },
            {
                "id": "msg_clear_fundamentals",
                "type": "message_clear",
                "name": "Msg Clear Fundamentals",
                "category": "utility",
                "config": {
                    "agent_type": "fundamentals_analyst"
                },
                "position": { "x": 700, "y": 400 }
            },
            {
                "id": "bull_researcher",
                "type": "researcher",
                "name": "Bull Researcher",
                "category": "researcher",
                "config": {
                    "agent_type": "bull_researcher"
                },
                "position": { "x": 100, "y": 550 }
            },
            {
                "id": "bear_researcher",
                "type": "researcher",
                "name": "Bear Researcher",
                "category": "researcher",
                "config": {
                    "agent_type": "bear_researcher"
                },
                "position": { "x": 300, "y": 550 }
            },
            {
                "id": "research_manager",
                "type": "manager",
                "name": "Research Manager",
                "category": "manager",
                "config": {
                    "agent_type": "research_manager"
                },
                "position": { "x": 200, "y": 700 }
            },
            {
                "id": "trader",
                "type": "trader",
                "name": "Trader",
                "category": "trader",
                "config": {
                    "agent_type": "trader"
                },
                "position": { "x": 200, "y": 850 }
            },
            {
                "id": "risky_analyst",
                "type": "risk_analyst",
                "name": "Risky Analyst",
                "category": "risk_analyst",
                "config": {
                    "agent_type": "aggressive_debator"
                },
                "position": { "x": 100, "y": 1000 }
            },
            {
                "id": "safe_analyst",
                "type": "risk_analyst",
                "name": "Safe Analyst",
                "category": "risk_analyst",
                "config": {
                    "agent_type": "conservative_debator"
                },
                "position": { "x": 300, "y": 1000 }
            },
            {
                "id": "neutral_analyst",
                "type": "risk_analyst",
                "name": "Neutral Analyst",
                "category": "risk_analyst",
                "config": {
                    "agent_type": "neutral_debator"
                },
                "position": { "x": 500, "y": 1000 }
            },
            {
                "id": "risk_judge",
                "type": "manager",
                "name": "Risk Judge",
                "category": "manager",
                "config": {
                    "agent_type": "risk_manager"
                },
                "position": { "x": 200, "y": 1150 }
            }
        ],
        "edges": [
            {
                "id": "start_to_market_analyst",
                "source": "START",
                "target": "market_analyst",
                "type": "direct"
            },
            {
                "id": "market_analyst_to_tools_market_conditional",
                "source": "market_analyst",
                "target": "tools_market",
                "type": "conditional",
                "condition": {
                    "function": "should_continue_market_analyst",
                    "mapping": {
                        "tools_market": "tools_market",
                        "Msg Clear Market": "msg_clear_market"
                    }
                }
            },
            {
                "id": "tools_market_to_market_analyst",
                "source": "tools_market",
                "target": "market_analyst",
                "type": "direct"
            },
            {
                "id": "msg_clear_market_to_social_analyst",
                "source": "msg_clear_market",
                "target": "social_analyst",
                "type": "direct"
            },
            {
                "id": "social_analyst_to_tools_social_conditional",
                "source": "social_analyst",
                "target": "tools_social",
                "type": "conditional",
                "condition": {
                    "function": "should_continue_social_media_analyst",
                    "mapping": {
                        "tools_social": "tools_social",
                        "Msg Clear Social": "msg_clear_social"
                    }
                }
            },
            {
                "id": "tools_social_to_social_analyst",
                "source": "tools_social",
                "target": "social_analyst",
                "type": "direct"
            },
            {
                "id": "msg_clear_social_to_news_analyst",
                "source": "msg_clear_social",
                "target": "news_analyst",
                "type": "direct"
            },
            {
                "id": "news_analyst_to_tools_news_conditional",
                "source": "news_analyst",
                "target": "tools_news",
                "type": "conditional",
                "condition": {
                    "function": "should_continue_news_analyst",
                    "mapping": {
                        "tools_news": "tools_news",
                        "Msg Clear News": "msg_clear_news"
                    }
                }
            },
            {
                "id": "tools_news_to_news_analyst",
                "source": "tools_news",
                "target": "news_analyst",
                "type": "direct"
            },
            {
                "id": "msg_clear_news_to_fundamentals_analyst",
                "source": "msg_clear_news",
                "target": "fundamentals_analyst",
                "type": "direct"
            },
            {
                "id": "fundamentals_analyst_to_tools_fundamentals_conditional",
                "source": "fundamentals_analyst",
                "target": "tools_fundamentals",
                "type": "conditional",
                "condition": {
                    "function": "should_continue_fundamentals_analyst",
                    "mapping": {
                        "tools_fundamentals": "tools_fundamentals",
                        "Msg Clear Fundamentals": "msg_clear_fundamentals"
                    }
                }
            },
            {
                "id": "tools_fundamentals_to_fundamentals_analyst",
                "source": "tools_fundamentals",
                "target": "fundamentals_analyst",
                "type": "direct"
            },
            {
                "id": "msg_clear_fundamentals_to_bull_researcher",
                "source": "msg_clear_fundamentals",
                "target": "bull_researcher",
                "type": "direct"
            },
            {
                "id": "bull_to_bear_conditional",
                "source": "bull_researcher",
                "target": "bear_researcher",
                "type": "conditional",
                "condition": {
                    "function": "should_continue_debate",
                    "mapping": {
                        "Bear Researcher": "bear_researcher",
                        "Research Manager": "research_manager"
                    }
                }
            },
            {
                "id": "bear_to_bull_conditional",
                "source": "bear_researcher",
                "target": "bull_researcher",
                "type": "conditional",
                "condition": {
                    "function": "should_continue_debate",
                    "mapping": {
                        "Bull Researcher": "bull_researcher",
                        "Research Manager": "research_manager"
                    }
                }
            },
            {
                "id": "research_manager_to_trader",
                "source": "research_manager",
                "target": "trader",
                "type": "direct"
            },
            {
                "id": "trader_to_risky_analyst",
                "source": "trader",
                "target": "risky_analyst",
                "type": "direct"
            },
            {
                "id": "risky_to_safe_conditional",
                "source": "risky_analyst",
                "target": "safe_analyst",
                "type": "conditional",
                "condition": {
                    "function": "should_continue_risk_analysis",
                    "mapping": {
                        "Safe Analyst": "safe_analyst",
                        "Risk Judge": "risk_judge"
                    }
                }
            },
            {
                "id": "safe_to_neutral_conditional",
                "source": "safe_analyst",
                "target": "neutral_analyst",
                "type": "conditional",
                "condition": {
                    "function": "should_continue_risk_analysis",
                    "mapping": {
                        "Neutral Analyst": "neutral_analyst",
                        "Risk Judge": "risk_judge"
                    }
                }
            },
            {
                "id": "neutral_to_risky_conditional",
                "source": "neutral_analyst",
                "target": "risky_analyst",
                "type": "conditional",
                "condition": {
                    "function": "should_continue_risk_analysis",
                    "mapping": {
                        "Risky Analyst": "risky_analyst",
                        "Risk Judge": "risk_judge"
                    }
                }
            },
            {
                "id": "risk_judge_to_end",
                "source": "risk_judge",
                "target": "END",
                "type": "direct"
            }
        ],
        "metadata": {
            "created_at": new Date(),
            "updated_at": new Date(),
            "author": "system",
            "is_default": true,
            "tags": ["default", "stock_analysis", "workflow"]
        },
        "is_active": true,
        "is_system": true
    });
    print("✅ [MongoDB初始化] 默认股票分析流程添加成功");
} else {
    print("ℹ️ [MongoDB初始化] 默认股票分析流程已存在，跳过添加");
}

// 完成初始化
print("\n🎉 [MongoDB初始化] 数据库初始化完成");
print("📋 数据库信息:");
print("   数据库名: tradingagents");
print("   用户名: tradingagents");
print("   密码: tradingagents123");
print("   角色: readWrite");
print("🔧 所有集合和索引已创建，优化查询性能");
print("📊 支持多市场数据: A股、港股、美股");
print("🚀 系统已准备就绪，可以开始使用了");