#!/usr/bin/env python3
"""
测试AKShare数据获取（完全清除代理设置）
"""

import os
import sys
from pathlib import Path

# 完全清除代理环境变量
proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'NO_PROXY', 'no_proxy']
for var in proxy_vars:
    if var in os.environ:
        del os.environ[var]
        print(f"[清除] {var}")

print("\n" + "=" * 80)
print("测试AKShare数据获取（无代理）")
print("=" * 80)

try:
    import akshare as ak
    
    # 测试1: 获取单只股票信息
    print("\n[测试1] 获取股票 600519 的行业信息...")
    try:
        stock_code = "600519"
        stock_info_df = ak.stock_individual_info_em(symbol=stock_code)
        
        if stock_info_df is not None and not stock_info_df.empty:
            # 提取行业信息
            industry_row = stock_info_df[stock_info_df['item'] == '所属行业']
            name_row = stock_info_df[stock_info_df['item'] == '股票简称']
            
            if not industry_row.empty:
                industry = str(industry_row['value'].iloc[0])
                name = str(name_row['value'].iloc[0]) if not name_row.empty else ''
                print(f"[成功] 股票: {name} ({stock_code})")
                print(f"[成功] 行业: {industry}")
            else:
                print("[失败] 未找到行业信息")
        else:
            print("[失败] 返回数据为空")
    except Exception as e:
        print(f"[失败] {type(e).__name__}: {e}")
    
    # 测试2: 获取股票列表（简单接口）
    print("\n[测试2] 获取A股列表...")
    try:
        stock_list = ak.stock_info_a_code_name()
        if stock_list is not None and not stock_list.empty:
            print(f"[成功] 获取到 {len(stock_list)} 只股票")
            print("[成功] 前5只股票:")
            print(stock_list.head().to_string(index=False))
        else:
            print("[失败] 返回数据为空")
    except Exception as e:
        print(f"[失败] {type(e).__name__}: {e}")
    
    # 测试3: 测试网络连接
    print("\n[测试3] 测试网络连接...")
    try:
        import requests
        response = requests.get('https://82.push2.eastmoney.com', timeout=5)
        print(f"[成功] 连接成功，状态码: {response.status_code}")
    except Exception as e:
        print(f"[失败] {type(e).__name__}: {e}")
        
except ImportError:
    print("[错误] akshare库未安装")
    sys.exit(1)

print("\n" + "=" * 80)
print("测试完成")
print("=" * 80)

