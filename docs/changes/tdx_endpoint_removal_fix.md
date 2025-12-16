# TDX数据源API端点字段删除修复

## 问题描述

在编辑TDX数据源时，即使API端点字段留空，测试连接仍然失败。需要确保TDX数据源不保存API端点参数。

## 修复内容

### 1. 前端修复

**文件**: `frontend/src/views/Settings/components/DataSourceConfigDialog.vue`

在保存数据源配置时，如果是TDX数据源，自动删除endpoint字段：

```typescript
// 🔥 TDX数据源特殊处理：删除endpoint字段（TDX不需要API端点）
if (isTdxDataSource.value) {
  delete payload.endpoint
  console.log('🔍 [保存] TDX数据源：删除endpoint字段（TDX不需要API端点）')
}
```

### 2. 后端修复

**文件**: `app/routers/config.py`

#### 添加数据源时

```python
# 🔥 TDX数据源特殊处理：删除endpoint字段（TDX不需要API端点）
ds_type = _req.get('type')
if ds_type == 'tdx':
    _req['endpoint'] = None
    logger.info(f"🔍 [TDX数据源] 删除endpoint字段（TDX不需要API端点）")
```

#### 更新数据源时

```python
# 🔥 TDX数据源特殊处理：删除endpoint字段（TDX不需要API端点）
ds_type = _req.get('type') or ds_config.type.value if hasattr(ds_config.type, 'value') else str(ds_config.type)
if ds_type == 'tdx' or ds_config.type.value == 'tdx':
    _req['endpoint'] = None
    logger.info(f"🔍 [TDX数据源] 删除endpoint字段（TDX不需要API端点）")
```

## 修复效果

### 修复前

- ❌ TDX数据源保存时会包含endpoint字段（即使为空）
- ❌ 测试连接时可能因为endpoint字段导致验证失败

### 修复后

- ✅ TDX数据源保存时自动删除endpoint字段
- ✅ 前端保存时删除endpoint字段
- ✅ 后端添加/更新时自动设置为None
- ✅ 测试连接时endpoint字段为None，不会影响测试

## 使用说明

### 编辑TDX数据源

1. 打开配置页面：`http://localhost:3000/settings/config`
2. 编辑TDX数据源
3. **API端点字段**：显示为禁用状态，提示"通达信无需填写API端点（留空即可）"
4. 保存配置
5. ✅ **系统会自动删除endpoint字段**，不会保存到数据库

### 测试连接

1. 编辑TDX数据源
2. API端点字段留空（已禁用）
3. 点击"测试连接"
4. ✅ **应该显示**："成功连接到通达信数据源"

## 清理现有数据

如果数据库中已有TDX数据源配置包含endpoint字段，可以通过以下方式清理：

### 方法1：通过前端界面

1. 编辑TDX数据源
2. 保存配置（系统会自动删除endpoint字段）

### 方法2：直接更新数据库（如果需要）

```python
# 在Docker容器内运行
docker-compose exec backend python -c "
from app.core.database import get_database
import asyncio

async def clean():
    db = await get_database()
    collection = db['system_configs']
    configs = await collection.find({}).to_list(length=None)
    for config in configs:
        if 'data_source_configs' in config:
            updated = False
            for ds in config['data_source_configs']:
                if ds.get('type') == 'tdx' and ds.get('endpoint'):
                    ds['endpoint'] = None
                    updated = True
            if updated:
                await collection.update_one({'_id': config['_id']}, {'$set': config})
                print(f'Updated config: {config[\"_id\"]}')

asyncio.run(clean())
"
```

## 相关文件

- `frontend/src/views/Settings/components/DataSourceConfigDialog.vue` - 前端保存逻辑
- `app/routers/config.py` - 后端添加/更新逻辑
- `app/services/config_service.py` - 后端测试逻辑

## 状态

✅ **已完成**：
- ✅ 前端代码已更新
- ✅ 后端代码已更新
- ✅ 前端镜像已重新构建
- ✅ 后端服务已重启

现在TDX数据源在保存和更新时会自动删除endpoint字段，测试连接应该可以正常工作了！

