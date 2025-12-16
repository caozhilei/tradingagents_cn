#!/usr/bin/env python3
"""
从AKShare股票列表获取行业信息的替代方案
"""

import os
import sys
from pathlib import Path

# 清除代理环境变量
proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'NO_PROXY', 'no_proxy']
for var in proxy_vars:
    if var in os.environ:
        del os.environ[var]

print("=" * 80)
print("从AKShare股票列表获取行业信息")
print("=" * 80)

try:
    import akshare as ak
    import pandas as pd
    
    # 方法1: 尝试获取包含行业信息的股票列表
    print("\n[方法1] 尝试获取包含行业信息的股票列表...")
    try:
        # 获取A股实时行情（可能包含行业信息）
        df = ak.stock_zh_a_spot_em()
        
        if df is not None and not df.empty:
            print(f"[成功] 获取到 {len(df)} 只股票的实时行情数据")
            
            # 查看列名
            print(f"\n[信息] 数据列: {list(df.columns)}")
            
            # 查找行业相关列
            industry_cols = [col for col in df.columns if '行业' in col or 'industry' in col.lower()]
            if industry_cols:
                print(f"[成功] 找到行业列: {industry_cols}")
                
                # 测试查询几只股票
                test_codes = ['600519', '000001', '000002']
                print(f"\n[测试] 查询以下股票的行业信息:")
                for code in test_codes:
                    stock = df[df['代码'] == code]
                    if not stock.empty:
                        for col in industry_cols:
                            industry = stock.iloc[0][col]
                            name = stock.iloc[0].get('名称', '')
                            print(f"  {code} ({name}): {industry}")
            else:
                print("[提示] 此接口不包含行业信息")
            
            # 显示示例数据
            print(f"\n[示例] 前3只股票数据:")
            print(df[['代码', '名称']].head(3).to_string(index=False))
            
        else:
            print("[失败] 返回数据为空")
    except Exception as e:
        print(f"[失败] {type(e).__name__}: {e}")
    
    # 方法2: 尝试其他接口
    print("\n[方法2] 尝试其他可能包含行业信息的接口...")
    try:
        # 尝试获取行业分类数据
        industry_list = ak.stock_board_industry_name_em()
        if industry_list is not None and not industry_list.empty:
            print(f"[成功] 获取到行业分类数据，共 {len(industry_list)} 个行业")
            print("[示例] 前5个行业:")
            print(industry_list.head().to_string(index=False))
        else:
            print("[提示] 未获取到行业分类数据")
    except Exception as e:
        print(f"[提示] 此接口可能不可用: {type(e).__name__}: {e}")
    
    # 方法3: 总结可用方法
    print("\n" + "=" * 80)
    print("[总结] 可用的数据获取方法:")
    print("=" * 80)
    print("""
1. ak.stock_info_a_code_name() - 获取股票代码和名称列表 ✅ 可用
2. ak.stock_zh_a_spot_em() - 获取A股实时行情 ✅ 可用
3. ak.stock_individual_info_em() - 获取个股详细信息 ⚠️ 连接问题
4. 建议：优先使用 stock_zh_a_spot_em() 批量获取，然后查询特定股票
    """)
        
except ImportError:
    print("[错误] akshare库未安装")
    sys.exit(1)

print("\n测试完成")

