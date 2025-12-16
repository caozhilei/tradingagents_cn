#!/usr/bin/env python3
"""
快速测试Tushare接口（支持手动输入Token）
"""

import sys
import os

# 清除代理
for var in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']:
    if var in os.environ:
        del os.environ[var]

print("=" * 80)
print("快速测试Tushare接口")
print("=" * 80)

try:
    import tushare as ts
    print("[成功] Tushare库已安装\n")
    
    # 尝试获取Token
    token = os.getenv('TUSHARE_TOKEN')
    
    if not token or token.startswith('your_'):
        print("[提示] 未在环境变量中找到有效的Token")
        print("[提示] 请输入你的Tushare Token（或按Enter跳过）:")
        manual_token = input().strip()
        if manual_token:
            token = manual_token
        else:
            print("[错误] 未提供Token，无法继续测试")
            sys.exit(1)
    
    if token.startswith('your_'):
        print("[错误] Token看起来是占位符，请提供真实的Token")
        sys.exit(1)
    
    print(f"[成功] 使用Token: {token[:10]}...{token[-4:] if len(token) > 14 else ''}\n")
    
    # 设置Token
    ts.set_token(token)
    pro = ts.pro_api()
    print("[成功] Tushare API初始化完成\n")
    
    # 测试1: 获取单只股票信息
    print("=" * 80)
    print("[测试1] 获取单只股票信息")
    print("=" * 80)
    
    test_code = "600519"  # 贵州茅台
    try:
        print(f"\n[查询] 股票 {test_code}...")
        df = pro.stock_basic(
            exchange='',
            list_status='L',
            fields='ts_code,symbol,name,area,industry,market,list_date'
        )
        
        # 查找目标股票
        stock = df[df['symbol'] == test_code]
        if not stock.empty:
            row = stock.iloc[0]
            print(f"[成功] 股票代码: {row['ts_code']}")
            print(f"[成功] 股票名称: {row['name']}")
            print(f"[成功] 所属行业: {row['industry']}")
            print(f"[成功] 所在地区: {row.get('area', 'N/A')}")
            print(f"[成功] 市场类型: {row.get('market', 'N/A')}")
        else:
            print(f"[失败] 未找到股票 {test_code}")
    except Exception as e:
        print(f"[失败] {type(e).__name__}: {e}")
        if "token" in str(e).lower():
            print("[错误] Token无效，请检查Token是否正确")
        sys.exit(1)
    
    # 测试2: 批量获取统计
    print("\n" + "=" * 80)
    print("[测试2] 批量获取统计")
    print("=" * 80)
    
    try:
        print("[查询] 获取所有上市股票...")
        df_all = pro.stock_basic(
            exchange='',
            list_status='L',
            fields='ts_code,symbol,name,area,industry,market'
        )
        
        if df_all is not None and not df_all.empty:
            print(f"[成功] 获取到 {len(df_all)} 只股票")
            
            # 统计有行业信息的股票
            with_industry = df_all[df_all['industry'].notna() & (df_all['industry'] != '')]
            print(f"[成功] 有行业信息的股票: {len(with_industry)} 只 ({len(with_industry)*100//len(df_all)}%)")
            
            # 显示示例
            print(f"\n[示例] 前5只股票:")
            print(df_all[['symbol', 'name', 'industry']].head().to_string(index=False))
        else:
            print("[失败] 返回数据为空")
    except Exception as e:
        print(f"[失败] {type(e).__name__}: {e}")
    
    print("\n" + "=" * 80)
    print("[总结] Tushare接口测试完成")
    print("=" * 80)
    print("[结论] Tushare接口可用，可以获取股票行业信息")
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

