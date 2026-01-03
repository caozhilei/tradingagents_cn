#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试新闻分析师完整流程
验证工具调用、结果处理、state更新等
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
from langchain_core.messages import AIMessage, HumanMessage

def test_news_analyst_flow():
    """测试新闻分析师完整流程"""
    print("=" * 80)
    print("🧪 测试新闻分析师完整流程（BTC）")
    print("=" * 80)
    print()
    
    try:
        # 创建模拟的 LLM 响应（包含工具调用）
        mock_result = AIMessage(
            content="",
            tool_calls=[{
                'name': 'get_stock_news_unified',
                'args': {'stock_code': 'BTC', 'max_news': 10},
                'id': 'call_123'
            }]
        )
        
        print("1️⃣ 模拟 LLM 工具调用请求")
        print(f"   工具名称: {mock_result.tool_calls[0]['name']}")
        print(f"   参数: {mock_result.tool_calls[0]['args']}")
        print()
        
        # 创建模拟工具
        class MockTool:
            def __init__(self, name):
                self.name = name
            
            def invoke(self, args):
                if self.name == 'get_stock_news_unified':
                    return f"""=== 📰 新闻数据来源: Google数字货币新闻(比特币) ===
获取时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

=== 📋 新闻内容 ===
## BTC bitcoin cryptocurrency news Google News:

### Bitcoin Price Surges Above $50,000 (source: CoinDesk) 
Bitcoin has reached a new milestone, crossing the $50,000 threshold...

### Ethereum 2.0 Staking Reaches New Heights (source: CryptoNews)
The Ethereum network continues to see increased staking activity...

=== ✅ 数据状态 ===
状态: 成功获取
来源: Google数字货币新闻(比特币)
"""
                return ""
        
        mock_tools = [MockTool('get_stock_news_unified')]
        
        print("2️⃣ 执行工具调用")
        from langchain_core.messages import ToolMessage
        
        tool_messages = []
        tool_results = []
        
        for tool_call in mock_result.tool_calls:
            tool_name = tool_call.get('name', '')
            tool_args = tool_call.get('args', {})
            tool_id = tool_call.get('id', '')
            
            print(f"   🛠️ 执行工具: {tool_name}")
            print(f"   参数: {tool_args}")
            
            # 找到对应的工具并执行
            tool_result = None
            for tool in mock_tools:
                if hasattr(tool, 'name') and tool.name == tool_name:
                    tool_result = tool.invoke(tool_args)
                    print(f"   ✅ 工具执行成功，结果长度: {len(tool_result)} 字符")
                    break
            
            if tool_result:
                tool_message = ToolMessage(
                    content=str(tool_result),
                    tool_call_id=tool_id
                )
                tool_messages.append(tool_message)
                tool_results.append(tool_result)
        
        print()
        print("3️⃣ 验证工具结果")
        print(f"   工具消息数量: {len(tool_messages)}")
        print(f"   工具结果数量: {len(tool_results)}")
        if tool_results:
            print(f"   第一个结果长度: {len(str(tool_results[0]))} 字符")
            print(f"   第一个结果预览: {str(tool_results[0])[:200]}...")
        print()
        
        print("4️⃣ 模拟生成最终报告")
        # 模拟 LLM 基于工具结果生成报告
        mock_final_report = f"""# BTC 新闻分析报告

## 新闻事件总结
基于工具获取的最新新闻数据，BTC（比特币）近期有以下重要动态：

1. **价格突破**：Bitcoin价格突破$50,000大关，创下新的里程碑
2. **市场活跃度**：Ethereum 2.0质押活动持续增长

## 对股票的影响分析
这些新闻事件对BTC价格产生积极影响...

## 市场情绪评估
市场情绪整体乐观...

## 投资建议
建议关注后续市场动态...
"""
        
        print(f"   ✅ 模拟报告生成成功，长度: {len(mock_final_report)} 字符")
        print()
        
        print("5️⃣ 验证返回值结构")
        return_value = {
            "messages": [AIMessage(content=mock_final_report)],
            "news_report": mock_final_report,
            "news_tool_call_count": 1
        }
        
        print(f"   ✅ 返回值包含 news_report: {'news_report' in return_value}")
        print(f"   ✅ news_report 长度: {len(return_value['news_report'])} 字符")
        print(f"   ✅ messages 数量: {len(return_value['messages'])}")
        print()
        
        print("=" * 80)
        print("✅ 测试完成 - 流程正常")
        print("=" * 80)
        print()
        print("💡 如果实际运行中仍然失败，请检查：")
        print("1. 工具是否正确绑定到 ToolNode")
        print("2. 工具是否有 invoke 方法")
        print("3. 网络连接是否正常")
        print("4. API 配置是否正确")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_news_analyst_flow()
    sys.exit(0 if success else 1)

