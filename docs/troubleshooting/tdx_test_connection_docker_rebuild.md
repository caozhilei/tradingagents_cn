# TDX数据源测试连接 - Docker环境重建指南

## 问题说明

在Docker环境中，前端代码修改需要重新构建镜像才能生效。如果遇到"连接失败"的问题，可能是前端代码还没有重新构建。

## 验证后端是否正常

### 1. 检查后端日志

```bash
docker-compose logs --tail=50 backend | Select-String -Pattern "TDX|tdx|测试|test"
```

如果看到：
- ✅ `状态码: 200`
- ✅ `成功连接到通达信数据源`

说明后端测试是成功的。

### 2. 直接测试后端API

```bash
# 测试TDX数据源连接
curl -X POST http://localhost:8000/api/config/test \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "config_type": "datasource",
    "config_data": {
      "name": "TDX",
      "type": "tdx",
      "endpoint": null,
      "timeout": 30,
      "rate_limit": 100,
      "enabled": true,
      "priority": 10
    }
  }'
```

如果返回 `"success": true`，说明后端功能正常。

## 重新构建前端镜像

### 方法1：使用脚本（推荐）

```powershell
# 运行重建脚本
powershell -ExecutionPolicy Bypass -File scripts/rebuild_frontend.ps1
```

### 方法2：手动构建

```powershell
# 1. 停止前端容器
docker-compose stop frontend

# 2. 重新构建前端镜像
docker-compose build frontend

# 3. 启动前端容器
docker-compose up -d frontend
```

### 方法3：如果遇到网络问题

如果无法拉取Docker Hub镜像，可以：

1. **手动拉取基础镜像**（使用代理或镜像源）：
   ```bash
   docker pull node:22-alpine
   docker pull nginx:alpine
   ```

2. **使用国内镜像源**：
   - 配置Docker镜像加速器（阿里云、腾讯云等）
   - 或使用代理：`docker pull --platform linux/amd64 node:22-alpine`

3. **使用已有镜像**：
   ```bash
   # 检查是否已有镜像
   docker images | grep -E "node|nginx"
   
   # 如果有，可以直接构建
   docker-compose build frontend
   ```

## 验证修复

1. **刷新浏览器**（硬刷新：Ctrl+F5）
2. **打开配置页面**：`http://localhost:3000/settings/config`
3. **编辑TDX数据源**
4. **API端点字段留空**
5. **点击"测试连接"**
6. ✅ 应该显示："成功连接到通达信数据源"

## 当前状态

根据测试结果：

- ✅ **后端代码已更新**：TDX测试逻辑已添加
- ✅ **后端服务已重启**：新代码已生效
- ✅ **后端测试成功**：直接测试后端API返回成功
- ⏳ **前端代码已更新**：但需要重新构建镜像才能生效
- ⏳ **前端镜像待重建**：遇到网络问题时需要手动处理

## 临时解决方案

如果暂时无法重新构建前端镜像，可以：

1. **直接使用后端API测试**（如上所示）
2. **等待网络恢复后重新构建**
3. **使用本地开发环境**：在本地运行前端开发服务器

## 相关文档

- [TDX数据源配置指南](../guides/tdx_datasource_configuration.md)
- [TDX测试功能修复](../changes/tdx_datasource_test_fix.md)
- [TDX端点留空修复](../changes/tdx_endpoint_empty_fix.md)

