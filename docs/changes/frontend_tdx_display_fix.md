# 前端显示TDX数据源修复

## ✅ 已完成的修复

### 1. 前端数据源类型定义

**文件**: `frontend/src/views/Settings/components/DataSourceConfigDialog.vue`

✅ 在数据源类型列表中添加了TDX：
```typescript
{
  label: '通达信 (TDX)',
  value: 'tdx',
  register_url: 'https://github.com/rainx/pytdx',
  register_guide: '通达信是免费的实时A股行情数据接口，无需注册和API Key即可使用。访问GitHub了解更多：'
}
```

### 2. 后端数据源状态API

**文件**: `app/routers/multi_source_sync.py`

✅ 在数据源描述字典中添加了TDX：
```python
descriptions = {
    "tdx": "通达信实时行情接口，提供A股实时行情和历史K线数据，完全免费且无需API Key",
    ...
}
```

### 3. 数据库配置更新

✅ 已通过脚本将TDX添加到数据库配置：
- TDX数据源已添加（优先级10，最高）
- TDX已设置为默认数据源
- 配置已保存到MongoDB

## 🔍 验证步骤

### 1. 检查后端API返回

访问后端API验证TDX是否在返回列表中：

```bash
# 获取数据源配置列表
curl http://localhost:8000/api/config/datasource

# 获取数据源状态
curl http://localhost:8000/api/sync/sources/status
```

### 2. 前端页面检查

1. 打开浏览器访问: `http://localhost:3000/settings/sync`
2. 在数据源配置部分应该能看到：
   - ✅ 通达信 (TDX) - 优先级10
   - ✅ 显示为"启用"状态
   - ✅ 显示为默认数据源

### 3. 如果仍然看不到

可能的原因和解决方案：

1. **前端缓存问题**
   - 清除浏览器缓存
   - 硬刷新页面 (Ctrl+F5)

2. **后端未重启**
   - 重启后端服务: `docker-compose restart backend`
   - 检查后端日志: `docker-compose logs -f backend`

3. **数据库配置未同步**
   - 运行更新脚本: `py scripts/add_tdx_to_database_direct.py`
   - 检查MongoDB中的配置

## 📊 当前数据库状态

根据脚本输出，当前配置：
- ✅ TDX已添加（优先级10）
- ✅ TDX已设置为默认数据源
- ✅ TDX已启用

数据源列表（按优先级）：
1. ✅ 通达信 (优先级: 10, 类型: tdx)
2. ✅ AKShare (优先级: 1, 类型: akshare)
3. ✅ Tushare (优先级: 1, 类型: tushare)

## 🎯 下一步

1. ✅ 后端已重启
2. ⏭️ 刷新前端页面查看
3. ⏭️ 如果仍看不到，检查浏览器控制台错误

