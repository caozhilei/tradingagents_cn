// MongoDB初始化脚本 - TradingAgents-CN v1.0.0-preview
// 用于Docker部署时初始化数据库和集合

// 切换到tradingagents数据库
db = db.getSiblingDB('tradingagents');

// ===== 创建集合 =====

print('开始创建数据库集合...');

// 用户相关
db.createCollection('users');
db.createCollection('user_sessions');
db.createCollection('user_activities');

// 股票数据（A股）
db.createCollection('stock_basic_info');
db.createCollection('market_quotes');
db.createCollection('stock_daily_quotes');
db.createCollection('stock_financial_data');
db.createCollection('stock_news');

// 股票数据（港股）
db.createCollection('stock_basic_info_hk');
db.createCollection('market_quotes_hk');
db.createCollection('stock_daily_quotes_hk');
db.createCollection('stock_financial_data_hk');
db.createCollection('stock_news_hk');

// 股票数据（美股）
db.createCollection('stock_basic_info_us');
db.createCollection('market_quotes_us');
db.createCollection('stock_daily_quotes_us');
db.createCollection('stock_financial_data_us');
db.createCollection('stock_news_us');

// 分析相关
db.createCollection('analysis_tasks');
db.createCollection('analysis_results');
db.createCollection('analysis_reports');
db.createCollection('analysis_progress');
db.createCollection('analysis_preferences');

// 提示词模板相关
db.createCollection('prompt_templates');
db.createCollection('prompt_template_versions');
db.createCollection('user_template_configs');

// 工具配置相关
db.createCollection('agent_tools');
db.createCollection('agent_tool_configs');
db.createCollection('tool_configs');

// 筛选和收藏
db.createCollection('screening_results');
db.createCollection('favorites');
db.createCollection('tags');

// 工作流配置
db.createCollection('workflow_configs');

// 系统配置
db.createCollection('system_config');
db.createCollection('system_configs');
db.createCollection('operation_logs');
db.createCollection('system_logs');

// 多市场统一字典
db.createCollection('market_metadata');
db.createCollection('industry_mapping');
db.createCollection('symbol_registry');

// 社交媒体相关
db.createCollection('social_media_posts');

// 数据源配置
db.createCollection('data_source_configs');
db.createCollection('data_sync_logs');

// 模型目录
db.createCollection('model_catalog');

// 系统状态
db.createCollection('system_status');

// 系统通知
db.createCollection('notifications');

print('✅ 所有集合创建完成');

// ===== 创建索引 =====

print('\n开始创建索引...');

// 用户相关索引
db.users.createIndex({ "username": 1 }, { unique: true });
db.users.createIndex({ "email": 1 }, { unique: true });

db.user_sessions.createIndex({ "user_id": 1 });
db.user_sessions.createIndex({ "created_at": -1 });
db.user_sessions.createIndex({ "expires_at": 1 }, { expireAfterSeconds: 0 });

db.user_activities.createIndex({ "user_id": 1, "created_at": -1 });

// 股票数据索引（A股）
db.stock_basic_info.createIndex({ "code": 1, "source": 1 }, { unique: true });
db.stock_basic_info.createIndex({ "code": 1 });
db.stock_basic_info.createIndex({ "source": 1 });
db.stock_basic_info.createIndex({ "market": 1 });
db.stock_basic_info.createIndex({ "industry": 1 });

db.market_quotes.createIndex({ "code": 1 }, { unique: true });
db.market_quotes.createIndex({ "updated_at": 1 });

db.stock_daily_quotes.createIndex({ "stock_code": 1, "trade_date": -1 });
db.stock_daily_quotes.createIndex({ "trade_date": -1 });

db.stock_financial_data.createIndex({ "stock_code": 1, "report_date": -1 });
db.stock_financial_data.createIndex({ "report_type": 1 });

db.stock_news.createIndex({ "code": 1, "published_at": -1 });
db.stock_news.createIndex({ "title": "text", "content": "text" });

// 港股数据索引
db.stock_basic_info_hk.createIndex({ "code": 1, "source": 1 }, { unique: true });
db.stock_basic_info_hk.createIndex({ "code": 1 });
db.stock_basic_info_hk.createIndex({ "updated_at": 1 });

db.market_quotes_hk.createIndex({ "code": 1 }, { unique: true });
db.market_quotes_hk.createIndex({ "updated_at": 1 });

db.stock_daily_quotes_hk.createIndex({ "code": 1, "trade_date": -1 });

db.stock_financial_data_hk.createIndex({ "code": 1, "report_date": -1 });

db.stock_news_hk.createIndex({ "code": 1, "published_at": -1 });

// 美股数据索引
db.stock_basic_info_us.createIndex({ "code": 1, "source": 1 }, { unique: true });
db.stock_basic_info_us.createIndex({ "code": 1 });
db.stock_basic_info_us.createIndex({ "updated_at": 1 });

db.market_quotes_us.createIndex({ "code": 1 }, { unique: true });
db.market_quotes_us.createIndex({ "updated_at": 1 });

db.stock_daily_quotes_us.createIndex({ "code": 1, "trade_date": -1 });

db.stock_financial_data_us.createIndex({ "code": 1, "report_date": -1 });

db.stock_news_us.createIndex({ "code": 1, "published_at": -1 });

// 分析相关索引
db.analysis_tasks.createIndex({ "task_id": 1 }, { unique: true });
db.analysis_tasks.createIndex({ "user_id": 1, "created_at": -1 });
db.analysis_tasks.createIndex({ "status": 1, "created_at": -1 });

