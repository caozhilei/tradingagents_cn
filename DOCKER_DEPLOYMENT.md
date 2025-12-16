# 🐳 TradingAgents-CN Docker 本地部署指南

## 📋 概述

本指南将帮助您在本地 Docker 环境中快速部署 TradingAgents-CN v1.0.0-preview 项目。

## 🎯 前置要求

### 必需软件

- **Docker Desktop** 20.10+ 或 **Docker Engine** 20.10+
- **Docker Compose** 2.0+
- **至少 4GB 内存** 和 **20GB 磁盘空间**

### 检查 Docker 环境

```bash
# 检查 Docker 版本
docker --version
# 应该显示: Docker version 20.10.0 或更高

# 检查 Docker Compose 版本
docker-compose --version
# 应该显示: Docker Compose version 2.0.0 或更高

# 检查 Docker 是否运行
docker ps
# 应该显示容器列表（可能为空）
```

## 🚀 快速部署步骤

### 步骤 1: 准备环境变量文件

创建 `.env` 文件（如果不存在）：

```bash
# Windows PowerShell
if (-not (Test-Path ".env")) {
    @"
# ===== 应用基础配置 =====
DEBUG=true
HOST=0.0.0.0
PORT=8000

# ===== 数据库配置 =====
MONGODB_HOST=mongodb
MONGODB_PORT=27017
MONGODB_USERNAME=admin
MONGODB_PASSWORD=tradingagents123
MONGODB_DATABASE=tradingagents
MONGODB_AUTH_SOURCE=admin

REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=tradingagents123
REDIS_DB=0

# ===== 安全配置 =====
JWT_SECRET=change-me-in-production-use-random-string
CSRF_SECRET=change-me-csrf-secret-in-production

# ===== LLM API 密钥配置（至少配置一个）=====
DEEPSEEK_API_KEY=your_deepseek_api_key_here
DEEPSEEK_ENABLED=true

# ===== 数据源配置 =====
TUSHARE_TOKEN=your_tushare_token_here
TUSHARE_ENABLED=true

# ===== Docker 环境配置 =====
DOCKER_CONTAINER=true
"@ | Out-File -FilePath ".env" -Encoding utf8
}
```

```bash
# Linux/macOS
if [ ! -f ".env" ]; then
cat > .env << 'EOF'
# ===== 应用基础配置 =====
DEBUG=true
HOST=0.0.0.0
PORT=8000

# ===== 数据库配置 =====
MONGODB_HOST=mongodb
MONGODB_PORT=27017
MONGODB_USERNAME=admin
MONGODB_PASSWORD=tradingagents123
MONGODB_DATABASE=tradingagents
MONGODB_AUTH_SOURCE=admin

REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=tradingagents123
REDIS_DB=0

# ===== 安全配置 =====
JWT_SECRET=change-me-in-production-use-random-string
CSRF_SECRET=change-me-csrf-secret-in-production

# ===== LLM API 密钥配置（至少配置一个）=====
DEEPSEEK_API_KEY=your_deepseek_api_key_here
DEEPSEEK_ENABLED=true

# ===== 数据源配置 =====
TUSHARE_TOKEN=your_tushare_token_here
TUSHARE_ENABLED=true

# ===== Docker 环境配置 =====
DOCKER_CONTAINER=true
EOF
fi
```

### 步骤 2: 编辑 .env 文件

使用文本编辑器打开 `.env` 文件，配置以下必需项：

1. **LLM API 密钥**（至少配置一个）：
   - `DEEPSEEK_API_KEY`: DeepSeek API 密钥（推荐）
   - 或 `DASHSCOPE_API_KEY`: 阿里百炼 API 密钥
   - 或 `OPENAI_API_KEY`: OpenAI API 密钥

2. **数据源配置**（推荐）：
   - `TUSHARE_TOKEN`: Tushare Token（用于 A 股数据）

3. **安全配置**（生产环境必须修改）：
   - `JWT_SECRET`: 随机字符串，用于 JWT 令牌签名
   - `CSRF_SECRET`: 随机字符串，用于 CSRF 保护

### 步骤 3: 创建必需的目录

```bash
# Windows PowerShell
New-Item -ItemType Directory -Force -Path logs, data\cache, data\exports, data\reports, config

# Linux/macOS
mkdir -p logs data/cache data/exports data/reports config
```

### 步骤 4: 启动 Docker 服务

```bash
# 构建并启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

### 步骤 5: 等待服务启动

等待 1-2 分钟，确保所有服务完全启动。可以通过以下命令检查：

```bash
# 检查后端健康状态
curl http://localhost:8000/api/health

# 检查前端
curl http://localhost:3000

# 查看所有服务日志
docker-compose logs
```

## 🌐 访问应用

### 主要入口

- **前端界面**: http://localhost:3000
- **后端 API**: http://localhost:8000
- **API 文档**: http://localhost:8000/docs
- **ReDoc 文档**: http://localhost:8000/redoc

### 默认账号

- **用户名**: `admin`
- **密码**: `admin123`

⚠️ **重要**: 首次登录后请立即修改密码！

### 管理界面（可选）

启动管理服务：

```bash
docker-compose --profile management up -d
```

然后访问：

- **MongoDB 管理**: http://localhost:8082
  - 用户名: `admin`
  - 密码: `tradingagents123`

- **Redis 管理**: http://localhost:8081

## 🔧 常用命令

### 服务管理

```bash
# 启动所有服务
docker-compose up -d

