#!/usr/bin/env python3
"""
快速测试Tushare Token是否有效
"""

import sys
import os

# 清除代理
for var in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']:
    if var in os.environ:
        del os.environ[var]

print("=" * 80)
print("快速测试Tushare Token")
print("=" * 80)

# 尝试多种方式获取Token
token = None
sources = []

# 方法1: 环境变量
env_token = os.getenv('TUSHARE_TOKEN')
if env_token and not env_token.startswith('your_'):
    token = env_token
    sources.append('环境变量')

# 方法2: 从.env文件读取
if not token or token.startswith('your_'):
    try:
        from pathlib import Path
        import re
        env_file = Path(__file__).parent.parent / ".env"
        if env_file.exists():
            with open(env_file, 'r', encoding='utf-8') as f:
                content = f.read()
                match = re.search(r'TUSHARE_TOKEN\s*=\s*(.+)', content, re.MULTILINE)
                if match:
                    file_token = match.group(1).strip().strip('"\'')
                    if file_token and not file_token.startswith('your_'):
                        token = file_token
                        sources.append('.env文件')
    except:
        pass

print(f"\n[信息] Token来源: {', '.join(sources) if sources else '未找到'}")
if token:
    print(f"[信息] Token长度: {len(token)} 字符")
    print(f"[信息] Token前缀: {token[:10]}...")
else:
    print("[错误] 未找到有效的Token")
    print("[提示] 如果已在系统后台配置，请确保系统正在运行")
    sys.exit(1)

try:
    import tushare as ts
    
    print(f"\n[测试] 使用Token初始化Tushare API...")
    ts.set_token(token)
    pro = ts.pro_api()
    
    # 快速测试：获取单只股票
    print("[测试] 获取股票 600519 的信息...")
    df = pro.stock_basic(
        exchange='',
        list_status='L',
        fields='ts_code,symbol,name,area,industry,market'
    )
    
    stock = df[df['symbol'] == '600519']
    if not stock.empty:
        row = stock.iloc[0]
        print(f"\n[成功] Token有效！")
        print(f"  股票名称: {row['name']}")
        print(f"  所属行业: {row['industry']}")
        print(f"  所在地区: {row.get('area', 'N/A')}")
        print(f"\n[结论] Tushare接口可用，可以获取行业信息")
    else:
        print("[失败] 未找到测试股票")
        
except Exception as e:
    error_msg = str(e)
    if "token" in error_msg.lower() or "您的token不对" in error_msg:
        print(f"\n[错误] Token无效: {error_msg}")
        print("[提示] 请检查Token是否正确")
    else:
        print(f"\n[错误] {type(e).__name__}: {error_msg}")

