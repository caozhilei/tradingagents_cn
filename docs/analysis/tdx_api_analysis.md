# 通达信股票数据获取接口分析

## 📋 概述

本文档详细分析了 `data/tdx_utils.py` 中通达信股票数据获取接口的实现机制、API认证方式和主要功能。

---

## 🔑 API Key 认证分析

### 重要发现：**通达信API不需要API Key**

通达信API采用**TCP/IP直连**方式，**不需要任何API Key或Token认证**。

### 连接方式

```66:111:data/tdx_utils.py
    def connect(self):
        """连接通达信服务器"""
        print(f"🔍 [DEBUG] 开始连接通达信服务器...")
        try:
            # 尝试从配置文件加载可用服务器
            print(f"🔍 [DEBUG] 加载服务器配置...")
            working_servers = self._load_working_servers()

            # 如果没有配置文件，使用默认服务器列表
            if not working_servers:
                print(f"🔍 [DEBUG] 未找到配置文件，使用默认服务器列表")
                working_servers = [
                    {'ip': '115.238.56.198', 'port': 7709},
                    {'ip': '115.238.90.165', 'port': 7709},
                    {'ip': '180.153.18.170', 'port': 7709},
                    {'ip': '119.147.212.81', 'port': 7709},  # 备用
                ]
            else:
                print(f"🔍 [DEBUG] 从配置文件加载了 {len(working_servers)} 个服务器")

            # 尝试连接可用服务器
            print(f"🔍 [DEBUG] 创建通达信API实例...")
            self.api = TdxHq_API()
            print(f"🔍 [DEBUG] 开始尝试连接服务器...")

            for i, server in enumerate(working_servers):
                try:
                    print(f"🔍 [DEBUG] 尝试连接服务器 {i+1}/{len(working_servers)}: {server['ip']}:{server['port']}")
                    result = self.api.connect(server['ip'], server['port'])
                    print(f"🔍 [DEBUG] 连接结果: {result}")
                    if result:
                        print(f"✅ 通达信API连接成功: {server['ip']}:{server['port']}")
                        self.connected = True
                        return True
                except Exception as e:
                    print(f"⚠️ 服务器 {server['ip']}:{server['port']} 连接失败: {e}")
                    continue

            print("❌ 所有通达信服务器连接失败")
            self.connected = False
            return False

        except Exception as e:
            print(f"❌ 通达信API连接失败: {e}")
            self.connected = False
            return False
```

### 认证机制

- **连接方式**: TCP Socket连接
- **认证要求**: 无（直接连接）
- **连接参数**: 仅需IP地址和端口号
- **默认端口**: 7709

---

## 🏗️ 核心架构

### 1. 依赖库

```38:47:data/tdx_utils.py
try:
    # 通达信Python接口
    import pytdx
    from pytdx.hq import TdxHq_API
    from pytdx.exhq import TdxExHq_API
    TDX_AVAILABLE = True
except ImportError:
    TDX_AVAILABLE = False
    print("⚠️ pytdx库未安装，无法使用通达信API")
    print("💡 安装命令: pip install pytdx")
```

**核心依赖**: `pytdx` Python库
- **安装命令**: `pip install pytdx`
- **主要类**: 
  - `TdxHq_API`: 行情API（主市场）
  - `TdxExHq_API`: 扩展行情API（备用，代码中未使用）

### 2. 主类结构

```50:64:data/tdx_utils.py
class TongDaXinDataProvider:
    """通达信数据提供器"""
    
    def __init__(self):
        print(f"🔍 [DEBUG] 初始化通达信数据提供器...")
        self.api = None
        self.exapi = None  # 扩展行情API
        self.connected = False

        print(f"🔍 [DEBUG] 检查pytdx库可用性: {TDX_AVAILABLE}")
        if not TDX_AVAILABLE:
            error_msg = "pytdx库未安装，请运行: pip install pytdx"
            print(f"❌ [DEBUG] {error_msg}")
            raise ImportError(error_msg)
        print(f"✅ [DEBUG] pytdx库检查通过")
```

---

## 📡 主要数据接口

### 1. 实时行情数据

**接口**: `get_real_time_data(stock_code: str) -> Dict`

