#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试数字货币新闻采集功能（多源聚合）

测试步骤：
1. 测试主要数字货币（BTC、ETH）的新闻获取
2. 验证多源聚合功能
3. 检查各个数据源的可用性
"""

import sys
import os

# 修复 Windows 编码问题
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

import logging
from datetime import datetime

# 配置日志（禁用可能导致编码错误的日志）
logging.basicConfig(
    level=logging.WARNING,  # 降低日志级别，避免编码错误
    format='%(asctime)s | %(levelname)s | %(name)s | %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def test_crypto_news():
    """测试数字货币新闻获取"""
    try:
        from tradingagents.tools.unified_news_tool import UnifiedNewsAnalyzer
        from tradingagents.agents.utils.agent_utils import Toolkit
        
        # 创建工具包
        toolkit = Toolkit()
        
        # 创建统一新闻分析器
        analyzer = UnifiedNewsAnalyzer(toolkit)
        
        # 测试的数字货币列表
        test_cryptos = ['BTC', 'ETH', 'DOGE']
        
        print("=" * 80)
        print("🧪 数字货币新闻采集功能测试（多源聚合）")
        print("=" * 80)
        print()
        
        for crypto_code in test_cryptos:
            print(f"\n{'='*80}")
            print(f"📰 测试数字货币: {crypto_code}")
            print(f"{'='*80}\n")
            
            try:
                # 获取新闻
                result = analyzer.get_stock_news_unified(
                    stock_code=crypto_code,
                    max_news=10,
                    model_info="test",
                    current_date=datetime.now().strftime("%Y-%m-%d")
                )
                
                # 显示结果
                print(f"✅ 获取成功！")
                print(f"📊 结果长度: {len(result)} 字符")
                print(f"\n{'─'*80}")
                print("📋 新闻内容预览（前500字符）:")
                print(f"{'─'*80}")
                print(result[:500])
                print(f"{'─'*80}")
                
                # 检查数据源
                if "Google" in result:
                    print("✅ 数据源: Google News")
                elif "OpenAI" in result:
                    print("✅ 数据源: OpenAI 全球新闻")
                elif "NewsAPI" in result:
                    print("✅ 数据源: NewsAPI")
                elif "Reddit" in result:
                    print("✅ 数据源: Reddit")
                elif "无法获取" in result or "❌" in result:
                    print("❌ 所有数据源均失败")
                
            except Exception as e:
                print(f"❌ 测试失败: {e}")
                import traceback
                traceback.print_exc()
            
            print()
        
        print("=" * 80)
        print("✅ 测试完成")
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ 测试初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = test_crypto_news()
    sys.exit(0 if success else 1)

