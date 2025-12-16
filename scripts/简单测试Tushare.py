#!/usr/bin/env python3
"""
简单测试Tushare接口 - 直接使用环境变量或手动输入Token
"""

import sys
import os

# 清除代理
for var in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']:
    if var in os.environ:
        del os.environ[var]

print("=" * 80)
print("简单测试Tushare接口")
print("=" * 80)

try:
    import tushare as ts
    print("[成功] Tushare库已安装\n")
    
    # 获取Token
    token = os.getenv('TUSHARE_TOKEN')
    
    if not token or token.startswith('your_'):
        print("[提示] 环境变量中未找到有效的Token")
        print("[提示] 如果你已在系统后台配置了Tushare，Token应该已设置")
        print("[提示] 或者你可以:")
        print("  1. 在.env文件中设置 TUSHARE_TOKEN=你的真实Token")
        print("  2. 或者直接在这里输入Token进行测试\n")
        print("请输入你的Tushare Token（直接按Enter跳过）:")
        manual_token = input().strip()
        if manual_token:
            token = manual_token
        else:
            print("\n[提示] 跳过手动输入，尝试从其他位置读取...")
            # 尝试从配置文件读取
            try:
                from pathlib import Path
                env_file = Path(__file__).parent.parent / ".env"
                if env_file.exists():
                    with open(env_file, 'r', encoding='utf-8') as f:
                        for line in f:
                            if line.startswith('TUSHARE_TOKEN='):
                                token = line.split('=', 1)[1].strip().strip('"\'')
                                if token and not token.startswith('your_'):
                                    print(f"[成功] 从.env文件读取到Token")
                                    break
            except:
                pass
    
    if not token or token.startswith('your_'):
        print("\n[错误] 未找到有效的Tushare Token")
        print("[提示] 请配置Token后重试")
        sys.exit(1)
    
    print(f"\n[成功] 使用Token: {token[:10]}...{token[-4:] if len(token) > 14 else ''}\n")
    
    # 设置Token
    ts.set_token(token)
    pro = ts.pro_api()
    print("[成功] Tushare API初始化完成\n")
    
    # 测试获取股票信息
    print("=" * 80)
    print("[测试] 获取股票行业信息")
    print("=" * 80)
    
    test_stocks = [
        ('600519', 'SH', '贵州茅台'),
        ('000001', 'SZ', '平安银行'),
    ]
    
    success_count = 0
    for symbol, exchange, name in test_stocks:
        try:
            print(f"\n[查询] {symbol} ({name})...")
            df = pro.stock_basic(
                exchange='',
                list_status='L',
                fields='ts_code,symbol,name,area,industry,market'
            )
            
            stock = df[df['symbol'] == symbol]
            if not stock.empty:
                row = stock.iloc[0]
                print(f"  [成功] 股票名称: {row['name']}")
                print(f"  [成功] 所属行业: {row['industry']}")
                print(f"  [成功] 所在地区: {row.get('area', 'N/A')}")
                success_count += 1
            else:
                print(f"  [失败] 未找到股票")
        except Exception as e:
            error_msg = str(e)
            if "token" in error_msg.lower() or "您的token不对" in error_msg:
                print(f"  [错误] Token无效: {error_msg}")
                print(f"  [提示] 请检查Token是否正确")
                break
            else:
                print(f"  [失败] {type(e).__name__}: {error_msg}")
    
    # 批量测试
    if success_count > 0:
        print("\n" + "=" * 80)
        print("[测试] 批量获取统计")
        print("=" * 80)
        
        try:
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
                
                print(f"\n[示例] 前3只股票:")
                print(df_all[['symbol', 'name', 'industry']].head(3).to_string(index=False))
        except Exception as e:
            print(f"[失败] {type(e).__name__}: {e}")
    
    # 总结
    print("\n" + "=" * 80)
    print("[总结]")
    print("=" * 80)
    if success_count > 0:
        print(f"[成功] Tushare接口可用！")
        print(f"[成功] 成功获取 {success_count}/{len(test_stocks)} 只股票信息")
        print("[结论] Tushare可以用于获取股票行业信息")
        print("[建议] 可以在主脚本中使用Tushare作为获取行业信息的可靠数据源")
    else:
        print("[失败] 未能成功获取股票信息")
        print("[提示] 请检查Token是否正确")
    print("=" * 80)
    
except ImportError:
    print("[错误] Tushare库未安装")
    print("[提示] 安装命令: pip install tushare")
    sys.exit(1)
except KeyboardInterrupt:
    print("\n\n[提示] 用户中断")
    sys.exit(1)
except Exception as e:
    print(f"[错误] 发生错误: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