```217:265:data/tdx_utils.py
    def get_real_time_data(self, stock_code: str) -> Dict:
        """
        获取股票实时数据
        Args:
            stock_code: 股票代码
        Returns:
            Dict: 实时数据
        """
        if not self.connected:
            if not self.connect():
                return {}
        
        try:
            market = self._get_market_code(stock_code)
            
            # 获取实时数据
            data = self.api.get_security_quotes([(market, stock_code)])

            if not data:
                return {}

            quote = data[0]
            
            # 安全获取字段，避免KeyError
            def safe_get(key, default=0):
                return quote.get(key, default)

            return {
                'code': stock_code,
                'name': self._get_stock_name(stock_code),  # 使用独立的股票名称获取方法
                'price': safe_get('price'),
                'last_close': safe_get('last_close'),
                'open': safe_get('open'),
                'high': safe_get('high'),
                'low': safe_get('low'),
                'volume': safe_get('vol'),
                'amount': safe_get('amount'),
                'change': safe_get('price') - safe_get('last_close'),
                'change_percent': ((safe_get('price') - safe_get('last_close')) / safe_get('last_close') * 100) if safe_get('last_close') > 0 else 0,
                'bid_prices': [safe_get(f'bid{i}') for i in range(1, 6)],
                'bid_volumes': [safe_get(f'bid_vol{i}') for i in range(1, 6)],
                'ask_prices': [safe_get(f'ask{i}') for i in range(1, 6)],
                'ask_volumes': [safe_get(f'ask_vol{i}') for i in range(1, 6)],
                'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            print(f"获取实时数据失败: {e}")
            return {}
```

**返回数据字段**:
- `code`: 股票代码
- `name`: 股票名称
- `price`: 当前价格
- `last_close`: 昨收价
- `open`: 开盘价
- `high`: 最高价
- `low`: 最低价
- `volume`: 成交量
- `amount`: 成交额
- `change`: 涨跌额
- `change_percent`: 涨跌幅
- `bid_prices`: 买1-5价
- `bid_volumes`: 买1-5量
- `ask_prices`: 卖1-5价
- `ask_volumes`: 卖1-5量
- `update_time`: 更新时间

### 2. 历史K线数据

**接口**: `get_stock_history_data(stock_code, start_date, end_date, period='D') -> pd.DataFrame`

```267:337:data/tdx_utils.py
    def get_stock_history_data(self, stock_code: str, start_date: str, end_date: str, period: str = 'D') -> pd.DataFrame:
        """
        获取股票历史数据
        Args:
            stock_code: 股票代码
            start_date: 开始日期 'YYYY-MM-DD'
            end_date: 结束日期 'YYYY-MM-DD'
            period: 周期 'D'=日线, 'W'=周线, 'M'=月线
        Returns:
            DataFrame: 历史数据
        """
        if not self.connected:
            if not self.connect():
                return pd.DataFrame()
        
        try:
            market = self._get_market_code(stock_code)
            
            # 计算需要获取的数据量
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            days_diff = (end_dt - start_dt).days
            
            # 根据周期调整数据量
            if period == 'D':
                count = min(days_diff + 10, 800)  # 日线最多800条
            elif period == 'W':
                count = min(days_diff // 7 + 10, 800)
            elif period == 'M':
                count = min(days_diff // 30 + 10, 800)
            else:
                count = 800
            
            # 获取K线数据
            category_map = {'D': 9, 'W': 5, 'M': 6}
            category = category_map.get(period, 9)
            
            data = self.api.get_security_bars(category, market, stock_code, 0, count)
            
            if not data:
                return pd.DataFrame()
            
            # 转换为DataFrame
            df = pd.DataFrame(data)
            
            # 处理数据格式
            df['datetime'] = pd.to_datetime(df['datetime'])
            df = df.set_index('datetime')
            df = df.sort_index()
            
            # 筛选日期范围
            df = df[start_date:end_date]
            
            # 重命名列以匹配Yahoo Finance格式
            df = df.rename(columns={
                'open': 'Open',
                'high': 'High', 
                'low': 'Low',
                'close': 'Close',
                'vol': 'Volume',
                'amount': 'Amount'
            })
            
            # 添加股票代码信息
            df['Symbol'] = stock_code
            
            return df
            
        except Exception as e:
            print(f"获取历史数据失败: {e}")
            return pd.DataFrame()
```

**关键参数**:
- `period`: 周期类型
  - `'D'`: 日线 (category=9)
  - `'W'`: 周线 (category=5)
  - `'M'`: 月线 (category=6)
