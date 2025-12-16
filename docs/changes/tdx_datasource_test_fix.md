# TDX数据源测试功能修复

## 问题描述

在 `http://localhost:3000/settings/config` 页面测试通达信数据源时失败，因为 `test_data_source_config` 方法中没有处理 TDX 数据源类型。

## 修复内容

### 1. 添加 TDX 测试支持

**文件**: `app/services/config_service.py`

在 `test_data_source_config` 方法中添加了对 TDX 数据源的测试支持：

```python
elif ds_type == "tdx":
    # 通达信 (TDX) 不需要 API Key，直接测试连接和获取数据
    try:
        # 导入通达信工具模块（使用与 data_source_manager.py 相同的方式）
        from data.tdx_utils import get_tdx_provider
        
        # 获取数据提供器实例
        provider = get_tdx_provider()
        
        if not provider:
            return {
                "success": False,
                "message": "无法创建通达信数据提供器",
                ...
            }
        
        # 测试连接
        if not provider.connected:
            if not provider.connect():
                return {
                    "success": False,
                    "message": "通达信服务器连接失败，请检查网络连接",
                    ...
                }
        
        # 测试获取实时数据（使用平安银行 000001）
        test_code = "000001"
        real_time_data = provider.get_real_time_data(test_code)
        
        if real_time_data and 'price' in real_time_data and real_time_data['price']:
            return {
                "success": True,
                "message": "成功连接到通达信数据源",
                "details": {
                    "type": ds_type,
                    "test_result": f"获取股票 {test_code} 实时数据成功",
                    "test_stock": test_code,
                    "test_price": real_time_data.get('price'),
                    "test_name": real_time_data.get('name', '未知')
                }
            }
        ...
    except ImportError as e:
        return {
            "success": False,
            "message": "通达信工具模块未安装，请确保 pytdx 库已安装: pip install pytdx",
            ...
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"通达信 API 调用失败: {str(e)}",
            ...
        }
```

## 测试流程

1. **连接测试**: 检查通达信服务器连接状态
2. **数据获取测试**: 尝试获取股票 `000001`（平安银行）的实时数据
3. **结果验证**: 验证返回的数据是否包含价格信息

## 测试特点

- ✅ **无需 API Key**: TDX 是免费数据源，不需要 API Key
- ✅ **轻量级测试**: 只获取单只股票的实时数据，快速验证连接
- ✅ **详细反馈**: 返回测试股票代码、价格和名称等信息
- ✅ **错误处理**: 完善的异常处理和错误提示

## 使用方法

1. 打开前端配置页面: `http://localhost:3000/settings/config`
2. 找到"通达信 (TDX)"数据源配置
3. 点击"测试连接"按钮
4. 查看测试结果：
   - ✅ 成功：显示"成功连接到通达信数据源"，包含测试股票信息
   - ❌ 失败：显示具体错误信息（连接失败、库未安装等）

## 相关文件

- `app/services/config_service.py` - 测试方法实现
- `data/tdx_utils.py` - 通达信数据提供器
- `tradingagents/dataflows/data_source_manager.py` - 数据源管理器（参考导入方式）

## 状态

✅ **已完成**: TDX 数据源测试功能已添加并测试通过

