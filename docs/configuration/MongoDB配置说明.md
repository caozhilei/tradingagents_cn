# MongoDB 配置说明

## 📋 概述

本文档详细说明 TradingAgents-CN 项目中 MongoDB 数据库的配置方法，特别是财务数据同步相关的配置。

## 🔧 配置项

### 必需配置项

| 配置项 | 环境变量名 | 默认值 | 说明 |
|--------|-----------|--------|------|
| 主机地址 | `MONGODB_HOST` | `localhost` | MongoDB服务器地址 |
| 端口号 | `MONGODB_PORT` | `27017` | MongoDB端口 |
| 数据库名称 | `MONGODB_DATABASE` | `tradingagents` | 数据库名称 |

### 可选配置项（如果MongoDB启用了认证）

| 配置项 | 环境变量名 | 默认值 | 说明 |
|--------|-----------|--------|------|
| 用户名 | `MONGODB_USERNAME` | `""`（空） | MongoDB用户名 |
| 密码 | `MONGODB_PASSWORD` | `""`（空） | MongoDB密码 |
| 认证源 | `MONGODB_AUTH_SOURCE` | `admin` | 认证数据库 |

## 📝 配置位置

### .env 文件

在项目根目录创建或编辑 `.env` 文件：

```bash
# MongoDB 数据库配置
MONGODB_HOST=localhost
MONGODB_PORT=27017
MONGODB_USERNAME=admin
MONGODB_PASSWORD=tradingagents123
MONGODB_DATABASE=tradingagents
MONGODB_AUTH_SOURCE=admin
```

## 🎯 不同环境的配置

### 1. 本地开发环境（无认证）

如果本地MongoDB没有启用认证：

```bash
MONGODB_HOST=localhost
MONGODB_PORT=27017
MONGODB_USERNAME=
MONGODB_PASSWORD=
MONGODB_DATABASE=tradingagents
MONGODB_AUTH_SOURCE=admin
```

### 2. Docker Compose环境（宿主机运行）

在宿主机上运行，连接Docker容器中的MongoDB：

```bash
MONGODB_HOST=localhost
MONGODB_PORT=27017
MONGODB_USERNAME=admin
MONGODB_PASSWORD=tradingagents123
MONGODB_DATABASE=tradingagents
MONGODB_AUTH_SOURCE=admin
```

### 3. Docker容器内运行

在Docker容器内运行，使用服务名连接：

```bash
MONGODB_HOST=mongodb
MONGODB_PORT=27017
MONGODB_USERNAME=admin
MONGODB_PASSWORD=tradingagents123
MONGODB_DATABASE=tradingagents
MONGODB_AUTH_SOURCE=admin
```

## 🔍 配置验证

### 方法1: 使用诊断脚本

```bash
py scripts/使用应用配置诊断财务数据.py
```

### 方法2: 检查应用启动日志

启动应用时查看日志输出：

```
📋 TradingAgents-CN Configuration Summary
MongoDB: localhost:27017/tradingagents
```

### 方法3: 测试连接

```python
from app.core.config import settings
from pymongo import MongoClient

# 智能检测host（Docker环境自动转换）
mongodb_host = settings.MONGODB_HOST
if mongodb_host == "mongodb":
    mongodb_host = "localhost"  # 宿主机环境

connect_kwargs = {
    "host": mongodb_host,
    "port": settings.MONGODB_PORT
}

if settings.MONGODB_USERNAME and settings.MONGODB_PASSWORD:
    connect_kwargs.update({
        "username": settings.MONGODB_USERNAME,
        "password": settings.MONGODB_PASSWORD,
        "authSource": settings.MONGODB_AUTH_SOURCE
    })

client = MongoClient(**connect_kwargs)
client.admin.command('ping')
print("✅ MongoDB连接成功")
```

## 📊 数据库结构

### 主要集合

| 集合名称 | 用途 | 说明 |
|---------|------|------|
| `stock_basic_info` | 股票基础信息 | 股票代码、名称、行业等 |
| `stock_financial_data` | 财务数据 | ROE、负债率、营业收入等 |
| `stock_daily_quotes` | 日K线数据 | 价格、成交量等 |
| `stock_news` | 新闻数据 | 股票相关新闻 |
| `system_configs` | 系统配置 | LLM配置、数据源配置等 |

### 财务数据集合结构

```javascript
{
  "code": "000001",           // 股票代码（6位）
  "symbol": "000001",         // 股票代码（兼容字段）
  "full_symbol": "000001.SZ", // 完整代码
  "market": "CN",             // 市场类型
  "report_period": "20251231", // 报告期（YYYYMMDD）
  "report_type": "quarterly",  // 报告类型（quarterly/annual）
  "data_source": "akshare",    // 数据源
  "revenue": 1234567890,       // 营业收入
  "net_income": 123456789,     // 净利润
  "total_assets": 12345678900, // 总资产
  "total_equity": 1234567890,  // 股东权益
  "roe": 12.5,                 // 净资产收益率
  "debt_to_assets": 45.6,      // 资产负债率
  "created_at": ISODate(...),  // 创建时间
  "updated_at": ISODate(...)   // 更新时间
}
```

## 🔄 财务数据同步配置

### 启用自动同步

在 `.env` 文件中配置：

```bash
# AKShare财务数据同步
AKSHARE_UNIFIED_ENABLED=true
AKSHARE_FINANCIAL_SYNC_ENABLED=true
AKSHARE_FINANCIAL_SYNC_CRON=0 4 * * 0  # 每周日凌晨4点

# Tushare财务数据同步（如果有Token）
TUSHARE_UNIFIED_ENABLED=true
TUSHARE_FINANCIAL_SYNC_ENABLED=true
TUSHARE_FINANCIAL_SYNC_CRON=0 4 * * 0
TUSHARE_TOKEN=your_tushare_token_here
```

### 手动同步

```bash
# 同步指定股票
py scripts/直接同步财务数据.py --symbols 000001 600000

# 批量同步
py scripts/批量同步财务数据.py --limit 100
```

## ⚠️ 常见问题

### 问题1: 连接失败

**症状**: `getaddrinfo failed` 或 `Connection refused`

**解决方案**:
1. 检查MongoDB是否运行: `docker ps | grep mongodb`
2. 检查端口是否正确: `netstat -an | findstr 27017`
3. 检查host配置（Docker环境使用 `mongodb`，宿主机使用 `localhost`）

### 问题2: 认证失败

**症状**: `Authentication failed` 或 `Unauthorized`

**解决方案**:
1. 检查用户名和密码是否正确
2. 检查 `MONGODB_AUTH_SOURCE` 是否设置为 `admin`
3. 验证MongoDB用户是否存在

### 问题3: 数据库不存在

**症状**: 连接成功但找不到数据

**解决方案**:
1. 确认数据库名称: `MONGODB_DATABASE=tradingagents`
2. 运行数据同步脚本初始化数据
3. 检查集合是否存在

## 📚 相关文档

- [环境变量配置指南](./环境变量配置指南.md)
- [配置矩阵](./CONFIG_MATRIX.md)
- [基本面数据诊断](../../故障排除/基本面数据诊断结果.md)
- [财务数据同步服务](../../app/worker/financial_data_sync_service.py)

---

**最后更新**: 2025-01-13

