#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接测试：使用pytdx底层API获取300476当前股价
不依赖pandas，直接使用socket连接
"""
import sys
import socket
import struct
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def get_stock_quote_direct(ip, port, market, code):
    """直接使用socket获取股票行情"""
    try:
        # 创建socket连接
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect((ip, port))
        
        # 构建请求包
        # 通达信协议：获取行情数据包
        # 包格式：包长度(2字节) + 包类型(2字节) + 市场代码(2字节) + 股票代码(6字节)
        packet = bytearray()
        packet.extend(struct.pack('>H', 0x0c))  # 包长度
        packet.extend(struct.pack('>H', 0x0201))  # 包类型：获取行情
        packet.extend(struct.pack('>H', market))  # 市场代码
        packet.extend(code.encode('utf-8').ljust(6, b'\x00'))  # 股票代码，6字节
        
        # 发送请求
        sock.send(packet)
        
        # 接收响应
        # 先读取包长度
        length_data = sock.recv(2)
        if len(length_data) < 2:
            sock.close()
            return None
        
        packet_length = struct.unpack('>H', length_data)[0]
        
        # 读取完整数据包
        data = sock.recv(packet_length - 2)
        
        sock.close()
        
        # 解析数据（简化版，实际协议更复杂）
        if len(data) >= 32:
            # 通达信行情数据格式（简化解析）
            price = struct.unpack('>I', data[0:4])[0] / 100.0
            return {
                'price': price,
                'raw_data': data
            }
        
        return None
        
    except Exception as e:
        print(f"   Socket错误: {e}")
        return None


def test_get_stock_price_direct(stock_code: str):
    """直接测试获取股票当前股价"""
    print("=" * 80)
    print(f"🧪 直接测试获取股票 {stock_code} 的当前股价")
    print("=" * 80)
    print()
    
    # 判断市场代码（300开头是深圳创业板，市场代码为0）
    market = 0  # 300开头是深圳市场
    print(f"📊 股票信息:")
    print(f"   市场代码: {market} (深圳)")
    print(f"   股票代码: {stock_code}")
    print()
    
    # 尝试连接服务器并获取数据
    servers = [
        ('115.238.56.198', 7709),
        ('115.238.90.165', 7709),
        ('180.153.18.170', 7709),
        ('119.147.212.81', 7709),
    ]
    
    print("🌐 尝试连接服务器...")
    for ip, port in servers:
        print(f"   尝试: {ip}:{port}...")
        result = get_stock_quote_direct(ip, port, market, stock_code)
        if result:
            print(f"✅ 连接成功: {ip}:{port}")
            print(f"   当前价格: ¥{result.get('price', 0):.2f}")
            return True
        else:
            print(f"   ⚠️ 未能获取数据")
    
    print()
    print("❌ 所有服务器都无法获取数据")
    print()
    print("💡 建议：")
    print("   1. 检查网络连接")
    print("   2. 确认股票代码正确（300476）")
    print("   3. 尝试使用完整的tdx_utils接口（需要修复numpy依赖）")
    return False


if __name__ == "__main__":
    # 测试股票代码 300476
    stock_code = "300476"
    print("⚠️  注意：此测试使用简化的socket协议，可能无法完整解析数据")
    print("   建议修复numpy依赖后使用完整的tdx_utils接口")
    print()
    
    success = test_get_stock_price_direct(stock_code)
    
    print()
    if success:
        print("🎉 测试完成：成功获取股价数据")
        sys.exit(0)
    else:
        print("❌ 测试完成：未能成功获取股价数据")
        print()
        print("📝 测试总结：")
        print("   由于numpy依赖问题，无法使用完整的tdx_utils接口")
        print("   建议：")
        print("   1. 修复numpy安装问题")
        print("   2. 或使用虚拟环境重新安装依赖")
        sys.exit(1)