- **数据限制**: 单次最多800条
- **返回格式**: pandas DataFrame，列名为 `Open`, `High`, `Low`, `Close`, `Volume`, `Amount`

### 3. 技术指标计算

**接口**: `get_stock_technical_indicators(stock_code, period=20) -> Dict`

```339:396:data/tdx_utils.py
    def get_stock_technical_indicators(self, stock_code: str, period: int = 20) -> Dict:
        """
        计算技术指标
        Args:
            stock_code: 股票代码
            period: 计算周期
        Returns:
            Dict: 技术指标数据
        """
        try:
            # 获取最近的历史数据
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=period*2)).strftime('%Y-%m-%d')
            
            df = self.get_stock_history_data(stock_code, start_date, end_date)
            
            if df.empty:
                return {}
            
            # 计算技术指标
            indicators = {}
            
            # 移动平均线
            indicators['MA5'] = df['Close'].rolling(5).mean().iloc[-1] if len(df) >= 5 else None
            indicators['MA10'] = df['Close'].rolling(10).mean().iloc[-1] if len(df) >= 10 else None
            indicators['MA20'] = df['Close'].rolling(20).mean().iloc[-1] if len(df) >= 20 else None
            
            # RSI
            if len(df) >= 14:
                delta = df['Close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
                rs = gain / loss
                indicators['RSI'] = (100 - (100 / (1 + rs))).iloc[-1]
            
            # MACD
            if len(df) >= 26:
                exp1 = df['Close'].ewm(span=12).mean()
                exp2 = df['Close'].ewm(span=26).mean()
                macd = exp1 - exp2
                signal = macd.ewm(span=9).mean()
                indicators['MACD'] = macd.iloc[-1]
                indicators['MACD_Signal'] = signal.iloc[-1]
                indicators['MACD_Histogram'] = (macd - signal).iloc[-1]
            
            # 布林带
            if len(df) >= 20:
                sma = df['Close'].rolling(20).mean()
                std = df['Close'].rolling(20).std()
                indicators['BB_Upper'] = (sma + 2 * std).iloc[-1]
                indicators['BB_Middle'] = sma.iloc[-1]
                indicators['BB_Lower'] = (sma - 2 * std).iloc[-1]
            
            return indicators
            
        except Exception as e:
            print(f"计算技术指标失败: {e}")
            return {}
```

**计算的技术指标**:
- **移动平均线**: MA5, MA10, MA20
- **RSI**: 相对强弱指标（14周期）
- **MACD**: 包括MACD线、信号线、柱状图
- **布林带**: 上轨、中轨、下轨

### 4. 市场概览

**接口**: `get_market_overview() -> Dict`

```464:499:data/tdx_utils.py
    def get_market_overview(self) -> Dict:
        """获取市场概览"""
        if not self.connected:
            if not self.connect():
                return {}
        
        try:
            # 获取主要指数数据
            indices = {
                '上证指数': ('1', '000001'),
                '深证成指': ('0', '399001'),
                '创业板指': ('0', '399006'),
                '科创50': ('1', '000688')
            }
            
            market_data = {}
            
            for name, (market, code) in indices.items():
                try:
                    data = self.api.get_security_quotes([(int(market), code)])
                    if data:
                        quote = data[0]
                        market_data[name] = {
                            'price': quote['price'],
                            'change': quote['price'] - quote['last_close'],
                            'change_percent': ((quote['price'] - quote['last_close']) / quote['last_close'] * 100) if quote['last_close'] > 0 else 0,
                            'volume': quote['vol']
                        }
                except:
                    continue
            
            return market_data
            
        except Exception as e:
            print(f"获取市场概览失败: {e}")
            return {}
```

**监控的指数**:
- 上证指数 (000001)
- 深证成指 (399001)
- 创业板指 (399006)
- 科创50 (000688)

---

## ⚙️ 服务器配置

### 默认服务器列表

```77:82:data/tdx_utils.py
                working_servers = [
                    {'ip': '115.238.56.198', 'port': 7709},
                    {'ip': '115.238.90.165', 'port': 7709},
                    {'ip': '180.153.18.170', 'port': 7709},
                    {'ip': '119.147.212.81', 'port': 7709},  # 备用
                ]
```

### 配置文件支持

