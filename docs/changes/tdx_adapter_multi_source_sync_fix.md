# TDX数据源多数据源同步界面显示修复

## 问题描述

在多数据源同步界面（`http://localhost:3000/settings/sync`）没有显示TDX数据源。

## 问题原因

`app/services/data_sources/manager.py` 中的 `DataSourceManager` 只初始化了三个适配器：
- TushareAdapter
- AKShareAdapter
- BaoStockAdapter

**缺少TDX适配器**，导致TDX数据源无法在多数据源同步界面显示。

## 修复内容

### 1. 创建TDX适配器

**文件**: `app/services/data_sources/tdx_adapter.py` (新建)

创建了TDX适配器类，实现 `DataSourceAdapter` 接口：

```python
class TDXAdapter(DataSourceAdapter):
    """TDX（通达信）数据源适配器"""
    
    @property
    def name(self) -> str:
        return "tdx"
    
    def _get_default_priority(self) -> int:
        return 10  # TDX作为默认数据源，优先级最高
    
    def is_available(self) -> bool:
        """检查TDX是否可用"""
        # 尝试连接TDX服务器验证可用性
        ...
```

**注意**：TDX主要用于实时行情，不提供股票列表和每日基础财务数据，这些方法返回None，让系统使用其他数据源。

### 2. 添加TDX适配器到管理器

**文件**: `app/services/data_sources/manager.py`

```python
# 尝试导入TDX适配器
try:
    from .tdx_adapter import TDXAdapter
    TDX_ADAPTER_AVAILABLE = True
except ImportError:
    TDX_ADAPTER_AVAILABLE = False
    logger.warning("TDX适配器不可用，跳过导入")

class DataSourceManager:
    def __init__(self):
        adapters_list = [
            AKShareAdapter(),
            TushareAdapter(),
            BaoStockAdapter(),
        ]
        
        # 添加TDX适配器（如果可用）
        if TDX_ADAPTER_AVAILABLE:
            adapters_list.insert(0, TDXAdapter())  # TDX优先级最高，放在最前面
            logger.info("✅ TDX适配器已添加到数据源管理器")
        else:
            logger.warning("⚠️ TDX适配器不可用，跳过添加")
        
        self.adapters: List[DataSourceAdapter] = adapters_list
```

## 验证结果

### 后端验证

```bash
docker-compose exec backend python -c "from app.services.data_sources.manager import DataSourceManager; m = DataSourceManager(); print('适配器列表:', [a.name for a in m.adapters]); print('可用适配器:', [a.name for a in m.get_available_adapters()])"
```

结果：
- ✅ **适配器列表**: `['tdx', 'akshare', 'tushare', 'baostock']`
- ✅ **可用适配器**: `['tdx', 'akshare', 'baostock']`
- ✅ **TDX连接成功**: `✅ 通达信API连接成功: 115.238.56.198:7709`
- ✅ **TDX可用**: `Data source tdx is available (priority: 2)`

### 前端验证

1. **刷新浏览器**（硬刷新：Ctrl+F5）
2. **打开多数据源同步页面**：`http://localhost:3000/settings/sync`
3. **查看数据源状态**：应该能看到TDX数据源
4. ✅ **TDX数据源应该显示**：
   - 名称：TDX
   - 优先级：2（从数据库读取）
   - 状态：可用
   - 描述：通达信实时行情接口，提供A股实时行情和历史K线数据，完全免费且无需API Key

## TDX适配器特性

### 支持的功能

- ✅ **实时行情**：TDX的主要功能
- ✅ **历史K线**：可以获取历史K线数据
- ✅ **连接测试**：可以测试连接状态

### 不支持的功能（返回None，使用其他数据源）

- ❌ **股票列表**：TDX不提供股票列表，使用AKShare或其他数据源
- ❌ **每日基础财务数据**：TDX不提供每日基础财务数据，使用Tushare或其他数据源
- ❌ **全市场实时快照**：需要遍历所有股票，效率低，使用AKShare
- ❌ **新闻和公告**：TDX不提供新闻数据

## 相关文件

- `app/services/data_sources/tdx_adapter.py` - TDX适配器（新建）
- `app/services/data_sources/manager.py` - 数据源管理器（更新）
- `app/routers/multi_source_sync.py` - 多数据源同步API（已包含TDX描述）
- `frontend/src/components/Sync/DataSourceStatus.vue` - 数据源状态组件

## 状态

✅ **已完成**：
- ✅ TDX适配器已创建
- ✅ TDX适配器已添加到数据源管理器
- ✅ 后端镜像已重新构建
- ✅ 后端服务已重启
- ✅ TDX适配器已成功加载并可用

现在TDX数据源应该能在多数据源同步界面正常显示了！

