#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
诊断新闻分析师问题
检查工具调用、返回值、state更新等
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

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(name)s | %(message)s'
)
logger = logging.getLogger(__name__)

def diagnose_news_analyst():
    """诊断新闻分析师问题"""
    print("=" * 80)
    print("🔍 新闻分析师诊断工具")
    print("=" * 80)
    print()
    
    # 1. 检查代码是否已更新
    print("1️⃣ 检查代码是否已更新...")
    try:
        import inspect
        from tradingagents.agents.analysts import news_analyst
        
        source = inspect.getsource(news_analyst.create_news_analyst)
        
        has_tool_execution = "检测到工具调用，开始执行工具" in source
        has_toolmessage = "ToolMessage" in source
        has_news_report = "news_report" in source
        
        print(f"   ✅ 包含工具执行逻辑: {has_tool_execution}")
        print(f"   ✅ 包含ToolMessage: {has_toolmessage}")
        print(f"   ✅ 包含news_report返回: {has_news_report}")
        
        if not (has_tool_execution and has_toolmessage):
            print("   ⚠️ 代码可能未更新，请重启后端服务")
        
    except Exception as e:
        print(f"   ❌ 检查失败: {e}")
    
    print()
    
    # 2. 检查统一新闻工具
    print("2️⃣ 检查统一新闻工具...")
    try:
        from tradingagents.tools.unified_news_tool import UnifiedNewsAnalyzer
        
        source = inspect.getsource(UnifiedNewsAnalyzer._get_crypto_news)
        has_multi_source = "优先级1" in source and "优先级2" in source
        
        print(f"   ✅ 包含多源聚合逻辑: {has_multi_source}")
        
        if not has_multi_source:
            print("   ⚠️ 数字货币新闻功能可能未实现")
        
    except Exception as e:
        print(f"   ❌ 检查失败: {e}")
    
    print()
    
    # 3. 检查工具包
    print("3️⃣ 检查工具包...")
    try:
        from tradingagents.agents.utils.agent_utils import Toolkit
        
        toolkit = Toolkit()
        
        has_google_news = hasattr(toolkit, 'get_google_news')
        has_openai_news = hasattr(toolkit, 'get_global_news_openai')
        has_reddit = hasattr(toolkit, 'get_reddit_stock_info')
        
        print(f"   ✅ get_google_news: {has_google_news}")
        print(f"   ✅ get_global_news_openai: {has_openai_news}")
        print(f"   ✅ get_reddit_stock_info: {has_reddit}")
        
    except Exception as e:
        print(f"   ❌ 检查失败: {e}")
    
    print()
    
    # 4. 检查环境变量
    print("4️⃣ 检查环境变量...")
    newsapi_key = os.getenv('NEWSAPI_KEY')
    print(f"   NEWSAPI_KEY: {'已配置' if newsapi_key else '未配置'}")
    
    print()
    
    # 5. 测试数字货币识别
    print("5️⃣ 测试数字货币识别...")
    try:
        from tradingagents.tools.unified_news_tool import UnifiedNewsAnalyzer
        
        analyzer = UnifiedNewsAnalyzer(None)  # 不需要toolkit来测试识别
        
        test_codes = ['BTC', 'ETH', 'DOGE']
        for code in test_codes:
            stock_type = analyzer._identify_stock_type(code)
            print(f"   {code} -> {stock_type}")
            if stock_type != "数字货币":
                print(f"      ⚠️ 识别错误！应该是'数字货币'")
    
    except Exception as e:
        print(f"   ❌ 测试失败: {e}")
    
    print()
    print("=" * 80)
    print("✅ 诊断完成")
    print("=" * 80)
    print()
    print("💡 建议：")
    print("1. 如果代码未更新，请重启后端服务：docker-compose restart backend")
    print("2. 如果工具包缺少方法，检查 agent_utils.py")
    print("3. 查看实际日志：docker-compose logs backend --tail 200 | Select-String -Pattern '新闻分析师|工具调用|BTC'")

if __name__ == "__main__":
    diagnose_news_analyst()

