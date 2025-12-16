#!/usr/bin/env python3
"""
交互式测试Tushare接口 - 支持直接输入Token
"""

import sys
import os

# 清除代理
for var in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']:
    if var in os.environ:
        del os.environ[var]

print("=" * 80)
print("交互式测试Tushare接口")
print("=" * 80)

try:
    import tushare as ts
    print("[成功] Tushare库已安装\n")
    
    # 获取Token
    token = os.getenv('TUSHARE_TOKEN')
    
    # 如果环境变量中没有有效的Token，提示用户输入
    if not token or token.startswith('your_'):
        print("[提示] 未在环境变量中找到有效的Token")
        print("[提示] 请输入你的Tushare Token进行测试:")
        print("  (如果已在系统后台配置，Token应该会自动加载)")
        print("  (直接按Enter使用环境变量中的Token，如果有的话)\n")
        
        user_input = input("请输入Token (或按Enter跳过): ").strip()
        if user_input:
            token = user_input
        elif token:
            print(f"[使用] 使用环境变量中的Token")
        else:
            print("\n[错误] 未提供Token，无法继续测试")
            sys.exit(1)
    
    if token.startswith('your_'):
        print("\n[错误] Token看起来是占位符，请提供真实的Token")
        sys.exit(1)
    
    print(f"\n[使用] Token: {token[:10]}...{token[-4:] if len(token) > 14 else ''}\n")
    
    # 设置Token并测试
    print("[设置] 初始化Tushare API...")
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
        ('000002', 'SZ', '万科A'),
    ]
    
    success_count = 0
    for symbol, exchange, name in test_stocks:
        try:
            print(f"\n[查询] {symbol} ({name})...")
            df = pro.stock_basic(
                exchange='',
                list_status='L',
                fields='ts_code,symbol,name,area,industry,market,list_date'
            )
            
            stock = df[df['symbol'] == symbol]
            if not stock.empty:
                row = stock.iloc[0]
                print(f"  [成功] 股票代码: {row['ts_code']}")
                print(f"  [成功] 股票名称: {row['name']}")
                print(f"  [成功] 所属行业: {row['industry']}")
                print(f"  [成功] 所在地区: {row.get('area', 'N/A')}")
                print(f"  [成功] 市场类型: {row.get('market', 'N/A')}")
                print(f"  [成功] 上市日期: {row.get('list_date', 'N/A')}")
                success_count += 1
            else:
                print(f"  [失败] 未找到股票")
        except Exception as e:
            error_msg = str(e)
            if "token" in error_msg.lower() or "您的token不对" in error_msg:
                print(f"  [错误] Token无效: {error_msg}")
                print(f"  [提示] 请检查Token是否正确，或者Token可能已过期")
                break
            else:
                print(f"  [失败] {type(e).__name__}: {error_msg}")
                import traceback
                traceback.print_exc()
                break
    
    # 如果成功，测试批量获取
    if success_count > 0:
        print("\n" + "=" * 80)
        print("[测试] 批量获取统计")
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
                
                # 统计行业
                industry_counts = df_all['industry'].value_counts()
                print(f"\n[信息] 行业数量: {len(industry_counts)} 个")
                print("[信息] 前10个行业:")
                print(industry_counts.head(10).to_string())
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