```113:126:data/tdx_utils.py
    def _load_working_servers(self):
        """加载可用服务器配置"""
        try:
            import json
            import os

            config_file = 'tdx_servers_config.json'
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    return config.get('working_servers', [])
        except Exception:
            pass
        return []
```

**配置文件格式** (`tdx_servers_config.json`):
```json
{
  "working_servers": [
    {"ip": "115.238.56.198", "port": 7709},
    {"ip": "115.238.90.165", "port": 7709}
  ]
}
```

---

## 🗺️ 市场代码映射

```449:462:data/tdx_utils.py
    def _get_market_code(self, stock_code: str) -> int:
        """
        根据股票代码判断市场
        Args:
            stock_code: 股票代码
        Returns:
            int: 市场代码 (0=深圳, 1=上海)
        """
        if stock_code.startswith(('000', '002', '003', '300')):
            return 0  # 深圳
        elif stock_code.startswith(('600', '601', '603', '605', '688')):
            return 1  # 上海
        else:
            return 0  # 默认深圳
```

**市场代码规则**:
- **深圳市场 (0)**:
  - `000xxx`: 深圳主板
  - `002xxx`: 深圳中小板
  - `003xxx`: 深圳主板（新）
  - `300xxx`: 深圳创业板
- **上海市场 (1)**:
  - `600xxx`: 上海主板
  - `601xxx`: 上海主板（大盘股）
  - `603xxx`: 上海主板
  - `605xxx`: 上海主板
  - `688xxx`: 科创板

---

## 💾 缓存机制

### 1. 股票名称缓存

```502:504:data/tdx_utils.py
# 全局实例和缓存
_tdx_provider = None
_stock_name_cache = {}  # 股票名称缓存，避免重复API调用
```

### 2. 数据缓存策略

```633:675:data/tdx_utils.py
    # 优先尝试从数据库缓存加载数据（使用统一的database_manager）
    try:
        from tradingagents.config.database_manager import get_database_manager
        db_manager = get_database_manager()
        if db_manager.is_mongodb_available():
            # 直接使用MongoDB客户端查询缓存数据
            mongodb_client = db_manager.get_mongodb_client()
            if mongodb_client:
                db = mongodb_client[db_manager.mongodb_config["database"]]
                collection = db.stock_data

                # 查询最近的缓存数据
                from datetime import datetime, timedelta
                cutoff_time = datetime.utcnow() - timedelta(hours=6)

                cached_doc = collection.find_one({
                    "symbol": stock_code,
                    "market_type": "china",
                    "created_at": {"$gte": cutoff_time}
                }, sort=[("created_at", -1)])

                if cached_doc and 'data' in cached_doc:
                    print(f"🗄️ 从MongoDB缓存加载数据: {stock_code}")
                    return cached_doc['data']
    except Exception as e:
        print(f"⚠️ 从MongoDB加载缓存失败: {e}")

    # 如果数据库缓存不可用，尝试文件缓存
    if FILE_CACHE_AVAILABLE:
        cache = get_cache()
        cache_key = cache.find_cached_stock_data(
            symbol=stock_code,
            start_date=start_date,
            end_date=end_date,
            data_source="tdx",
            max_age_hours=6  # 6小时内的缓存有效
        )

        if cache_key:
            cached_data = cache.load_stock_data(cache_key)
            if cached_data:
                print(f"💾 从文件缓存加载数据: {stock_code} -> {cache_key}")
                return cached_data
```

**缓存层级**:
1. **MongoDB缓存** (优先级最高): 6小时有效期
2. **文件缓存** (备用): 6小时有效期
3. **内存缓存**: 股票名称缓存（全局变量）

---

## 🔧 主要公共接口

### 1. 获取数据提供器实例

```604:618:data/tdx_utils.py
def get_tdx_provider() -> TongDaXinDataProvider:
    """获取通达信数据提供器实例"""
    global _tdx_provider
    if _tdx_provider is None:
        print(f"🔍 [DEBUG] 创建新的通达信数据提供器实例...")
        _tdx_provider = TongDaXinDataProvider()
        print(f"🔍 [DEBUG] 通达信数据提供器实例创建完成")
    else:
        print(f"🔍 [DEBUG] 使用现有的通达信数据提供器实例")
        # 检查连接状态，如果连接断开则重新创建
        if not _tdx_provider.is_connected():
            print(f"🔍 [DEBUG] 检测到连接断开，重新创建通达信数据提供器...")
            _tdx_provider = TongDaXinDataProvider()
            print(f"🔍 [DEBUG] 通达信数据提供器重新创建完成")
    return _tdx_provider
```

