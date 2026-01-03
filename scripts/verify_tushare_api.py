#!/usr/bin/env python3
"""
基于 .env 配置验证 Tushare 接口可用性
"""
import os
import sys
from datetime import datetime, timedelta

def load_env_config():
    """加载环境变量配置"""
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
    
    token = os.getenv('TUSHARE_TOKEN', '')
    enabled = os.getenv('TUSHARE_ENABLED', 'false').lower() == 'true'
    
    return token, enabled

def verify_tushare_api(token: str):
    """验证 Tushare API 可用性"""
    print("=" * 80)
    print("Tushare API 接口可用性验证")
    print("=" * 80)
    print()
    
    # 1. 检查 Token
    if not token:
        print("❌ TUSHARE_TOKEN 未配置")
        return False
    
    print(f"✅ TUSHARE_TOKEN 已配置 (长度: {len(token)})")
    print(f"   Token 前10位: {token[:10]}...")
    print()
    
    # 2. 测试导入
    try:
        import tushare as ts
        version = ts.__version__ if hasattr(ts, '__version__') else 'unknown'
        print(f"✅ tushare 库已安装 (版本: {version})")
    except ImportError as e:
        print(f"❌ tushare 库未安装: {e}")
        return False
    
    # 3. 设置 Token 并创建 API 对象
    try:
        ts.set_token(token)
        pro = ts.pro_api()
        print("✅ Tushare API 对象创建成功")
        print(f"   API 类型: {type(pro).__name__}")
    except Exception as e:
        print(f"❌ 创建 API 对象失败: {e}")
        return False
    
    print()
    print("-" * 80)
    print("开始测试 API 接口...")
    print("-" * 80)
    print()
    
    # 4. 测试多个 API 接口
    test_results = []
    
    # 测试 1: trade_cal (交易日历) - 根据官方文档使用空字符串 exchange
    print("测试 1: trade_cal (交易日历)")
    print("  参数: exchange='', is_open='1' (获取交易日)")
    try:
        today = datetime.now()
        start_date = (today - timedelta(days=30)).strftime('%Y%m%d')
        end_date = today.strftime('%Y%m%d')
        df = pro.trade_cal(exchange='', start_date=start_date, end_date=end_date, is_open='1')
        
        if df is not None and len(df) > 0:
            print(f"   ✅ 成功: 返回 {len(df)} 条交易日数据")
            print(f"   📊 日期范围: {df['cal_date'].min()} 至 {df['cal_date'].max()}")
            test_results.append(("trade_cal", True, len(df)))
        else:
            print(f"   ⚠️  返回空数据")
            # 尝试不指定 is_open
            df2 = pro.trade_cal(exchange='', start_date=start_date, end_date=end_date)
            if df2 is not None and len(df2) > 0:
                print(f"   ✅ 不指定 is_open 成功: 返回 {len(df2)} 条数据")
                test_results.append(("trade_cal", True, len(df2)))
            else:
                print(f"   ❌ 所有尝试都返回空数据")
                test_results.append(("trade_cal", False, 0))
    except Exception as e:
        print(f"   ❌ 调用失败: {e}")
        test_results.append(("trade_cal", False, 0))
    
    print()
    
    # 测试 2: stock_basic (股票基本信息)
    print("测试 2: stock_basic (股票基本信息)")
    print("  参数: list_status='L' (上市), limit=10")
    try:
        df = pro.stock_basic(list_status='L', limit=10)
        
        if df is not None and len(df) > 0:
            print(f"   ✅ 成功: 返回 {len(df)} 条股票数据")
            print(f"   📊 示例股票: {df.iloc[0]['ts_code']} - {df.iloc[0]['name']}")
            test_results.append(("stock_basic", True, len(df)))
        else:
            print(f"   ⚠️  返回空数据")
            test_results.append(("stock_basic", False, 0))
    except Exception as e:
        print(f"   ❌ 调用失败: {e}")
        test_results.append(("stock_basic", False, 0))
    
    print()
    
    # 测试 3: daily (日线行情) - 使用平安银行作为测试
    print("测试 3: daily (日线行情)")
    print("  参数: ts_code='000001.SZ' (平安银行), 最近10天")
    try:
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=10)).strftime('%Y%m%d')
        df = pro.daily(ts_code='000001.SZ', start_date=start_date, end_date=end_date)
        
        if df is not None and len(df) > 0:
            print(f"   ✅ 成功: 返回 {len(df)} 条日线数据")
            print(f"   📊 最新收盘价: {df.iloc[0]['close']:.2f} (日期: {df.iloc[0]['trade_date']})")
            test_results.append(("daily", True, len(df)))
        else:
            print(f"   ⚠️  返回空数据")
            test_results.append(("daily", False, 0))
    except Exception as e:
        print(f"   ❌ 调用失败: {e}")
        test_results.append(("daily", False, 0))
    
    print()
    print("=" * 80)
    print("测试结果汇总")
    print("=" * 80)
    
    success_count = sum(1 for _, success, _ in test_results if success)
    total_count = len(test_results)
    
    for api_name, success, count in test_results:
        status = "✅ 成功" if success else "❌ 失败"
        print(f"{api_name:20s} {status:10s} (数据条数: {count})")
    
    print()
    print(f"总体结果: {success_count}/{total_count} 个接口测试成功")
    
    if success_count == 0:
        print()
        print("❌ 所有接口测试失败，可能的原因：")
        print("   1. Token 无效或已过期")
        print("   2. Token 权限不足（需要积分或特定权限）")
        print("   3. 网络连接问题（需要代理）")
        print("   4. Tushare 服务暂时不可用")
        print()
        print("💡 建议：")
        print("   1. 检查 Token 是否有效：https://tushare.pro/user/index")
        print("   2. 检查 Token 积分和权限")
        print("   3. 检查网络连接和代理设置")
        return False
    elif success_count < total_count:
        print()
        print("⚠️  部分接口测试失败，可能是权限或参数问题")
        return True
    else:
        print()
        print("✅ 所有接口测试成功，Tushare API 可用")
        return True

def main():
    """主函数"""
    token, enabled = load_env_config()
    
    print(f"TUSHARE_ENABLED: {enabled}")
    print()
    
    if not enabled:
        print("⚠️  TUSHARE_ENABLED 为 false，但将继续测试接口可用性")
        print()
    
    success = verify_tushare_api(token)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()

