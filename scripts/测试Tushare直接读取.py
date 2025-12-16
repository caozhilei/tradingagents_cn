#!/usr/bin/env python3
"""
直接测试Tushare接口 - 从.env文件读取Token并测试
"""

import sys
import os
import re
from pathlib import Path

# 清除代理
for var in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']:
    if var in os.environ:
        del os.environ[var]

print("=" * 80)
print("直接测试Tushare接口")
print("=" * 80)

# 直接从.env文件读取Token
env_file = Path(__file__).parent.parent / ".env"
token = None

if env_file.exists():
    try:
        with open(env_file, 'r', encoding='utf-8') as f:
            content = f.read()
            # 使用正则表达式提取Token
            match = re.search(r'TUSHARE_TOKEN\s*=\s*(.+)', content, re.MULTILINE)
            if match:
                token = match.group(1).strip().strip('"\'')
                if token and not token.startswith('your_'):
                    print(f"[成功] 从.env文件读取到Token: {token[:10]}...{token[-4:] if len(token) > 14 else ''}")
                else:
                    print(f"[提示] .env文件中的Token是占位符: {token}")
                    token = None
    except Exception as e:
        print(f"[提示] 读取.env文件失败: {e}")

# 如果.env中没有，尝试从环境变量读取
if not token or token.startswith('your_'):
    token = os.getenv('TUSHARE_TOKEN')
    if token and not token.startswith('your_'):
        print(f"[成功] 从环境变量读取到Token")

if not token or token.startswith('your_'):
    print("\n[错误] 未找到有效的Tushare Token")
    print("[提示] 请检查.env文件中的TUSHARE_TOKEN配置")
    print("[提示] 如果已在系统后台配置，请确保:")
    print("  1. 系统已启动并加载了配置")
    print("  2. 或者直接在.env文件中配置TUSHARE_TOKEN=你的真实Token")
    sys.exit(1)

try:
    import tushare as ts
    print("[成功] Tushare库已安装\n")
    
    # 设置Token
    print("[设置] 初始化Tushare API...")
    ts.set_token(token)
    pro = ts.pro_api()
    print("[成功] Tushare API初始化完成\n")
    
    # 测试1: 获取单只股票
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
        
        stock = df[df['symbol'] == test_code]
        if not stock.empty:
            row = stock.iloc[0]
            print(f"[成功] 股票代码: {row['ts_code']}")
            print(f"[成功] 股票名称: {row['name']}")
            print(f"[成功] 所属行业: {row['industry']}")
            print(f"[成功] 所在地区: {row.get('area', 'N/A')}")
            print(f"[成功] 市场类型: {row.get('market', 'N/A')}")
            print(f"[成功] 上市日期: {row.get('list_date', 'N/A')}")
        else:
            print(f"[失败] 未找到股票 {test_code}")
    except Exception as e:
        error_msg = str(e)
        if "token" in error_msg.lower() or "您的token不对" in error_msg:
            print(f"[错误] Token无效: {error_msg}")
            print("[提示] 请检查Token是否正确")
            sys.exit(1)
        else:
            print(f"[失败] {type(e).__name__}: {error_msg}")
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
            total = len(df_all)
            with_industry = len(df_all[df_all['industry'].notna() & (df_all['industry'] != '')])
            
            print(f"[成功] 获取到 {total} 只股票")
            print(f"[成功] 有行业信息的股票: {with_industry} 只 ({with_industry*100//total if total > 0 else 0}%)")
            
            # 显示示例
            print(f"\n[示例] 前5只股票:")
            print(df_all[['symbol', 'name', 'industry']].head(5).to_string(index=False))
            
            # 统计行业分布
            industry_counts = df_all['industry'].value_counts()
            print(f"\n[信息] 行业数量: {len(industry_counts)} 个")
            print("[信息] 前10个行业:")
            print(industry_counts.head(10).to_string())
        else:
            print("[失败] 返回数据为空")
    except Exception as e:
        print(f"[失败] {type(e).__name__}: {e}")
    
    # 总结
    print("\n" + "=" * 80)
    print("[总结]")
    print("=" * 80)
    print("[成功] Tushare接口可用！")
    print("[结论] Tushare可以用于获取股票行业信息")
    print("[建议] 可以在主脚本中使用Tushare作为获取行业信息的可靠数据源")
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

