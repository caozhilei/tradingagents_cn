# TDX数据源API端点留空测试连接修复

## 问题描述

在编辑TDX数据源时，当API端点字段留空时，测试连接会失败，提示"不支持的数据源类型: tdx，且未配置端点"。

## 问题原因

1. **前端问题**: 测试连接时，如果endpoint为空字符串，可能会在某些验证逻辑中被当作错误
2. **后端问题**: 虽然TDX数据源的测试逻辑不依赖endpoint，但在某些情况下，空字符串可能导致验证失败

## 修复方案

### 1. 前端修复

**文件**: `frontend/src/views/Settings/components/DataSourceConfigDialog.vue`

在测试连接时，对TDX数据源做特殊处理：

```typescript
// 🔥 TDX数据源特殊处理：endpoint为空时设置为null，避免空字符串导致验证失败
if (isTdxDataSource.value && (!testPayload.endpoint || testPayload.endpoint.trim() === '')) {
  testPayload.endpoint = null
  console.log('🔍 [测试连接] TDX数据源：endpoint为空，设置为null')
}
```

### 2. 后端修复

**文件**: `app/services/config_service.py`

在TDX数据源测试逻辑中添加明确说明：

```python
elif ds_type == "tdx":
    # 通达信 (TDX) 不需要 API Key 和 endpoint，直接测试连接和获取数据
    # 🔥 特殊处理：TDX数据源不需要endpoint，即使为空也能正常工作
    logger.info(f"🧪 [TEST] Testing TDX data source (endpoint not required)")
    
    # ... 测试逻辑 ...
    
    return {
        "success": True,
        "message": f"成功连接到通达信数据源",
        "details": {
            ...
            "note": "TDX数据源不需要API端点，系统自动使用内置服务器列表"
        }
    }
```

## 修复效果

### 修复前

- ❌ API端点字段留空时，测试连接失败
- ❌ 提示："不支持的数据源类型: tdx，且未配置端点"

### 修复后

- ✅ API端点字段留空时，测试连接正常
- ✅ 前端自动将空字符串转换为null
- ✅ 后端明确处理TDX数据源，不依赖endpoint字段
- ✅ 测试成功时，返回信息中包含说明："TDX数据源不需要API端点，系统自动使用内置服务器列表"

## 测试步骤

1. 打开配置页面：`http://localhost:3000/settings/config`
2. 选择或编辑TDX数据源
3. **API端点字段留空**（或设置为空字符串）
4. 点击"测试连接"按钮
5. ✅ 应该显示："成功连接到通达信数据源"

## 相关文件

- `frontend/src/views/Settings/components/DataSourceConfigDialog.vue` - 前端测试连接逻辑
- `app/services/config_service.py` - 后端测试数据源配置逻辑
- `docs/guides/tdx_datasource_configuration.md` - TDX数据源配置指南

## 状态

✅ **已完成**: TDX数据源API端点留空时的测试连接问题已修复

