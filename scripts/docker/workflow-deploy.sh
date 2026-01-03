#!/bin/bash
# 工作流模块 Docker 部署脚本
# 用于快速部署包含工作流模块的系统

set -e

echo "🚀 开始部署工作流模块..."

# 检查 Docker 和 Docker Compose
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装，请先安装 Docker"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose 未安装，请先安装 Docker Compose"
    exit 1
fi

# 检查必要文件
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ 未找到 docker-compose.yml 文件"
    exit 1
fi

if [ ! -f "frontend/package.json" ]; then
    echo "❌ 未找到 frontend/package.json 文件"
    exit 1
fi

# 检查 Vue Flow 依赖
if ! grep -q "@vue-flow/core" frontend/package.json; then
    echo "⚠️  警告：未检测到 Vue Flow 依赖，工作流模块可能无法正常工作"
fi

echo "✅ 环境检查通过"

# 询问是否重新构建
read -p "是否重新构建镜像？(y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🔨 开始构建镜像..."
    docker-compose build --no-cache
else
    echo "⏭️  跳过构建，使用现有镜像"
fi

# 启动服务
echo "🚀 启动服务..."
docker-compose up -d

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 10

# 检查服务状态
echo "📊 检查服务状态..."
docker-compose ps

# 健康检查
echo "🏥 执行健康检查..."

# 检查后端
if curl -f http://localhost:8000/api/health > /dev/null 2>&1; then
    echo "✅ 后端服务健康"
else
    echo "❌ 后端服务健康检查失败"
    echo "查看日志: docker-compose logs backend"
fi

# 检查前端
if curl -f http://localhost:3000 > /dev/null 2>&1; then
    echo "✅ 前端服务健康"
else
    echo "❌ 前端服务健康检查失败"
    echo "查看日志: docker-compose logs frontend"
fi

# 检查 MongoDB
if docker exec tradingagents-mongodb mongosh --quiet --eval "db.adminCommand('ping')" > /dev/null 2>&1; then
    echo "✅ MongoDB 服务健康"
    
    # 检查工作流配置索引
    echo "🔍 检查工作流配置索引..."
    INDEXES=$(docker exec tradingagents-mongodb mongosh -u admin -p tradingagents123 --authenticationDatabase admin --quiet --eval "db.getSiblingDB('tradingagents').workflow_configs.getIndexes().length" 2>/dev/null || echo "0")
    if [ "$INDEXES" -gt "1" ]; then
        echo "✅ 工作流配置索引已创建"
    else
        echo "⚠️  工作流配置索引可能未创建，将在后端启动时自动创建"
    fi
else
    echo "❌ MongoDB 服务健康检查失败"
fi

echo ""
echo "🎉 部署完成！"
echo ""
echo "访问地址："
echo "  前端: http://localhost:3000"
echo "  后端 API: http://localhost:8000"
echo "  工作流编辑器: http://localhost:3000/settings/workflow"
echo ""
echo "查看日志:"
echo "  docker-compose logs -f"
echo ""
echo "停止服务:"
echo "  docker-compose down"
echo ""

