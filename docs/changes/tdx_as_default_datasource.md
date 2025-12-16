# 将通达信（TDX）设置为默认数据源

## 📋 更改概述

本次更改将通达信（TDX）数据源集成到项目中，并设置为默认数据源。通达信提供实时A股行情数据，完全免费且无需API Key。

## ✅ 完成的更改

### 1. 数据源编码定义 (`tradingagents/constants/data_sources.py`)

- ✅ 在 `DataSourceCode` 枚举中添加了 `TDX = "tdx"`
- ✅ 在 `DATA_SOURCE_REGISTRY` 中注册了通达信数据源信息：
  - 名称：通达信
  - 提供商：通达信
  - 支持市场：A股
  - 特性：实时行情、历史K线、五档买卖盘、技术指标、完全免费、无需API Key

### 2. 数据源类型定义 (`app/models/config.py`)

- ✅ 在 `DataSourceType` 枚举中添加了 `TDX = "tdx"`

### 3. 数据源管理器 (`tradingagents/dataflows/data_source_manager.py`)

- ✅ 在 `ChinaDataSource` 枚举中添加了 `TDX = DataSourceCode.TDX`
- ✅ 在 `_get_default_source()` 中将默认数据源从 `AKShare` 改为 `TDX`
- ✅ 在 `_get_data_source_priority_order()` 中将 `TDX` 设置为最高优先级（第一位）
- ✅ 在 `_check_available_sources()` 中添加了TDX可用性检查
- ✅ 在 `get_data_adapter()` 中添加了 `_get_tdx_adapter()` 方法
- ✅ 实现了 `_get_tdx_data()` 方法，调用 `data/tdx_utils.py` 中的接口
- ✅ 在 `get_stock_data()` 中添加了TDX数据源支持
- ✅ 在 `get_fundamentals_data()` 中添加了TDX支持（降级到基本分析）

### 4. 统一配置管理器 (`app/core/unified_config.py`)

- ✅ 在硬编码配置中添加了TDX数据源配置（优先级10，最高）
- ✅ 调整了其他数据源的优先级：
  - TDX: 10（最高）
  - AKShare: 5
  - Tushare: 3

### 5. 配置服务 (`app/services/config_service.py`)

- ✅ 在默认系统配置中添加了TDX数据源配置
- ✅ 将 `default_data_source` 从 `"AKShare"` 改为 `"TDX"`

## 🔧 数据源优先级

新的数据源优先级顺序（从高到低）：

1. **MongoDB** - 缓存数据源（如果启用，最高优先级）
2. **TDX（通达信）** - 默认数据源 ⭐
3. **AKShare** - 备用数据源
4. **Tushare** - 备用数据源（需要API Key）
5. **BaoStock** - 备用数据源

## 📊 通达信数据源特性

### 优势
- ✅ **完全免费** - 无需API Key
- ✅ **实时数据** - 提供实时行情和五档买卖盘
- ✅ **历史数据** - 支持日/周/月K线
- ✅ **技术指标** - 内置常用技术指标计算
- ✅ **数据完整** - 包含成交量、成交额等完整信息

### 限制
- ⚠️ 仅支持A股市场
- ⚠️ 依赖网络连接到通达信服务器
- ⚠️ 单次最多800条历史数据

## 🚀 使用方式

### 自动使用（默认）

系统会自动使用TDX作为默认数据源，无需额外配置：

```python
from tradingagents.dataflows.data_source_manager import get_data_source_manager

manager = get_data_source_manager()
# 自动使用TDX数据源
result = manager.get_stock_data("300476", "2025-01-01", "2025-01-31")
```

### 手动切换数据源

如果需要切换到其他数据源：

```python
from tradingagents.dataflows.data_source_manager import get_data_source_manager, ChinaDataSource

manager = get_data_source_manager()
manager.set_current_source(ChinaDataSource.AKSHARE)  # 切换到AKShare
```

### 环境变量配置

可以通过环境变量设置默认数据源：

```bash
# 使用TDX（默认）
DEFAULT_CHINA_DATA_SOURCE=tdx

# 或使用其他数据源
DEFAULT_CHINA_DATA_SOURCE=akshare
DEFAULT_CHINA_DATA_SOURCE=tushare
```

## 📝 依赖要求

通达信数据源需要以下依赖：

```bash
pip install pytdx
```

已在 `data/tdx_utils.py` 中实现完整的接口封装。

## 🔍 测试验证

已通过测试验证：
- ✅ 成功获取股票300476的实时股价
- ✅ 数据格式正确
- ✅ 接口调用正常

测试脚本：`tests/test_tdx_300476.py`

## 📚 相关文档

- [通达信API分析文档](../analysis/tdx_api_analysis.md)
- [测试报告](../../tests/test_tdx_300476_report.md)

## ⚠️ 注意事项

1. **网络连接**：通达信数据源需要网络连接到通达信服务器
2. **服务器稳定性**：依赖第三方服务器，可能不稳定
3. **降级机制**：如果TDX不可用，系统会自动降级到其他可用数据源
4. **缓存支持**：TDX数据会保存到MongoDB缓存（如果启用）

## 🎯 后续优化建议

1. 添加TDX数据源的连接状态监控
2. 优化错误处理和重试机制
3. 添加数据源性能监控
4. 支持更多周期类型（分钟线等）

