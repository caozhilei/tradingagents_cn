#!/usr/bin/env python3
"""
测试Tushare接口（从数据库读取配置）
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 清除代理
for var in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']:
    if var in os.environ:
        del os.environ[var]

print("=" * 80)
print("测试Tushare接口（从数据库读取配置）")
print("=" * 80)

try:
    import tushare as ts
    print("[成功] Tushare库已安装\n")
    
    # 方法1: 从数据库读取配置
    token = None
    print("[方法1] 尝试从数据库读取Tushare配置...")
    try:
        from app.core.database import get_mongo_db_sync
        db = get_mongo_db_sync()
        config_collection = db.system_configs
        
        # 获取最新的激活配置
        config_data = config_collection.find_one(
            {"is_active": True},
            sort=[("version", -1)]
        )
        
        if config_data and config_data.get('data_source_configs'):
            data_source_configs = config_data.get('data_source_configs', [])
            print(f"[成功] 从数据库读取到 {len(data_source_configs)} 个数据源配置")
            
            for ds_config in data_source_configs:
                ds_type = ds_config.get('type', '')
                if isinstance(ds_type, dict):
                    ds_type = ds_type.get('value', '') or str(ds_type)
                ds_type = str(ds_type).lower()
                
                if ds_type == 'tushare':
                    enabled = ds_config.get('enabled', False)
                    api_key = ds_config.get('api_key', '')
                    
                    print(f"[信息] 找到Tushare配置: enabled={enabled}, api_key长度={len(api_key) if api_key else 0}")
                    
                    if enabled and api_key and not api_key.startswith('your_'):
                        token = api_key
                        print(f"[成功] 从数据库读取到有效的Tushare Token")
                        break
        else:
            print("[提示] 数据库中没有找到配置")
    except Exception as e:
        print(f"[提示] 从数据库读取失败: {type(e).__name__}: {e}")
        print("[提示] 可能原因: MongoDB未运行或连接配置问题")
    
    # 方法2: 从环境变量读取
    if not token or token.startswith('your_'):
        print("\n[方法2] 尝试从环境变量读取...")
        token = os.getenv('TUSHARE_TOKEN')
        if token and not token.startswith('your_'):
            print(f"[成功] 从环境变量读取到Token")
        else:
            print("[提示] 环境变量中未找到有效Token")
    
    # 方法3: 从settings读取
    if not token or token.startswith('your_'):
        print("\n[方法3] 尝试从settings读取...")
        try:
            from app.core.config import settings
            token = getattr(settings, 'TUSHARE_TOKEN', None)
            if token and not token.startswith('your_'):
                print(f"[成功] 从settings读取到Token")
            else:
                print("[提示] settings中未找到有效Token")
        except Exception as e:
            print(f"[提示] 读取settings失败: {type(e).__name__}")
    
    # 检查Token
    if not token or token.startswith('your_'):
        print("\n" + "=" * 80)
        print("[错误] 未找到有效的Tushare Token")
        print("=" * 80)
        print("[提示] 请检查以下位置:")
        print("  1. 系统后台配置页面 - 数据源配置中的Tushare")
        print("  2. .env文件中的TUSHARE_TOKEN")
        print("  3. 环境变量TUSHARE_TOKEN")
        print("\n[提示] 如果已在系统后台配置，请确保:")
        print("  - 数据源类型选择为 'tushare'")
        print("  - API密钥字段填写正确的Token")
        print("  - 数据源已启用")
        sys.exit(1)
    
    print(f"\n[成功] 找到有效的Token: {token[:10]}...{token[-4:] if len(token) > 14 else ''}")
    
    # 设置Token并测试
    print("\n[设置] 初始化Tushare API...")
    ts.set_token(token)
    pro = ts.pro_api()
    print("[成功] Tushare API初始化完成\n")
    
    # 测试获取股票信息
    print("=" * 80)
    print("[测试] 获取股票行业信息")
    print("=" * 80)
    
    test_stocks = [
        ('600519', 'SH'),  # 贵州茅台
        ('000001', 'SZ'),  # 平安银行
        ('000002', 'SZ'),  # 万科A
    ]
    
    success_count = 0
    for symbol, exchange in test_stocks:
        try:
            ts_code = f"{symbol}.{exchange}"
            print(f"\n[查询] {symbol} ({ts_code})...")
            
            df = pro.stock_basic(
                exchange='',
                list_status='L',
                fields='ts_code,symbol,name,area,industry,market,list_date'
            )
            
            stock = df[df['symbol'] == symbol]
            if not stock.empty:
                row = stock.iloc[0]
                print(f"  [成功] 名称: {row['name']}")
                print(f"  [成功] 行业: {row['industry']}")
                print(f"  [成功] 地区: {row.get('area', 'N/A')}")
                success_count += 1
            else:
                print(f"  [失败] 未找到股票")
        except Exception as e:
            error_msg = str(e)
            if "token" in error_msg.lower():
                print(f"  [错误] Token无效: {error_msg}")
                break
            else:
                print(f"  [失败] {type(e).__name__}: {error_msg}")
    
    # 测试批量获取
    print("\n" + "=" * 80)
    print("[测试] 批量获取统计")
    print("=" * 80)
    
    try:
        print("[查询] 获取所有上市股票...")
        df_all = pro.stock_basic(
            exchange='',
            list_status='L',
            fields='ts_code,symbol,name,industry'
        )
        
        if df_all is not None and not df_all.empty:
            total = len(df_all)
            with_industry = len(df_all[df_all['industry'].notna() & (df_all['industry'] != '')])
            
            print(f"[成功] 获取到 {total} 只股票")
            print(f"[成功] 有行业信息的股票: {with_industry} 只 ({with_industry*100//total if total > 0 else 0}%)")
            
            # 显示示例
            print(f"\n[示例] 前3只股票:")
            print(df_all[['symbol', 'name', 'industry']].head(3).to_string(index=False))
        else:
            print("[失败] 返回数据为空")
    except Exception as e:
        print(f"[失败] {type(e).__name__}: {e}")
    
    # 总结
    print("\n" + "=" * 80)
    print("[总结]")
    print("=" * 80)
    if success_count > 0:
        print(f"[成功] Tushare接口可用！成功获取 {success_count}/{len(test_stocks)} 只股票信息")
        print("[结论] Tushare可以用于获取股票行业信息")
    else:
        print("[失败] 未能成功获取股票信息")
    print("=" * 80)
    
except ImportError:
    print("[错误] Tushare库未安装")
    print("[提示] 安装命令: pip install tushare")
    sys.exit(1)
except Exception as e:
    print(f"[错误] 发生错误: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

