# 配置 Docker 使用腾讯云镜像源

## Windows Docker Desktop 配置步骤

### 方法一：通过 Docker Desktop GUI 配置（推荐）

1. **打开 Docker Desktop**
   - 右键点击系统托盘中的 Docker 图标
   - 选择 "Settings"（设置）

2. **进入 Docker Engine 配置**
   - 在左侧菜单选择 "Docker Engine"
   - 右侧会显示 JSON 配置编辑器

3. **添加腾讯云镜像源配置**
   - 在 JSON 配置中找到 `"registry-mirrors"` 字段
   - 如果不存在，添加以下配置：
   ```json
   {
     "registry-mirrors": [
       "https://mirror.ccs.tencentyun.com"
     ]
   }
   ```
   - 如果已存在其他镜像源，可以添加腾讯云镜像源到列表中：
   ```json
   {
     "registry-mirrors": [
       "https://mirror.ccs.tencentyun.com",
       "https://docker.mirrors.ustc.edu.cn"
     ]
   }
   ```

4. **应用配置**
   - 点击 "Apply & Restart" 按钮
   - 等待 Docker 重启完成

5. **验证配置**
   ```powershell
   docker info | Select-String -Pattern "Registry Mirrors"
   ```
   应该能看到 `https://mirror.ccs.tencentyun.com/`

### 方法二：直接编辑配置文件

1. **找到 Docker Desktop 配置文件**
   - Windows 路径：`%USERPROFILE%\.docker\daemon.json`
   - 或者：`C:\Users\<用户名>\.docker\daemon.json`

2. **编辑配置文件**
   ```json
   {
     "registry-mirrors": [
       "https://mirror.ccs.tencentyun.com"
     ]
   }
   ```

3. **重启 Docker Desktop**
   - 右键点击 Docker 图标
   - 选择 "Restart Docker Desktop"

## 验证配置

运行以下命令验证镜像源是否配置成功：

```powershell
docker info | Select-String -Pattern "Registry Mirrors"
```

应该看到类似输出：
```
Registry Mirrors:
 https://mirror.ccs.tencentyun.com/
```

## 其他可用的国内镜像源

如果腾讯云镜像源不可用，可以使用以下镜像源：

```json
{
  "registry-mirrors": [
    "https://mirror.ccs.tencentyun.com",
    "https://docker.mirrors.ustc.edu.cn",
    "https://hub-mirror.c.163.com",
    "https://registry.docker-cn.com"
  ]
}
```

## 注意事项

1. **腾讯云镜像源限制**：`https://mirror.ccs.tencentyun.com` 主要面向腾讯云内网用户，如果不在腾讯云内网环境，建议使用其他镜像源。

2. **镜像源优先级**：Docker 会按顺序尝试镜像源，如果第一个失败会自动尝试下一个。

3. **配置后需要重启**：修改镜像源配置后，必须重启 Docker Desktop 才能生效。

## 配置完成后构建前端

配置完成后，运行以下命令构建前端：

```powershell
docker-compose build frontend
```

或者构建所有服务：

```powershell
docker-compose build
```

