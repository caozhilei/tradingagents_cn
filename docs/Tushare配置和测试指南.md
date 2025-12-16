# Tushare配置和测试指南

## 📋 当前状态

根据测试结果：
- ✅ Tushare库已安装
- ⚠️  Token配置：`.env`文件中是占位符 `your_tushare_token_here`
- ⚠️  数据库配置：如果已在系统后台配置，需要系统运行才能加载

## 🔧 配置方法

### 方法1: 在.env文件中配置（推荐用于测试）

编辑 `.env` 文件，将以下行：
```bash
TUSHARE_TOKEN=your_tushare_token_here
```

改为你的真实Token：
```bash
TUSHARE_TOKEN=你的真实Tushare_Token
```

### 方法2: 在系统后台配置（推荐用于生产）

1. 访问系统后台配置页面
2. 进入"数据源配置"
3. 添加或编辑Tushare数据源：
   - 数据源类型：选择 `tushare`
   - API密钥：填写你的Tushare Token
   - 启用：勾选
4. 保存配置

**注意**：系统后台配置会保存到数据库，系统启动时会自动加载。

## 🧪 测试方法

### 测试脚本1: 直接读取.env文件测试

```bash
py scripts/测试Tushare直接读取.py
```

### 测试脚本2: 从数据库读取配置测试

```bash
py scripts/测试Tushare从数据库读取.py
```

**注意**：此脚本需要MongoDB运行，如果MongoDB未运行会失败。

### 测试脚本3: 手动输入Token测试

```bash
py scripts/简单测试Tushare.py
```

运行后会提示输入Token，可以直接输入进行测试。

## 📊 测试结果说明

### 成功的情况

如果Token有效，会看到：
```
[成功] Tushare API初始化完成
[成功] 获取到 XXXX 只股票
[成功] 有行业信息的股票: XXXX 只
[成功] 股票名称: XXX
[成功] 所属行业: XXX
```

### 失败的情况

如果Token无效，会看到：
```
[错误] Token无效: 您的token不对，请确认。
```

**解决方法**：
1. 检查Token是否正确
2. 确认Token是否过期
3. 访问 https://tushare.pro/ 检查Token状态

## 💡 使用建议

1. **获取Token**：
   - 访问 https://tushare.pro/
   - 注册/登录账号
   - 在个人中心获取Token

2. **配置优先级**：
   - 系统后台配置（数据库）> .env文件配置
   - 如果系统正在运行，优先使用数据库配置

3. **在主脚本中使用**：
   - 主脚本 `scripts/使用TDX查询行业信息并更新.py` 已经支持Tushare
   - 如果TDX无法提供行业信息，会自动使用Tushare作为备用方案

## 🔍 验证配置是否生效

如果已在系统后台配置了Tushare：

1. **确保系统正在运行**：
   - 系统启动时会自动从数据库加载配置
   - 配置会被设置到环境变量中

2. **检查环境变量**：
   ```powershell
   echo $env:TUSHARE_TOKEN
   ```

3. **运行测试脚本**：
   ```bash
   py scripts/测试Tushare直接读取.py
   ```

## 📝 注意事项

1. Token格式：Tushare Token通常是32位字符串
2. Token权限：确保Token有足够的权限访问所需的数据接口
3. 网络连接：确保可以访问 tushare.pro 的API服务器
4. 配置更新：如果修改了配置，可能需要重启系统才能生效

