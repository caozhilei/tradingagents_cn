#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试通达信接口获取300476当前股价
"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from data.tdx_utils import get_tdx_provider
import traceback


def test_get_stock_price(stock_code: str):
    """测试获取股票当前股价"""
    print("=" * 80)
    print(f"🧪 测试获取股票 {stock_code} 的当前股价")
    print("=" * 80)
    print()
    
    try:
        # 获取通达信数据提供器
        print("📡 步骤1: 获取通达信数据提供器实例...")
        provider = get_tdx_provider()
        print("✅ 数据提供器获取成功")
        print()
        
        # 检查连接状态
        print("🔌 步骤2: 检查连接状态...")
        if not provider.is_connected():
            print("⚠️ 未连接，尝试连接服务器...")
            if not provider.connect():
                print("❌ 连接失败，无法继续测试")
                return False
        print("✅ 连接正常")
        print()
        
        # 获取实时数据
        print(f"📊 步骤3: 获取股票 {stock_code} 的实时数据...")
        realtime_data = provider.get_real_time_data(stock_code)
        print()
        
        if not realtime_data:
            print("❌ 未能获取到实时数据")
            return False
        
        # 显示结果
        print("=" * 80)
        print("✅ 数据获取成功！")
        print("=" * 80)
        print()
        print("📈 实时行情数据:")
        print(f"  股票代码: {realtime_data.get('code', 'N/A')}")
        print(f"  股票名称: {realtime_data.get('name', 'N/A')}")
        print(f"  当前价格: ¥{realtime_data.get('price', 0):.2f}")
        print(f"  昨收价格: ¥{realtime_data.get('last_close', 0):.2f}")
        print(f"  今日开盘: ¥{realtime_data.get('open', 0):.2f}")
        print(f"  今日最高: ¥{realtime_data.get('high', 0):.2f}")
        print(f"  今日最低: ¥{realtime_data.get('low', 0):.2f}")
        print(f"  涨跌额: ¥{realtime_data.get('change', 0):.2f}")
        print(f"  涨跌幅: {realtime_data.get('change_percent', 0):.2f}%")
        print(f"  成交量: {realtime_data.get('volume', 0):,} 手")
        print(f"  成交额: ¥{realtime_data.get('amount', 0):,.2f}")
        print(f"  更新时间: {realtime_data.get('update_time', 'N/A')}")
        print()
        
        # 显示五档买卖盘
        print("📋 五档买卖盘:")
        bid_prices = realtime_data.get('bid_prices', [])
        bid_volumes = realtime_data.get('bid_volumes', [])
        ask_prices = realtime_data.get('ask_prices', [])
        ask_volumes = realtime_data.get('ask_volumes', [])
        
        print("  卖盘:")
        for i in range(4, -1, -1):  # 从卖5到卖1
            if ask_prices and i < len(ask_prices):
                print(f"    卖{i+1}: ¥{ask_prices[i]:.2f}  {ask_volumes[i]:,}手")
        
        print(f"  ──────────── 当前价: ¥{realtime_data.get('price', 0):.2f} ────────────")
        
        print("  买盘:")
        for i in range(5):  # 从买1到买5
            if bid_prices and i < len(bid_prices):
                print(f"    买{i+1}: ¥{bid_prices[i]:.2f}  {bid_volumes[i]:,}手")
        
        print()
        print("=" * 80)
        
        # 验证数据有效性
        price = realtime_data.get('price', 0)
        if price > 0:
            print("✅ 测试通过：成功获取到有效的股价数据")
            return True
        else:
            print("⚠️ 警告：获取到的股价为0，可能数据异常")
            return False
            
    except ImportError as e:
        print("❌ 导入错误：")
        print(f"   {str(e)}")
        print()
        print("💡 解决建议:")
        print("   1. 确保已安装 pytdx 库: pip install pytdx")
        print("   2. 检查 data/tdx_utils.py 文件是否存在")
        return False
        
    except Exception as e:
        print("❌ 测试失败：")
        print(f"   错误类型: {type(e).__name__}")
        print(f"   错误信息: {str(e)}")
        print()
        print("📋 详细错误堆栈:")
        traceback.print_exc()
        return False
    
    finally:
        # 断开连接
        try:
            if 'provider' in locals():
                provider.disconnect()
                print("✅ 已断开连接")
        except:
            pass


if __name__ == "__main__":
    # 测试股票代码 300476
    stock_code = "300476"
    success = test_get_stock_price(stock_code)
    
    print()
    if success:
        print("🎉 测试完成：成功获取股价数据")
        sys.exit(0)
    else:
        print("❌ 测试完成：未能成功获取股价数据")
        sys.exit(1)

