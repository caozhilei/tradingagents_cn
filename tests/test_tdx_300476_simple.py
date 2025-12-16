#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版测试：测试通达信接口获取300476当前股价
只测试核心功能，避免依赖问题
"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_get_stock_price_simple(stock_code: str):
    """简化版测试获取股票当前股价"""
    print("=" * 80)
    print(f"🧪 测试获取股票 {stock_code} 的当前股价（简化版）")
    print("=" * 80)
    print()
    
    try:
        # 直接导入pytdx库测试
        print("📡 步骤1: 检查pytdx库...")
        try:
            from pytdx.hq import TdxHq_API
            print("✅ pytdx库可用")
        except ImportError:
            print("❌ pytdx库未安装")
            print("💡 安装命令: pip install pytdx")
            return False
        print()
        
        # 创建API实例
        print("🔌 步骤2: 创建通达信API实例...")
        api = TdxHq_API()
        print("✅ API实例创建成功")
        print()
        
        # 尝试连接服务器
        print("🌐 步骤3: 连接通达信服务器...")
        servers = [
            ('115.238.56.198', 7709),
            ('115.238.90.165', 7709),
            ('180.153.18.170', 7709),
            ('119.147.212.81', 7709),
        ]
        
        connected = False
        for ip, port in servers:
            try:
                print(f"   尝试连接: {ip}:{port}...")
                result = api.connect(ip, port)
                if result:
                    print(f"✅ 连接成功: {ip}:{port}")
                    connected = True
                    break
                else:
                    print(f"   ⚠️ 连接失败: {ip}:{port}")
            except Exception as e:
                print(f"   ❌ 连接异常: {ip}:{port} - {e}")
                continue
        
        if not connected:
            print("❌ 所有服务器连接失败")
            return False
        print()
        
        # 判断市场代码（300开头是深圳创业板，市场代码为0）
        print(f"📊 步骤4: 获取股票 {stock_code} 的实时数据...")
        market = 0  # 300开头是深圳市场
        print(f"   市场代码: {market} (深圳)")
        print(f"   股票代码: {stock_code}")
        print()
        
        # 获取实时行情
        try:
            data = api.get_security_quotes([(market, stock_code)])
            
            if not data or len(data) == 0:
                print("❌ 未能获取到数据")
                return False
            
            quote = data[0]
            print("✅ 数据获取成功！")
            print()
            
            # 显示结果
            print("=" * 80)
            print("📈 实时行情数据:")
            print("=" * 80)
            
            # 安全获取字段
            def safe_get(key, default=0):
                return quote.get(key, default) if isinstance(quote, dict) else getattr(quote, key, default)
            
            price = safe_get('price', 0)
            last_close = safe_get('last_close', 0)
            open_price = safe_get('open', 0)
            high = safe_get('high', 0)
            low = safe_get('low', 0)
            volume = safe_get('vol', 0)
            amount = safe_get('amount', 0)
            
            change = price - last_close if last_close > 0 else 0
            change_percent = (change / last_close * 100) if last_close > 0 else 0
            
            print(f"  股票代码: {stock_code}")
            print(f"  当前价格: ¥{price:.2f}")
            print(f"  昨收价格: ¥{last_close:.2f}")
            print(f"  今日开盘: ¥{open_price:.2f}")
            print(f"  今日最高: ¥{high:.2f}")
            print(f"  今日最低: ¥{low:.2f}")
            print(f"  涨跌额: ¥{change:.2f}")
            print(f"  涨跌幅: {change_percent:.2f}%")
            print(f"  成交量: {volume:,} 手")
            print(f"  成交额: ¥{amount:,.2f}")
            print()
            
            # 显示五档买卖盘
            print("📋 五档买卖盘:")
            print("  卖盘:")
            for i in range(5, 0, -1):  # 从卖5到卖1
                ask_price = safe_get(f'ask{i}', 0)
                ask_vol = safe_get(f'ask_vol{i}', 0)
                if ask_price > 0:
                    print(f"    卖{i}: ¥{ask_price:.2f}  {ask_vol:,}手")
            
            print(f"  ──────────── 当前价: ¥{price:.2f} ────────────")
            
            print("  买盘:")
            for i in range(1, 6):  # 从买1到买5
                bid_price = safe_get(f'bid{i}', 0)
                bid_vol = safe_get(f'bid_vol{i}', 0)
                if bid_price > 0:
                    print(f"    买{i}: ¥{bid_price:.2f}  {bid_vol:,}手")
            
            print()
            print("=" * 80)
            
            # 显示原始数据（用于调试）
            print("\n🔍 原始数据（调试用）:")
            if isinstance(quote, dict):
                for key, value in quote.items():
                    print(f"  {key}: {value}")
            else:
                print(f"  数据类型: {type(quote)}")
                print(f"  数据内容: {quote}")
            
            print()
            
            # 验证数据有效性
            if price > 0:
                print("✅ 测试通过：成功获取到有效的股价数据")
                api.disconnect()
                return True
            else:
                print("⚠️ 警告：获取到的股价为0，可能数据异常")
                api.disconnect()
                return False
                
        except Exception as e:
            print(f"❌ 获取数据失败: {e}")
            import traceback
            traceback.print_exc()
            api.disconnect()
            return False
            
    except Exception as e:
        print("❌ 测试失败：")
        print(f"   错误类型: {type(e).__name__}")
        print(f"   错误信息: {str(e)}")
        print()
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # 测试股票代码 300476
    stock_code = "300476"
    success = test_get_stock_price_simple(stock_code)
    
    print()
    if success:
        print("🎉 测试完成：成功获取股价数据")
        sys.exit(0)
    else:
        print("❌ 测试完成：未能成功获取股价数据")
        sys.exit(1)

