# 工作流模块 Docker 部署脚本 (PowerShell)
# 用于快速部署包含工作流模块的系统

Write-Host "🚀 开始部署工作流模块..." -ForegroundColor Cyan

# 检查 Docker 和 Docker Compose
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Docker 未安装，请先安装 Docker" -ForegroundColor Red
    exit 1
}

if (-not (Get-Command docker-compose -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Docker Compose 未安装，请先安装 Docker Compose" -ForegroundColor Red
    exit 1
}

# 检查必要文件
if (-not (Test-Path "docker-compose.yml")) {
    Write-Host "❌ 未找到 docker-compose.yml 文件" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path "frontend/package.json")) {
    Write-Host "❌ 未找到 frontend/package.json 文件" -ForegroundColor Red
    exit 1
}

# 检查 Vue Flow 依赖
$packageJson = Get-Content "frontend/package.json" -Raw
if ($packageJson -notmatch "@vue-flow/core") {
    Write-Host "⚠️  警告：未检测到 Vue Flow 依赖，工作流模块可能无法正常工作" -ForegroundColor Yellow
}

Write-Host "✅ 环境检查通过" -ForegroundColor Green

# 询问是否重新构建
$rebuild = Read-Host "是否重新构建镜像？(y/n)"
if ($rebuild -eq "y" -or $rebuild -eq "Y") {
    Write-Host "🔨 开始构建镜像..." -ForegroundColor Cyan
    docker-compose build --no-cache
} else {
    Write-Host "⏭️  跳过构建，使用现有镜像" -ForegroundColor Yellow
}

# 启动服务
Write-Host "🚀 启动服务..." -ForegroundColor Cyan
docker-compose up -d

# 等待服务启动
Write-Host "⏳ 等待服务启动..." -ForegroundColor Cyan
Start-Sleep -Seconds 10

# 检查服务状态
Write-Host "📊 检查服务状态..." -ForegroundColor Cyan
docker-compose ps

# 健康检查
Write-Host "🏥 执行健康检查..." -ForegroundColor Cyan

# 检查后端
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/api/health" -TimeoutSec 5 -ErrorAction Stop
    Write-Host "✅ 后端服务健康" -ForegroundColor Green
} catch {
    Write-Host "❌ 后端服务健康检查失败" -ForegroundColor Red
    Write-Host "查看日志: docker-compose logs backend" -ForegroundColor Yellow
}

# 检查前端
try {
    $response = Invoke-WebRequest -Uri "http://localhost:3000" -TimeoutSec 5 -ErrorAction Stop
    Write-Host "✅ 前端服务健康" -ForegroundColor Green
} catch {
    Write-Host "❌ 前端服务健康检查失败" -ForegroundColor Red
    Write-Host "查看日志: docker-compose logs frontend" -ForegroundColor Yellow
}

# 检查 MongoDB
try {
    $mongoCheck = docker exec tradingagents-mongodb mongosh --quiet --eval "db.adminCommand('ping')" 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ MongoDB 服务健康" -ForegroundColor Green
        
        # 检查工作流配置索引
        Write-Host "🔍 检查工作流配置索引..." -ForegroundColor Cyan
        $indexCount = docker exec tradingagents-mongodb mongosh -u admin -p tradingagents123 --authenticationDatabase admin --quiet --eval "db.getSiblingDB('tradingagents').workflow_configs.getIndexes().length" 2>$null
        if ($indexCount -and [int]$indexCount -gt 1) {
            Write-Host "✅ 工作流配置索引已创建" -ForegroundColor Green
        } else {
            Write-Host "⚠️  工作流配置索引可能未创建，将在后端启动时自动创建" -ForegroundColor Yellow
        }
    } else {
        Write-Host "❌ MongoDB 服务健康检查失败" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ MongoDB 服务健康检查失败" -ForegroundColor Red
}

Write-Host ""
Write-Host "🎉 部署完成！" -ForegroundColor Green
Write-Host ""
Write-Host "访问地址："
Write-Host "  前端: http://localhost:3000"
Write-Host "  后端 API: http://localhost:8000"
Write-Host "  工作流编辑器: http://localhost:3000/settings/workflow"
Write-Host ""
Write-Host "查看日志:"
Write-Host "  docker-compose logs -f"
Write-Host ""
Write-Host "停止服务:"
Write-Host "  docker-compose down"
Write-Host ""