### 2. 获取中国股票数据（主接口）

```621:630:data/tdx_utils.py
def get_china_stock_data(stock_code: str, start_date: str, end_date: str) -> str:
    """
    获取中国股票数据的主要接口函数（支持缓存）
    Args:
        stock_code: 股票代码 (如 '000001')
        start_date: 开始日期 'YYYY-MM-DD'
        end_date: 结束日期 'YYYY-MM-DD'
    Returns:
        str: 格式化的股票数据
    """
```

**功能**: 
- 自动缓存管理
- 获取历史数据、实时数据、技术指标
- 格式化输出为Markdown字符串

### 3. 获取市场概览

```803:828:data/tdx_utils.py
def get_china_market_overview() -> str:
    """获取中国股市概览"""
    try:
        provider = get_tdx_provider()
        market_data = provider.get_market_overview()
        
        if not market_data:
            return "无法获取市场概览数据"
        
        result = "# 中国股市概览\n\n"
        
        for name, data in market_data.items():
            change_symbol = "📈" if data['change'] >= 0 else "📉"
            result += f"## {change_symbol} {name}\n"
            result += f"- 当前点位: {data['price']:.2f}\n"
            result += f"- 涨跌点数: {data['change']:+.2f}\n"
            result += f"- 涨跌幅: {data['change_percent']:+.2f}%\n"
            result += f"- 成交量: {data['volume']:,}\n\n"
        
        result += f"更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        result += "数据来源: 通达信API\n"
        
        return result
        
    except Exception as e:
        return f"获取市场概览失败: {str(e)}"
```

---

## 📊 数据流程

```
用户请求
    ↓
get_china_stock_data()
    ↓
检查MongoDB缓存 (6小时内)
    ↓ (缓存未命中)
检查文件缓存 (6小时内)
    ↓ (缓存未命中)
get_tdx_provider()
    ↓
连接通达信服务器 (自动重试多个服务器)
    ↓
获取历史数据 (get_stock_history_data)
    ↓
获取实时数据 (get_real_time_data)
    ↓
计算技术指标 (get_stock_technical_indicators)
    ↓
格式化输出
    ↓
保存到MongoDB缓存
    ↓
保存到文件缓存
    ↓
返回结果
```

---

## ⚠️ 限制和注意事项

### 1. 数据限制
- **历史数据**: 单次最多800条K线
- **连接超时**: 无明确超时设置（依赖pytdx库默认值）
- **服务器稳定性**: 依赖第三方服务器，可能不稳定

### 2. 错误处理
- 自动重试多个服务器
- 连接断开时自动重新创建实例
- 缓存降级机制（MongoDB → 文件 → 直接API）

### 3. 依赖要求
- **必需**: `pytdx` 库
- **可选**: 
  - MongoDB（用于缓存）
  - `pymongo`（用于股票名称查询）
  - `cache_manager`（用于文件缓存）

---

## 🔍 底层API调用

### pytdx库主要方法

1. **连接**: `api.connect(ip, port)`
2. **获取行情**: `api.get_security_quotes([(market, code)])`
3. **获取K线**: `api.get_security_bars(category, market, code, start, count)`
4. **获取股票列表**: `api.get_security_list(market, start_pos)` (仅深圳市场)
5. **获取股票数量**: `api.get_security_count(market)`

---

## 📝 总结

### API Key状态
✅ **无需API Key** - 通达信API采用TCP直连，无需认证

### 主要特点
1. **免费使用**: 无需注册或API Key
2. **实时数据**: 支持实时行情和五档买卖盘
3. **历史数据**: 支持日/周/月K线
4. **技术指标**: 内置常用技术指标计算
5. **缓存机制**: 多级缓存提升性能
6. **容错机制**: 自动重试和降级

### 适用场景
- ✅ A股实时行情查询
- ✅ 历史K线数据分析
- ✅ 技术指标计算
- ✅ 市场指数监控
- ❌ 高频交易（有连接限制）
- ❌ 大量并发请求（服务器可能限制）

---

## 🔗 相关文档

- [pytdx库文档](https://github.com/rainx/pytdx)
- [通达信协议说明](https://github.com/rainx/pytdx/blob/master/docs/protocol.md)

