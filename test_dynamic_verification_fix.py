#!/usr/bin/env python3
"""
测试动态验证修复
验证 _run_analysis_sync 方法中使用 request.get_symbol() 而不是 validation_result.stock_name
"""

import sys
import os
import traceback
from unittest.mock import MagicMock, patch

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)


def test_dynamic_verification_fix():
    """测试动态验证修复"""
    print("🧪 测试动态验证修复...")
    
    try:
        # 导入所需模块
        from app.services.simple_analysis_service import SimpleAnalysisService
        
        # 创建模拟请求对象
        mock_request = MagicMock()
        mock_request.get_symbol.return_value = "AAPL"
        mock_request.stock_code = "AAPL"
        mock_request.parameters = MagicMock()
        mock_request.parameters.market_type = "美股"
        mock_request.parameters.analysis_date = "2025-01-03"
        mock_request.parameters.selected_analysts = ["market"]
        mock_request.parameters.research_depth = "标准"
        
        # 创建模拟进度跟踪器
        mock_progress_tracker = MagicMock()
        mock_progress_tracker.progress_data = {"progress_percentage": 0}
        
        # 创建模拟TradingAgentsGraph
        mock_trading_graph = MagicMock()
        mock_trading_graph.propagate.return_value = ({}, {"action": "buy", "confidence": 0.75})
        
        # 创建服务实例
        service = SimpleAnalysisService()
        
        # 模拟配置
        mock_config = {
            "selected_analysts": ["market"],
            "debug": True,
            "llm_provider": "dashscope",
            "quick_think_llm": "qwen-plus",
            "deep_think_llm": "qwen-plus"
        }
        
        # 补丁导入的模块和方法
        with patch('app.services.simple_analysis_service.TradingAgentsGraph', return_value=mock_trading_graph):
            with patch('app.services.simple_analysis_service.get_default_workflow_config_sync', return_value=None):
                with patch('app.services.simple_analysis_service.update_progress_sync', return_value=None):
                    # 调用 _run_analysis_sync 方法
                    result = service._run_analysis_sync(
                        task_id="test-task-123",
                        user_id="test-user",
                        request=mock_request,
                        config=mock_config,
                        progress_tracker=mock_progress_tracker
                    )
        
        print("✅ _run_analysis_sync 方法执行成功！")
        print(f"   返回结果: {result}")
        
        # 验证 trading_graph.propagate 被正确调用
        mock_trading_graph.propagate.assert_called_once()
        called_args = mock_trading_graph.propagate.call_args
        print(f"   调用参数: symbol={called_args[0][0]}, date={called_args[0][1]}")
        
        # 验证使用了 request.get_symbol() 而不是 validation_result.stock_name
        assert called_args[0][0] == "AAPL", f"期望使用 'AAPL' 作为股票代码，实际使用了 '{called_args[0][0]}'"
        
        print("🎉 动态验证修复测试通过！")
        print("   修复确认: _run_analysis_sync 方法使用 request.get_symbol() 而不是 validation_result.stock_name")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        print(traceback.format_exc())
        return False


def main():
    """运行测试"""
    print("🔧 动态验证修复测试")
    print("=" * 40)
    
    if test_dynamic_verification_fix():
        print("\n✅ 修复验证成功！")
        sys.exit(0)
    else:
        print("\n❌ 修复验证失败！")
        sys.exit(1)


if __name__ == "__main__":
    main()
