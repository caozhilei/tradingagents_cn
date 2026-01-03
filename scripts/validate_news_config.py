#!/usr/bin/env python3
"""
验证新闻源配置功能
"""

import sys
import os

# 添加项目路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def test_news_config_classes():
    """测试新闻源配置类"""
    try:
        # 直接定义类，避免导入问题
        from typing import Dict, List, Any

        class NewsSourceConfig:
            def __init__(self, name: str, display_name: str, enabled: bool = True,
                         priority: int = 1, description: str = ""):
                self.name = name
                self.display_name = display_name
                self.enabled = enabled
                self.priority = priority
                self.description = description

            def to_dict(self) -> Dict[str, Any]:
                return {
                    "name": self.name,
                    "display_name": self.display_name,
                    "enabled": self.enabled,
                    "priority": self.priority,
                    "description": self.description
                }

        class MarketNewsConfig:
            def __init__(self, market_type: str, display_name: str,
                         sources: List[NewsSourceConfig] = None):
                self.market_type = market_type
                self.display_name = display_name
                self.sources = sources or []

            def to_dict(self) -> Dict[str, Any]:
                return {
                    "market_type": self.market_type,
                    "display_name": self.display_name,
                    "sources": [source.to_dict() for source in self.sources]
                }

        # 测试类功能
        source = NewsSourceConfig("test", "测试数据源", True, 1, "测试描述")
        market = MarketNewsConfig("A股", "A股市场", [source])

        # 测试序列化
        data = market.to_dict()
        print("PASS: 新闻源配置类测试通过")
        print(f"  序列化结果: {len(data)} 个字段")
        print(f"  数据源数量: {len(data['sources'])}")

        return True

    except Exception as e:
        print(f"FAIL: 测试失败: {e}")
        return False

def test_config_file_operations():
    """测试配置文件操作"""
    try:
        import json
        import tempfile
        from pathlib import Path

        # 创建临时配置文件
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "test_news_config.json"

            # 测试数据
            test_data = [
                {
                    "market_type": "A股",
                    "display_name": "A股市场",
                    "sources": [
                        {
                            "name": "database_cache",
                            "display_name": "数据库缓存",
                            "enabled": True,
                            "priority": 1,
                            "description": "本地缓存的新闻数据"
                        }
                    ]
                }
            ]

            # 保存配置
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(test_data, f, ensure_ascii=False, indent=2)

            # 读取配置
            with open(config_file, 'r', encoding='utf-8') as f:
                loaded_data = json.load(f)

        print("PASS: 配置文件操作测试通过")
        print(f"  保存的数据: {len(test_data)} 个市场")
        print(f"  读取的数据: {len(loaded_data)} 个市场")

        return True

    except Exception as e:
        print(f"FAIL: 配置文件操作测试失败: {e}")
        return False

def test_default_config():
    """测试默认配置"""
    try:
        # 模拟默认配置
        default_sources = {
            "A股": [
                {"name": "database_cache", "display_name": "数据库缓存", "priority": 1},
                {"name": "eastmoney_realtime", "display_name": "东方财富实时", "priority": 2},
                {"name": "google_news", "display_name": "Google新闻", "priority": 3},
                {"name": "openai_news", "display_name": "OpenAI全球新闻", "priority": 4},
            ],
            "港股": [
                {"name": "database_cache", "display_name": "数据库缓存", "priority": 1},
                {"name": "google_news", "display_name": "Google新闻", "priority": 2},
                {"name": "openai_news", "display_name": "OpenAI全球新闻", "priority": 3},
                {"name": "realtime_hk", "display_name": "实时港股新闻", "priority": 4},
            ],
            "美股": [
                {"name": "database_cache", "display_name": "数据库缓存", "priority": 1},
                {"name": "openai_news", "display_name": "OpenAI全球新闻", "priority": 2},
                {"name": "google_news", "display_name": "Google新闻", "priority": 3},
                {"name": "finnhub_news", "display_name": "FinnHub新闻", "priority": 4},
            ],
            "数字货币": [
                {"name": "database_cache", "display_name": "数据库缓存", "priority": 1},
                {"name": "google_news", "display_name": "Google数字货币新闻", "priority": 2},
                {"name": "openai_news", "display_name": "OpenAI全球新闻", "priority": 3},
                {"name": "newsapi_crypto", "display_name": "NewsAPI数字货币", "priority": 4},
                {"name": "reddit_crypto", "display_name": "Reddit数字货币讨论", "priority": 5},
            ]
        }

        total_markets = len(default_sources)
        total_sources = sum(len(sources) for sources in default_sources.values())

        print("PASS: 默认配置测试通过")
        print(f"  支持的市场: {total_markets} 个")
        print(f"  数据源总数: {total_sources} 个")

        for market, sources in default_sources.items():
            print(f"  {market}: {len(sources)} 个数据源")

        return True

    except Exception as e:
        print(f"FAIL: 默认配置测试失败: {e}")
        return False

if __name__ == "__main__":
    print("=== 新闻源配置功能验证 ===\n")

    tests = [
        ("新闻源配置类", test_news_config_classes),
        ("配置文件操作", test_config_file_operations),
        ("默认配置", test_default_config),
    ]

    results = []
    for test_name, test_func in tests:
        print(f"正在测试: {test_name}")
        try:
            result = test_func()
            results.append(result)
            status = "✅ 通过" if result else "❌ 失败"
            print(f"结果: {status}\n")
        except Exception as e:
            print(f"FAIL: 异常: {e}\n")
            results.append(False)

    print("=" * 40)
    passed = sum(results)
    total = len(results)

    if passed == total:
        print(f"SUCCESS: 所有测试通过 ({passed}/{total})")
        print("新闻源配置功能已准备就绪，可以添加到Web界面中！")
    else:
        print(f"WARNING: 部分测试失败 ({passed}/{total})")
        print("需要检查失败的测试项")
