# PowerShell脚本：构建并启动后端Docker镜像

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "🚀 构建并启动后端Docker镜像" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# 检测代理
$PROXY_HOST = "host.docker.internal"
$PROXY_PORT = "10809"
$PROXY_URL = "http://${PROXY_HOST}:${PROXY_PORT}"

Write-Host "📡 使用代理: $PROXY_URL" -ForegroundColor Yellow

# 构建后端镜像
Write-Host ""
Write-Host "📦 步骤1: 构建后端Docker镜像..." -ForegroundColor Cyan

docker build `
  -f Dockerfile.backend `
  --build-arg HTTP_PROXY=$PROXY_URL `
  --build-arg HTTPS_PROXY=$PROXY_URL `
  --build-arg NO_PROXY="localhost,127.0.0.1,mongodb,redis" `
  -t tradingagents-backend:v1.0.0-preview `
  .

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ 镜像构建成功" -ForegroundColor Green
} else {
    Write-Host "❌ 镜像构建失败" -ForegroundColor Red
    exit 1
}

# 检查docker-compose是否可用
$COMPOSE_CMD = "docker-compose"
if (-not (Get-Command docker-compose -ErrorAction SilentlyContinue)) {
    if (Get-Command docker -ErrorAction SilentlyContinue) {
        $result = docker compose version 2>&1
        if ($LASTEXITCODE -eq 0) {
            $COMPOSE_CMD = "docker compose"
        }
    }
}

if (-not $COMPOSE_CMD) {
    Write-Host "❌ 未找到docker-compose命令" -ForegroundColor Red
    exit 1
}

# 启动后端服务
Write-Host ""
Write-Host "🚀 步骤2: 启动后端服务..." -ForegroundColor Cyan

if ($COMPOSE_CMD -eq "docker-compose") {
    docker-compose up -d backend
} else {
    docker compose up -d backend
}

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ 后端服务启动成功" -ForegroundColor Green
    Write-Host ""
    Write-Host "📊 服务状态:" -ForegroundColor Cyan
    if ($COMPOSE_CMD -eq "docker-compose") {
        docker-compose ps backend
    } else {
        docker compose ps backend
    }
    Write-Host ""
    Write-Host "📋 查看日志:" -ForegroundColor Cyan
    Write-Host "   $COMPOSE_CMD logs -f backend"
    Write-Host ""
    Write-Host "🌐 访问地址:" -ForegroundColor Cyan
    Write-Host "   http://localhost:8000"
    Write-Host "   http://localhost:8000/api/docs"
} else {
    Write-Host "❌ 后端服务启动失败" -ForegroundColor Red
    exit 1
}

