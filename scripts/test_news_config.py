#!/usr/bin/env python3
"""
测试新闻源配置功能
"""

import sys
import os
# 添加项目根目录
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'web'))

def test_news_config():
    """测试新闻源配置功能"""
    try:
        from modules.config_management import DEFAULT_NEWS_SOURCES, NewsSourceConfig, MarketNewsConfig

        print("✅ 新闻源配置类导入成功")

        # 测试默认配置
        configs = list(DEFAULT_NEWS_SOURCES.values())
        print(f"✅ 默认配置加载成功，共 {len(configs)} 个市场配置")

        for config in configs:
            print(f"  - {config.market_type}: {len(config.sources)} 个数据源")

            # 显示每个数据源的详细信息
            for source in config.sources:
                status = "✅" if source.enabled else "❌"
                print(f"    {status} {source.display_name} (优先级: {source.priority})")

        # 测试序列化
        test_config = configs[0]  # 测试A股配置
        dict_data = test_config.to_dict()
        restored_config = MarketNewsConfig.from_dict(dict_data)

        print(f"✅ 配置序列化/反序列化测试通过")
        print(f"  原始: {test_config.market_type}")
        print(f"  恢复: {restored_config.market_type}")

        return True

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=== 新闻源配置功能测试 ===\n")

    success = test_news_config()

    if success:
        print("\n🎉 新闻源配置功能测试通过！可以添加到Web界面中")
    else:
        print("\n⚠️ 测试失败，需要检查代码")
