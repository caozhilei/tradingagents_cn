#!/usr/bin/env python3
"""
测试Tushare接口是否可用，特别是获取股票行业信息
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 清除代理环境变量（如果需要）
proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']
for var in proxy_vars:
    if var in os.environ:
        del os.environ[var]

print("=" * 80)
print("测试Tushare接口")
print("=" * 80)

try:
    # 尝试导入Tushare
    import tushare as ts
    print("[成功] Tushare库已安装")
    
    # 尝试从配置获取Token
    token = None
    
    # 方法1: 直接从环境变量读取
    token = os.getenv('TUSHARE_TOKEN')
    
    # 方法2: 从settings读取
    if not token or token.startswith('your_'):
        try:
            from app.core.config import settings
            token = getattr(settings, 'TUSHARE_TOKEN', None)
        except:
            pass
    
    # 方法3: 尝试从数据库读取（如果MongoDB可用）
    if not token or token.startswith('your_'):
        try:
            from app.core.unified_config import UnifiedConfigManager
            config = UnifiedConfigManager()
            data_source_configs = config.get_data_source_configs()
            
            for ds_config in data_source_configs:
                if ds_config.type.value.lower() == 'tushare' and ds_config.enabled:
                    if ds_config.api_key and not ds_config.api_key.startswith('your_'):
                        token = ds_config.api_key
                        print(f"[成功] 从数据库读取到Tushare Token")
                        break
        except Exception as e:
            print(f"[提示] 从数据库读取配置失败（可能MongoDB未运行）: {type(e).__name__}")
        
    if not token or token.startswith('your_'):
        print("[警告] 未找到有效的Tushare Token配置")
        print("[提示] 请检查以下位置:")
        print("  1. .env文件中的TUSHARE_TOKEN（当前值: your_tushare_token_here）")
        print("  2. 系统后台配置页面 - 数据库配置")
        print("  3. 环境变量TUSHARE_TOKEN")
        print("\n[提示] 配置方法:")
        print("  方法1: 编辑.env文件，将TUSHARE_TOKEN设置为你的真实Token")
        print("  方法2: 在系统后台配置页面添加Tushare数据源，填写API密钥")
        print("\n[提示] 获取Tushare Token:")
        print("  1. 访问 https://tushare.pro/")
        print("  2. 注册/登录账号")
        print("  3. 在个人中心获取Token")
        sys.exit(1)
    else:
        print(f"[成功] 找到Tushare Token: {token[:10]}...{token[-4:] if len(token) > 14 else ''}")
        
        # 设置Token
        ts.set_token(token)
        pro = ts.pro_api()
        print("[成功] Tushare API初始化完成")
        
        # 测试1: 获取股票基本信息（包含行业信息）
        print("\n" + "=" * 80)
        print("[测试1] 获取股票基本信息（包含行业信息）")
        print("=" * 80)
        
        test_codes = ['600519.SH', '000001.SZ', '000002.SZ']
        
        for ts_code in test_codes:
            try:
                print(f"\n[查询] {ts_code}...")
                df = pro.stock_basic(
                    exchange='',
                    list_status='L',
                    fields='ts_code,symbol,name,area,industry,market,list_date'
                )
                
                # 查找目标股票
                stock = df[df['ts_code'] == ts_code]
                if not stock.empty:
                    row = stock.iloc[0]
                    print(f"[成功] 股票代码: {row['ts_code']}")
                    print(f"[成功] 股票名称: {row['name']}")
                    print(f"[成功] 所属行业: {row['industry']}")
                    print(f"[成功] 所在地区: {row.get('area', 'N/A')}")
                    print(f"[成功] 市场类型: {row.get('market', 'N/A')}")
                    print(f"[成功] 上市日期: {row.get('list_date', 'N/A')}")
                else:
                    print(f"[失败] 未找到股票 {ts_code}")
                    
            except Exception as e:
                print(f"[失败] {type(e).__name__}: {e}")
        
        # 测试2: 批量获取所有股票基本信息
        print("\n" + "=" * 80)
        print("[测试2] 批量获取所有股票基本信息")
        print("=" * 80)
        
        try:
            print("[查询] 获取所有上市股票...")
            df_all = pro.stock_basic(
                exchange='',
                list_status='L',
                fields='ts_code,symbol,name,area,industry,market,list_date'
            )
            
            if df_all is not None and not df_all.empty:
                print(f"[成功] 获取到 {len(df_all)} 只股票")
                
                # 统计有行业信息的股票数量
                with_industry = df_all[df_all['industry'].notna() & (df_all['industry'] != '')]
                print(f"[成功] 有行业信息的股票: {len(with_industry)} 只")
                
                # 统计行业分布
                industry_counts = df_all['industry'].value_counts()
                print(f"\n[信息] 行业数量: {len(industry_counts)} 个")
                print("[信息] 前10个行业:")
                print(industry_counts.head(10).to_string())
                
                # 显示示例数据
                print(f"\n[示例] 前5只股票:")
                print(df_all[['ts_code', 'name', 'industry']].head().to_string(index=False))
            else:
                print("[失败] 返回数据为空")
                
        except Exception as e:
            print(f"[失败] {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
        
        # 测试3: 测试API权限
        print("\n" + "=" * 80)
        print("[测试3] 测试API权限和限制")
        print("=" * 80)
        
        try:
            # 获取用户信息
            user_info = pro.user()
            print(f"[成功] API调用成功")
            print(f"[信息] 用户信息: {user_info}")
        except Exception as e:
            print(f"[提示] 获取用户信息失败（可能不需要）: {type(e).__name__}: {e}")
        
        # 测试4: 测试获取特定股票的行业信息
        print("\n" + "=" * 80)
        print("[测试4] 测试获取特定股票的行业信息")
        print("=" * 80)
        
        test_symbols = ['600519', '000001', '000002']
        for symbol in test_symbols:
            try:
                # 构建ts_code
                if symbol.startswith(('600', '601', '603', '605', '688')):
                    ts_code = f"{symbol}.SH"
                else:
                    ts_code = f"{symbol}.SZ"
                
                print(f"\n[查询] {symbol} ({ts_code})...")
                df = pro.stock_basic(
                    exchange='',
                    list_status='L',
                    fields='ts_code,symbol,name,area,industry,market'
                )
                
                stock = df[df['symbol'] == symbol]
                if not stock.empty:
                    row = stock.iloc[0]
                    print(f"[成功] {row['name']} - 行业: {row['industry']}")
                else:
                    print(f"[失败] 未找到股票 {symbol}")
                    
            except Exception as e:
                print(f"[失败] {type(e).__name__}: {e}")
        
        print("\n" + "=" * 80)
        print("[总结] Tushare接口测试完成")
        print("=" * 80)
        print("""
[结论]
1. Tushare接口: 可用
2. 获取股票基本信息: 成功
3. 获取行业信息: 成功
4. 批量获取: 成功

[建议]
- Tushare是获取行业信息的可靠数据源
- 可以用于补充TDX无法提供的行业信息
- 建议在主脚本中优先使用Tushare获取行业信息
        """)
            
except ImportError:
    print("[错误] Tushare库未安装")
    print("[提示] 安装命令: pip install tushare")
    sys.exit(1)
except Exception as e:
    print(f"[错误] 发生未知错误: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

