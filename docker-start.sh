#!/bin/bash
# TradingAgents-CN Docker 快速启动脚本
# 适用于 Linux/macOS 用户

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}=========================================="
echo "TradingAgents-CN Docker 部署脚本"
echo -e "==========================================${NC}"

# 检查 Docker 是否运行
echo -e "\n${YELLOW}检查 Docker 环境...${NC}"
if ! docker ps > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker 未运行，请先启动 Docker${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker 运行正常${NC}"

# 检查 .env 文件
echo -e "\n${YELLOW}检查环境变量配置...${NC}"
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  未找到 .env 文件${NC}"
    echo -e "${YELLOW}正在创建 .env 文件模板...${NC}"
    
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
    
    echo -e "${GREEN}✓ .env 文件已创建${NC}"
    echo -e "${YELLOW}⚠️  请编辑 .env 文件，配置你的 API 密钥后再运行此脚本${NC}"
    echo -e "\n${CYAN}按 Enter 键打开 .env 文件进行编辑...${NC}"
    read
    ${EDITOR:-nano} .env
    exit 0
else
    echo -e "${GREEN}✓ .env 文件存在${NC}"
fi

# 创建必需的目录
echo -e "\n${YELLOW}创建必需的目录...${NC}"
directories=("logs" "data/cache" "data/exports" "data/reports" "config")
for dir in "${directories[@]}"; do
    if [ ! -d "$dir" ]; then
        mkdir -p "$dir"
        echo -e "${GREEN}✓ 创建目录: $dir${NC}"
    fi
done

# 停止现有容器
echo -e "\n${YELLOW}停止现有容器...${NC}"
docker-compose down 2>/dev/null || true
echo -e "${GREEN}✓ 容器已停止${NC}"

# 构建并启动服务
echo -e "\n${YELLOW}构建并启动 Docker 服务...${NC}"
echo -e "${CYAN}这可能需要几分钟时间，请耐心等待...${NC}"

docker-compose up -d --build

if [ $? -eq 0 ]; then
    echo -e "\n${GREEN}✓ Docker 服务启动成功！${NC}"
    echo -e "\n${CYAN}=========================================="
    echo "服务访问地址："
    echo -e "==========================================${NC}"
    echo "前端界面: http://localhost:3000"
    echo "后端 API:  http://localhost:8000"
    echo "API 文档:  http://localhost:8000/docs"
    echo -e "\n${CYAN}默认账号：${NC}"
    echo "用户名: admin"
    echo "密码:   admin123"
    echo -e "\n${YELLOW}查看日志: docker-compose logs -f${NC}"
    echo -e "${YELLOW}停止服务: docker-compose down${NC}"
else
    echo -e "\n${RED}❌ Docker 服务启动失败${NC}"
    echo -e "${YELLOW}请检查错误信息并参考 DOCKER_DEPLOYMENT.md 进行故障排除${NC}"
    exit 1
fi

