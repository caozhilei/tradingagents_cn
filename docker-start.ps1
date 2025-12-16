# TradingAgents-CN Docker 快速启动脚本 (PowerShell)
# 适用于 Windows 用户

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "TradingAgents-CN Docker 部署脚本" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# 检查 Docker 是否运行
Write-Host "`n检查 Docker 环境..." -ForegroundColor Yellow
try {
    docker ps | Out-Null
    Write-Host "✓ Docker 运行正常" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker 未运行，请先启动 Docker Desktop" -ForegroundColor Red
    exit 1
}

# 检查 .env 文件
Write-Host "`n检查环境变量配置..." -ForegroundColor Yellow
if (-not (Test-Path ".env")) {
    Write-Host "⚠️  未找到 .env 文件" -ForegroundColor Yellow
    Write-Host "正在创建 .env 文件模板..." -ForegroundColor Yellow
    
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
    
    Write-Host "✓ .env 文件已创建" -ForegroundColor Green
    Write-Host "⚠️  请编辑 .env 文件，配置你的 API 密钥后再运行此脚本" -ForegroundColor Yellow
    Write-Host "`n按任意键打开 .env 文件进行编辑..." -ForegroundColor Cyan
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    notepad .env
    exit 0
} else {
    Write-Host "✓ .env 文件存在" -ForegroundColor Green
}

# 创建必需的目录
Write-Host "`n创建必需的目录..." -ForegroundColor Yellow
$directories = @("logs", "data\cache", "data\exports", "data\reports", "config")
foreach ($dir in $directories) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Force -Path $dir | Out-Null
        Write-Host "✓ 创建目录: $dir" -ForegroundColor Green
    }
}

# 停止现有容器
Write-Host "`n停止现有容器..." -ForegroundColor Yellow
docker-compose down 2>$null
Write-Host "✓ 容器已停止" -ForegroundColor Green

# 构建并启动服务
Write-Host "`n构建并启动 Docker 服务..." -ForegroundColor Yellow
Write-Host "这可能需要几分钟时间，请耐心等待..." -ForegroundColor Cyan

docker-compose up -d --build

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✓ Docker 服务启动成功！" -ForegroundColor Green
    Write-Host "`n==========================================" -ForegroundColor Cyan
    Write-Host "服务访问地址：" -ForegroundColor Cyan
    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host "前端界面: http://localhost:3000" -ForegroundColor White
    Write-Host "后端 API:  http://localhost:8000" -ForegroundColor White
    Write-Host "API 文档:  http://localhost:8000/docs" -ForegroundColor White
    Write-Host "`n默认账号：" -ForegroundColor Cyan
    Write-Host "用户名: admin" -ForegroundColor White
    Write-Host "密码:   admin123" -ForegroundColor White
    Write-Host "`n查看日志: docker-compose logs -f" -ForegroundColor Yellow
    Write-Host "停止服务: docker-compose down" -ForegroundColor Yellow
} else {
    Write-Host "`n❌ Docker 服务启动失败" -ForegroundColor Red
    Write-Host "请检查错误信息并参考 DOCKER_DEPLOYMENT.md 进行故障排除" -ForegroundColor Yellow
    exit 1
}

