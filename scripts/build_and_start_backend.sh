#!/bin/bash
# 构建并启动后端Docker镜像

set -e

echo "=========================================="
echo "🚀 构建并启动后端Docker镜像"
echo "=========================================="

# 检测代理
PROXY_HOST="host.docker.internal"
PROXY_PORT="10809"
PROXY_URL="http://${PROXY_HOST}:${PROXY_PORT}"

echo "📡 使用代理: ${PROXY_URL}"

# 构建后端镜像
echo ""
echo "📦 步骤1: 构建后端Docker镜像..."
docker build \
  -f Dockerfile.backend \
  --build-arg HTTP_PROXY=${PROXY_URL} \
  --build-arg HTTPS_PROXY=${PROXY_URL} \
  --build-arg NO_PROXY="localhost,127.0.0.1,mongodb,redis" \
  -t tradingagents-backend:v1.0.0-preview \
  .

if [ $? -eq 0 ]; then
    echo "✅ 镜像构建成功"
else
    echo "❌ 镜像构建失败"
    exit 1
fi

# 检查docker-compose是否可用
if command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
elif command -v docker &> /dev/null && docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
else
    echo "❌ 未找到docker-compose命令"
    exit 1
fi

# 启动后端服务
echo ""
echo "🚀 步骤2: 启动后端服务..."
$COMPOSE_CMD up -d backend

if [ $? -eq 0 ]; then
    echo "✅ 后端服务启动成功"
    echo ""
    echo "📊 服务状态:"
    $COMPOSE_CMD ps backend
    echo ""
    echo "📋 查看日志:"
    echo "   $COMPOSE_CMD logs -f backend"
    echo ""
    echo "🌐 访问地址:"
    echo "   http://localhost:8000"
    echo "   http://localhost:8000/api/docs"
else
    echo "❌ 后端服务启动失败"
    exit 1
fi

