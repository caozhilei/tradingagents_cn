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

// 创建索引集合（如果不存在）
// 优化查询性能

// 任务集合索引
if (!db.analysis_tasks.exists()) {
    db.createCollection("analysis_tasks");
    print("✅ [MongoDB初始化] 集合 'analysis_tasks' 创建成功");
}

// 创建任务索引以优化查询
db.analysis_tasks.createIndex({ "task_id": 1 }, { unique: true });
db.analysis_tasks.createIndex({ "user_id": 1 });
db.analysis_tasks.createIndex({ "status": 1 });
db.analysis_tasks.createIndex({ "created_at": -1 });
db.analysis_tasks.createIndex({ "analysis_date": 1 });
print("✅ [MongoDB初始化] 集合 'analysis_tasks' 索引创建成功");

// 分析结果集合索引
if (!db.analysis_results.exists()) {
    db.createCollection("analysis_results");
    print("✅ [MongoDB初始化] 集合 'analysis_results' 创建成功");
}

db.analysis_results.createIndex({ "analysis_id": 1 }, { unique: true });
db.analysis_results.createIndex({ "stock_code": 1 });
db.analysis_results.createIndex({ "analysis_date": 1 });
db.analysis_results.createIndex({ "created_at": -1 });
print("✅ [MongoDB初始化] 集合 'analysis_results' 索引创建成功");

// 股票数据集合索引
if (!db.stock_daily_quotes.exists()) {
    db.createCollection("stock_daily_quotes");
    print("✅ [MongoDB初始化] 集合 'stock_daily_quotes' 创建成功");
}

db.stock_daily_quotes.createIndex({ "stock_code": 1, "trade_date": -1 });
db.stock_daily_quotes.createIndex({ "trade_date": -1 });
db.stock_daily_quotes.createIndex({ "created_at": -1 });
print("✅ [MongoDB初始化] 集合 'stock_daily_quotes' 索引创建成功");

// 财务数据集合索引
if (!db.stock_financial_data.exists()) {
    db.createCollection("stock_financial_data");
    print("✅ [MongoDB初始化] 集合 'stock_financial_data' 创建成功");
}

db.stock_financial_data.createIndex({ "stock_code": 1, "report_date": -1 });
db.stock_financial_data.createIndex({ "report_type": 1 });
db.stock_financial_data.createIndex({ "created_at": -1 });
print("✅ [MongoDB初始化] 集合 'stock_financial_data' 索引创建成功");

// 日志集合索引
if (!db.operation_logs.exists()) {
    db.createCollection("operation_logs");
    print("✅ [MongoDB初始化] 集合 'operation_logs' 创建成功");
}

db.operation_logs.createIndex({ "user_id": 1 });
db.operation_logs.createIndex({ "action": 1 });
db.operation_logs.createIndex({ "created_at": -1 });
print("✅ [MongoDB初始化] 集合 'operation_logs' 索引创建成功");

// 完成初始化
print("🎉 [MongoDB初始化] 数据库初始化完成");
print("📋 数据库信息:");
print("   数据库名: tradingagents");
print("   用户名: tradingagents");
print("   密码: tradingagents123");
print("   角色: readWrite");
print("🔧 索引已创建，优化查询性能");
