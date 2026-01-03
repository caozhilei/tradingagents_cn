#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版数字货币新闻测试脚本
直接测试 _get_crypto_news 方法，避免依赖问题
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

from datetime import datetime

# 创建一个简单的 Mock Toolkit
class MockToolkit:
    """模拟 Toolkit，用于测试"""
    
    def __init__(self):
        self.has_google_news = True
        self.has_openai_news = True
        self.has_reddit = True
    
    @property
    def get_google_news(self):
        """模拟 Google News 工具"""
        class GoogleNewsTool:
            def invoke(self, params):
                query = params.get('query', '')
                curr_date = params.get('curr_date', '')
                look_back_days = params.get('look_back_days', 7)
                
                # 模拟返回新闻
                return f"""## {query} Google News, from {curr_date}:

### Bitcoin Price Surges Above $50,000 (source: CoinDesk) 

Bitcoin has reached a new milestone, crossing the $50,000 threshold. This represents a significant recovery from recent lows...

### Ethereum 2.0 Staking Reaches New Heights (source: CryptoNews) 

The Ethereum network continues to see increased staking activity, with over 30 million ETH now staked...

### Cryptocurrency Market Analysis (source: Bloomberg) 

The cryptocurrency market shows strong momentum with major coins experiencing significant gains...
"""
        return GoogleNewsTool()
    
    @property
    def get_global_news_openai(self):
        """模拟 OpenAI 全球新闻工具"""
        class OpenAINewsTool:
            def invoke(self, params):
                curr_date = params.get('curr_date', '')
                # 模拟返回包含数字货币内容的新闻
                return f"""## Global News from OpenAI, {curr_date}:

### Major Cryptocurrency Developments

Bitcoin and Ethereum continue to dominate the cryptocurrency market. Recent developments include...

### Market Trends

The cryptocurrency sector shows strong growth potential with increasing institutional adoption...
"""
        return OpenAINewsTool()
    
    @property
    def get_reddit_stock_info(self):
        """模拟 Reddit 工具"""
        class RedditTool:
            def invoke(self, params):
                ticker = params.get('ticker', '')
                curr_date = params.get('curr_date', '')
                return f"""## {ticker} Reddit Discussion, {curr_date}:

### Top Discussion: {ticker} Price Prediction

Community members are discussing the future price trajectory of {ticker}...

### Technical Analysis

Several users have shared technical analysis charts showing potential breakout patterns...
"""
        return RedditTool()

def test_crypto_news_direct():
    """直接测试 _get_crypto_news 方法"""
    try:
        from tradingagents.tools.unified_news_tool import UnifiedNewsAnalyzer
        
        # 创建模拟工具包
        mock_toolkit = MockToolkit()
        
        # 创建统一新闻分析器
        analyzer = UnifiedNewsAnalyzer(mock_toolkit)
        
        # 测试的数字货币列表
        test_cryptos = ['BTC', 'ETH', 'DOGE']
        
        print("=" * 80)
        print("测试数字货币新闻采集功能（多源聚合）")
        print("=" * 80)
        print()
        
        for crypto_code in test_cryptos:
            print(f"\n{'='*80}")
            print(f"测试数字货币: {crypto_code}")
            print(f"{'='*80}\n")
            
            try:
                # 直接调用 _get_crypto_news 方法
                result = analyzer._get_crypto_news(
                    stock_code=crypto_code,
                    max_news=10,
                    model_info="test",
                    current_date=datetime.now().strftime("%Y-%m-%d")
                )
                
                # 显示结果
                print(f"获取成功！")
                print(f"结果长度: {len(result)} 字符")
                print(f"\n{'-'*80}")
                print("新闻内容预览（前800字符）:")
                print(f"{'-'*80}")
                print(result[:800])
                print(f"{'-'*80}")
                
                # 检查数据源
                if "Google" in result:
                    print("数据源: Google News")
                elif "OpenAI" in result:
                    print("数据源: OpenAI 全球新闻")
                elif "NewsAPI" in result:
                    print("数据源: NewsAPI")
                elif "Reddit" in result:
                    print("数据源: Reddit")
                elif "无法获取" in result or "状态" in result:
                    print("所有数据源均失败（这是正常的，因为使用了模拟工具）")
                
            except Exception as e:
                print(f"测试失败: {e}")
                import traceback
                traceback.print_exc()
            
            print()
        
        print("=" * 80)
        print("测试完成")
        print("=" * 80)
        return True
        
    except Exception as e:
        print(f"测试初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_crypto_news_direct()
    sys.exit(0 if success else 1)