db.analysis_results.createIndex({ "analysis_id": 1 }, { unique: true });
db.analysis_results.createIndex({ "stock_code": 1, "analysis_date": 1 });
db.analysis_results.createIndex({ "created_at": -1 });

db.analysis_reports.createIndex({ "task_id": 1 });
db.analysis_reports.createIndex({ "created_at": -1 });

db.analysis_progress.createIndex({ "task_id": 1 }, { unique: true });
db.analysis_progress.createIndex({ "updated_at": 1 }, { expireAfterSeconds: 3600 });

// 提示词模板相关索引
db.prompt_templates.createIndex({ "agent_type": 1, "template_name": 1 });
db.prompt_templates.createIndex({ "agent_type": 1, "is_default": 1 });
db.prompt_templates.createIndex({ "is_system": 1 });

db.prompt_template_versions.createIndex({ "template_id": 1, "version": 1 });

db.user_template_configs.createIndex({ "user_id": 1, "agent_type": 1 }, { unique: true });
db.user_template_configs.createIndex({ "template_id": 1 });

// 工具配置相关索引
db.agent_tools.createIndex({ "agent_type": 1, "is_active": 1 });
db.agent_tools.createIndex({ "tool_name": 1 });

db.agent_tool_configs.createIndex({ "user_id": 1, "agent_type": 1 }, { unique: true });

db.tool_configs.createIndex({ "tool_name": 1 }, { unique: true });
db.tool_configs.createIndex({ "category": 1 });
db.tool_configs.createIndex({ "enabled": 1 });

// 筛选和收藏索引
db.screening_results.createIndex({ "user_id": 1, "created_at": -1 });
db.favorites.createIndex({ "user_id": 1, "symbol": 1 }, { unique: true });
db.tags.createIndex({ "user_id": 1, "name": 1 }, { unique: true });

// 工作流配置索引
db.workflow_configs.createIndex({ "name": 1 }, { unique: true });
db.workflow_configs.createIndex({ "metadata.created_at": -1 });

// 系统配置索引
db.system_config.createIndex({ "key": 1 }, { unique: true });
db.system_configs.createIndex({ "version": 1 });
db.system_configs.createIndex({ "is_active": 1 });

db.operation_logs.createIndex({ "user_id": 1 });
db.operation_logs.createIndex({ "created_at": -1 });

db.system_logs.createIndex({ "level": 1, "timestamp": -1 });
db.system_logs.createIndex({ "timestamp": -1 }, { expireAfterSeconds: 604800 });

// 多市场统一字典索引
db.market_metadata.createIndex({ "market_type": 1 });
db.industry_mapping.createIndex({ "source_industry": 1, "source_type": 1 });
db.symbol_registry.createIndex({ "symbol": 1, "market": 1 }, { unique: true });

// 社交媒体相关索引
db.social_media_posts.createIndex({ "platform": 1, "verified": 1, "created_at": -1 });
db.social_media_posts.createIndex({ "hashtags": 1 });
db.social_media_posts.createIndex({ "keywords": 1 });
db.social_media_posts.createIndex({ "topics": 1 });

// 数据源配置索引
db.data_source_configs.createIndex({ "source_name": 1 }, { unique: true });
db.data_source_configs.createIndex({ "source_type": 1 });
db.data_source_configs.createIndex({ "status": 1 });

db.data_sync_logs.createIndex({ "source_name": 1, "created_at": -1 });
db.data_sync_logs.createIndex({ "status": 1 });

// 模型目录索引
db.model_catalog.createIndex({ "provider": 1 });
db.model_catalog.createIndex({ "model_name": 1, "provider": 1 }, { unique: true });

// 系统状态索引
db.system_status.createIndex({ "component": 1 });
db.system_status.createIndex({ "created_at": -1 });

// 系统通知索引
db.notifications.createIndex({ "user_id": 1 });
db.notifications.createIndex({ "is_read": 1 });
db.notifications.createIndex({ "created_at": -1 });

print('✅ 所有索引创建完成');

// ===== 插入初始数据 =====

print('\n开始插入初始数据...');

// 插入默认系统配置
db.system_config.insertMany([
  {
    key: 'system_version',
    value: 'v1.0.0-preview',
    description: '系统版本号',
    updated_at: new Date()
  },
  {
    key: 'max_concurrent_tasks',
    value: 3,
    description: '最大并发分析任务数',
    updated_at: new Date()
  },
  {
    key: 'default_research_depth',
    value: 2,
    description: '默认分析深度',
    updated_at: new Date()
  },
  {
    key: 'enable_realtime_pe_pb',
    value: true,
    description: '启用实时PE/PB计算',
    updated_at: new Date()
  }
]);

print('✅ 初始数据插入完成');

// ===== 验证 =====

print('\n验证数据库初始化...');

var collections = db.getCollectionNames();
print('✓ 集合数量: ' + collections.length);

var indexes = 0;
collections.forEach(function(collName) {
  indexes += db.getCollection(collName).getIndexes().length;
});
print('✓ 索引数量: ' + indexes);

var configCount = db.system_config.count();
print('✓ 系统配置数量: ' + configCount);

print('\n🎉 TradingAgents数据库初始化完成！');
print('📋 数据库: tradingagents');
print('🔧 集合数: ' + collections.length);
print('📊 索引数: ' + indexes);
print('🚀 系统已准备就绪，可以开始使用了');