# 重新构建前端Docker镜像
# 用于应用前端代码修改

Write-Host "开始重新构建前端Docker镜像..." -ForegroundColor Cyan

# 设置代理（如果需要）
$env:HTTP_PROXY = "http://host.docker.internal:10809"
$env:HTTPS_PROXY = "http://host.docker.internal:10809"
$env:NO_PROXY = "localhost,127.0.0.1"

# 停止前端容器
Write-Host "停止前端容器..." -ForegroundColor Yellow
docker-compose stop frontend

# 重新构建前端镜像（使用缓存加速）
Write-Host "重新构建前端镜像（使用缓存）..." -ForegroundColor Cyan
docker-compose build frontend

if ($LASTEXITCODE -eq 0) {
    Write-Host "前端镜像构建成功！" -ForegroundColor Green
    
    # 启动前端容器
    Write-Host "启动前端容器..." -ForegroundColor Cyan
    docker-compose up -d frontend
    
    Write-Host "前端服务已重启，请刷新浏览器查看更新" -ForegroundColor Green
} else {
    Write-Host "前端镜像构建失败，请检查错误信息" -ForegroundColor Red
    Write-Host "提示：如果遇到网络问题，可以尝试：" -ForegroundColor Yellow
    Write-Host "  1. 检查代理设置" -ForegroundColor Yellow
    Write-Host "  2. 使用国内Docker镜像源" -ForegroundColor Yellow
    Write-Host "  3. 手动拉取基础镜像" -ForegroundColor Yellow
}
