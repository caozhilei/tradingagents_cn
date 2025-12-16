# TDX数据源配置验证显示修复

## 问题描述

在配置验证界面（`http://localhost:3000/settings/config`），TDX数据源显示为"未配置"状态，但实际上TDX数据源不需要API Key，应该显示为"已配置"。

## 问题原因

`app/routers/system_config.py` 中的配置验证逻辑只将 `akshare` 和 `yahoo` 数据源标记为"无需密钥"，没有包含 `tdx` 数据源。

## 修复内容

### 修改文件

**文件**: `app/routers/system_config.py`

**修改前**：
```python
# 某些数据源不需要 API Key（如 AKShare）
if ds_config.type in ["akshare", "yahoo"]:
    validation_item["has_api_key"] = True
    validation_item["status"] = "已配置（无需密钥）"
    validation_item["source"] = "builtin"
    validation_item["mongodb_configured"] = True
    validation_item["env_configured"] = True
```

**修改后**：
```python
# 某些数据源不需要 API Key（如 AKShare、TDX）
# TDX（通达信）数据源不需要API Key和endpoint，直接连接服务器
if ds_config.type in ["akshare", "yahoo", "tdx"]:
    validation_item["has_api_key"] = True
    validation_item["status"] = "已配置（无需密钥）"
    validation_item["source"] = "builtin"
    validation_item["mongodb_configured"] = True
    validation_item["env_configured"] = True
```

## TDX数据源特性

### 不需要的配置

- ❌ **API Key**：TDX不需要API Key认证
- ❌ **API端点（endpoint）**：TDX直接连接到内置的服务器列表
- ❌ **环境变量配置**：TDX不需要在.env文件中配置

### 需要的配置

- ✅ **数据源配置存在**：在数据库中创建TDX数据源配置即可
- ✅ **启用状态**：确保数据源已启用（`enabled: true`）

## 验证步骤

1. **刷新浏览器**（硬刷新：Ctrl+F5）
2. **打开配置管理页面**：`http://localhost:3000/settings/config`
3. **切换到"配置验证"标签**
4. **查看MongoDB配置验证部分**：
   - ✅ TDX数据源应显示为"已配置（无需密钥）"
   - ✅ 状态标签应为绿色（success类型）
   - ✅ 图标应为绿色的勾选标记

## 相关文件

- `app/routers/system_config.py` - 系统配置验证API（已修复）
- `frontend/src/components/ConfigValidator.vue` - 配置验证组件（前端显示）

## 状态

✅ **已完成**：
- ✅ TDX数据源已添加到"无需密钥"列表
- ✅ TDX数据源验证状态设置为"已配置（无需密钥）"
- ✅ 后端服务已重启

现在TDX数据源在配置验证界面应该正确显示为"已配置（无需密钥）"状态了！

