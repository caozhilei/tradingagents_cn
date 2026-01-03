#!/usr/bin/env python3
"""
测试HTML标签清理功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
import re

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clean_html_tags(text: str) -> str:
    """清理HTML标签，特别是<em>标签"""
    if not text:
        return text

    # 移除 <em> 和 </em> 标签（只移除标签，不移除内容）
    text = re.sub(r'</?em[^>]*>', '', text, flags=re.IGNORECASE)

    # 移除其他常见的HTML标签
    text = re.sub(r'<[^>]+>', '', text)

    # 清理多余的空白字符
    text = re.sub(r'\s+', ' ', text).strip()

    return text

def test_html_cleaning():
    """测试HTML标签清理功能"""
    test_cases = [
        # 原始文本 -> 期望结果
        ("电力设备行业今日涨<em>1.4</em>%，主力资金净流入8<em>5</em>.<em>60</em>亿元",
         "电力设备行业今日涨1.4%，主力资金净流入85.60亿元"),

        ("9<em>5</em>只个股突破半年线",
         "95只个股突破半年线"),

        ("5<em>9</em>只股上午收盘涨停(附股)",
         "59只股上午收盘涨停(附股)"),

        ("<em>5</em>9只股上午收盘涨停(附股)",
         "59只股上午收盘涨停(附股)"),

        ("9<em>0</em>只股中线走稳 站上半年线",
         "90只股中线走稳 站上半年线"),

        ("42<em>9</em>只股短线走稳 站上五日均线",
         "429只股短线走稳 站上五日均线"),

        ("重磅信号来了！两大板块迎涨停潮！",
         "重磅信号来了！两大板块迎涨停潮！"),  # 无HTML标签，应该不变

        ("今日48只个股突破半年线",
         "今日48只个股突破半年线"),  # 无HTML标签，应该不变
    ]

    print("=== HTML标签清理测试 ===\n")

    all_passed = True
    for i, (input_text, expected) in enumerate(test_cases, 1):
        result = clean_html_tags(input_text)
        passed = result == expected

        print(f"测试 {i}: {'✅ 通过' if passed else '❌ 失败'}")
        print(f"  输入: {input_text}")
        print(f"  输出: {result}")
        print(f"  期望: {expected}")

        if not passed:
            all_passed = False
            print("  ⚠️  结果不匹配!")
        print()

    print("=" * 50)
    if all_passed:
        print("✅ 所有测试通过！HTML标签清理功能正常")
    else:
        print("❌ 部分测试失败，需要检查清理逻辑")

    return all_passed

def test_regex_patterns():
    """测试正则表达式模式"""
    print("\n=== 正则表达式模式测试 ===\n")

    # 测试<em>标签清理
    em_pattern = r'<em[^>]*>.*?</em>'
    test_texts = [
        '电力设备行业今日涨<em>1.4</em>%',
        '9<em>5</em>只个股突破半年线',
        '<em>5</em>9只股上午收盘涨停',
        '正常文本没有标签',
    ]

    for text in test_texts:
        cleaned = re.sub(em_pattern, '', text, flags=re.IGNORECASE | re.DOTALL)
        print(f"原始: {text}")
        print(f"清理: {cleaned}")
        print()

if __name__ == "__main__":
    success = test_html_cleaning()
    test_regex_patterns()

    if success:
        print("\n🎉 HTML标签清理功能测试完成，可以修复市场快讯的异常字符问题！")
    else:
        print("\n⚠️ 需要进一步调整清理逻辑")