# 停止所有服务
docker-compose down

# 重启所有服务
docker-compose restart

# 重启单个服务
docker-compose restart backend

# 查看服务状态
docker-compose ps

# 查看服务日志
docker-compose logs -f

# 查看单个服务日志
docker-compose logs -f backend
```

### 数据管理

```bash
# 备份 MongoDB 数据
docker exec tradingagents-mongodb mongodump --out /data/backup

# 清理 Redis 缓存
docker exec tradingagents-redis redis-cli -a tradingagents123 FLUSHALL

# 进入 MongoDB 容器
docker exec -it tradingagents-mongodb mongo -u admin -p tradingagents123

# 进入后端容器
docker exec -it tradingagents-backend bash
```

### 容器管理

```bash
# 查看容器资源使用
docker stats

# 清理未使用的容器和镜像
docker system prune -a

# 重新构建镜像
docker-compose build --no-cache

# 拉取最新镜像
docker-compose pull
```

## 🐛 故障排除

### 问题 1: 端口被占用

**错误**: `Bind for 0.0.0.0:8000 failed: port is already allocated`

**解决方案**:

1. 查找占用端口的进程：
   ```bash
   # Windows
   netstat -ano | findstr :8000
   
   # Linux/macOS
   lsof -i :8000
   ```

2. 修改端口（编辑 `docker-compose.yml`）：
   ```yaml
   ports:
     - "8001:8000"  # 改为其他端口
   ```

### 问题 2: MongoDB 连接失败

**错误**: `MongoServerError: Authentication failed`

**解决方案**:

```bash
# 1. 停止所有服务
docker-compose down -v

# 2. 删除数据卷
docker volume rm tradingagents_mongodb_data

# 3. 重新启动
docker-compose up -d
```

### 问题 3: 前端无法连接后端

**错误**: 前端显示"网络错误"

**解决方案**:

1. 检查后端是否运行：
   ```bash
   curl http://localhost:8000/api/health
   ```

2. 检查 CORS 配置（编辑 `.env` 文件）：
   ```bash
   CORS_ORIGINS=http://localhost:3000,http://localhost:8080
   ```

3. 重启后端：
   ```bash
   docker-compose restart backend
   ```

### 问题 4: 内存不足

**错误**: 容器频繁重启或 OOM

**解决方案**:

1. 检查 Docker 资源限制：
   - Docker Desktop -> Settings -> Resources
   - 建议: 4GB+ 内存

2. 减少并发任务数（编辑 `.env` 文件）：
   ```bash
   MAX_CONCURRENT_ANALYSIS_TASKS=1
   ```

3. 清理缓存：
   ```bash
   docker exec tradingagents-redis redis-cli -a tradingagents123 FLUSHALL
   ```

### 问题 5: 构建失败

**错误**: `ERROR [internal] load metadata for docker.io/library/python:3.10`

**解决方案**:

1. 配置 Docker 镜像加速（编辑 Docker 配置文件）：
   ```json
   {
     "registry-mirrors": [
       "https://docker.mirrors.ustc.edu.cn",
       "https://hub-mirror.c.163.com"
     ]
   }
   ```

2. 重启 Docker 服务

3. 重新构建：
   ```bash
   docker-compose build --no-cache
   ```

## 🔐 安全建议

### 生产环境配置

1. **修改默认密码**:
   ```bash
   # MongoDB 密码
   MONGODB_PASSWORD=your-strong-password-here
   
   # Redis 密码
   REDIS_PASSWORD=your-strong-password-here
   
   # JWT 密钥
   JWT_SECRET=your-super-secret-jwt-key-change-in-production
   ```

2. **限制端口访问**:
   ```yaml
   # 只在本地访问
   ports:
     - "127.0.0.1:27017:27017"  # MongoDB
     - "127.0.0.1:6379:6379"    # Redis
   ```

3. **启用 HTTPS**: 使用 Nginx 反向代理并配置 SSL 证书

4. **定期备份**:
   ```bash
   # 创建备份脚本
   DATE=$(date +%Y%m%d_%H%M%S)
   docker exec tradingagents-mongodb mongodump --out /data/backup_$DATE
   ```

## 📊 服务说明

### 核心服务

| 服务 | 端口 | 说明 |
|-----|------|------|
| **frontend** | 3000 | Vue 3 前端界面 |
| **backend** | 8000 | FastAPI 后端 API |
| **mongodb** | 27017 | MongoDB 数据库 |
| **redis** | 6379 | Redis 缓存 |

### 管理服务（可选）

| 服务 | 端口 | 说明 |
|-----|------|------|
| **mongo-express** | 8082 | MongoDB 管理界面 |
| **redis-commander** | 8081 | Redis 管理界面 |

## 📚 更多资源

- [完整部署文档](docs/deployment/docker/DOCKER_DEPLOYMENT_v1.0.0.md)
- [API 文档](http://localhost:8000/docs)
- [故障排除指南](docs/troubleshooting/)
- [配置指南](docs/configuration/)

## 🤝 获取帮助

- **GitHub Issues**: https://github.com/hsliuping/TradingAgents-CN/issues
- **QQ群**: 1009816091
- **邮箱**: hsliup@163.com

---

**版本**: v1.0.0-preview  
**更新日期**: 2025-01-XX  
**维护者**: TradingAgents-CN Team

