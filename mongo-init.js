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
var defaultWorkflowExists = db.workflow_configs.findOne({ "name": "默认动态图工作流" });
if (!defaultWorkflowExists) {
    db.workflow_configs.insertOne({
        "name": "默认动态图工作流",
        "description": "系统默认的动态图工作流配置",
        "version": "1.0.0",
        "status": "active",
        "graph_config": {
            "nodes": [
                {
                    "id": "start",
                    "type": "start",
                    "label": "开始",
                    "position": { "x": 100, "y": 100 },
                    "properties": {}
                },
                {
                    "id": "data_collection",
                    "type": "agent",
                    "label": "数据采集",
                    "position": { "x": 300, "y": 100 },
                    "properties": {
                        "agent_type": "data_collector",
                        "parameters": {
                            "sources": ["stock_basic_info", "market_quotes"],
                            "frequency": "daily"
                        }
                    }
                },
                {
                    "id": "analysis",
                    "type": "agent",
                    "label": "数据分析",
                    "position": { "x": 500, "y": 100 },
                    "properties": {
                        "agent_type": "analyzer",
                        "parameters": {
                            "strategies": ["fundamental", "technical"],
                            "indicators": ["pe", "pb", "ma"]
                        }
                    }
                },
                {
                    "id": "report_generation",
                    "type": "agent",
                    "label": "报告生成",
                    "position": { "x": 700, "y": 100 },
                    "properties": {
                        "agent_type": "reporter",
                        "parameters": {
                            "format": "markdown",
                            "include_charts": true
                        }
                    }
                },
                {
                    "id": "end",
                    "type": "end",
                    "label": "结束",
                    "position": { "x": 900, "y": 100 },
                    "properties": {}
                }
            ],
            "edges": [
                {
                    "id": "edge1",
                    "source": "start",
                    "target": "data_collection",
                    "label": "开始采集数据"
                },
                {
                    "id": "edge2",
                    "source": "data_collection",
                    "target": "analysis",
                    "label": "数据就绪"
                },
                {
                    "id": "edge3",
                    "source": "analysis",
                    "target": "report_generation",
                    "label": "分析完成"
                },
                {
                    "id": "edge4",
                    "source": "report_generation",
                    "target": "end",
                    "label": "报告完成"
                }
            ],
            "global_settings": {
                "timeout": 3600,
                "concurrency": 1,
                "retry_on_failure": true
            }
        },
        "metadata": {
            "created_at": new Date(),
            "updated_at": new Date(),
            "author": "system",
            "is_default": true,
            "tags": ["default", "dynamic_graph", "workflow"]
        },
        "is_active": true,
        "is_system": true
    });
    print("✅ [MongoDB初始化] 默认动态图工作流添加成功");
} else {
    print("ℹ️ [MongoDB初始化] 默认动态图工作流已存在，跳过添加");
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