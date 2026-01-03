"""
测试提示词模板API
"""

import requests
import json
from typing import Optional

BASE_URL = "http://localhost:8000"

# 测试用的认证token（需要替换为实际token）
AUTH_TOKEN: Optional[str] = None


def get_headers():
    """获取请求头"""
    headers = {"Content-Type": "application/json"}
    if AUTH_TOKEN:
        headers["Authorization"] = f"Bearer {AUTH_TOKEN}"
    return headers


def test_get_agent_types():
    """测试获取智能体类型"""
    print("\n=== 测试获取智能体类型 ===")
    response = requests.get(f"{BASE_URL}/api/prompt-templates/agents", headers=get_headers())
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"智能体类型: {json.dumps(data, indent=2, ensure_ascii=False)}")
    else:
        print(f"错误: {response.text}")
    return response.status_code == 200


def test_create_template():
    """测试创建模板"""
    print("\n=== 测试创建模板 ===")
    template_data = {
        "agent_type": "fundamentals_analyst",
        "agent_name": "基本面分析师",
        "template_name": "test_template",
        "template_display_name": "测试模板",
        "description": "这是一个测试模板",
        "content": {
            "system_prompt": "你是一位专业的股票基本面分析师。\n任务：分析{company_name}（股票代码：{ticker}）\n\n请使用{currency_name}{currency_symbol}作为货币单位。"
        },
        "tags": ["test", "fundamentals"],
        "is_default": False
    }
    
    response = requests.post(
        f"{BASE_URL}/api/prompt-templates",
        headers=get_headers(),
        json=template_data
    )
    print(f"状态码: {response.status_code}")
    if response.status_code == 201:
        data = response.json()
        print(f"创建的模板ID: {data.get('id')}")
        return data.get('id')
    else:
        print(f"错误: {response.text}")
    return None


def test_list_templates(agent_type: str = "fundamentals_analyst"):
    """测试列出模板"""
    print(f"\n=== 测试列出模板 (agent_type={agent_type}) ===")
    response = requests.get(
        f"{BASE_URL}/api/prompt-templates",
        headers=get_headers(),
        params={"agent_type": agent_type}
    )
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        templates = response.json()
        print(f"模板数量: {len(templates)}")
        for template in templates:
            print(f"  - {template.get('template_display_name')} ({template.get('template_name')})")
    else:
        print(f"错误: {response.text}")
    return response.status_code == 200


def test_get_template(template_id: str):
    """测试获取模板详情"""
    print(f"\n=== 测试获取模板详情 (id={template_id}) ===")
    response = requests.get(
        f"{BASE_URL}/api/prompt-templates/{template_id}",
        headers=get_headers()
    )
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"模板名称: {data.get('template_display_name')}")
        print(f"系统提示词: {data.get('content', {}).get('system_prompt', '')[:100]}...")
    else:
        print(f"错误: {response.text}")
    return response.status_code == 200


def test_get_default_template(agent_type: str = "fundamentals_analyst"):
    """测试获取默认模板"""
    print(f"\n=== 测试获取默认模板 (agent_type={agent_type}) ===")
    response = requests.get(
        f"{BASE_URL}/api/prompt-templates/agent/{agent_type}/default",
        headers=get_headers()
    )
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"默认模板: {data.get('template_display_name')}")
    else:
        print(f"错误: {response.text} (可能没有默认模板)")
    return response.status_code == 200


def main():
    """运行所有测试"""
    print("=" * 60)
    print("提示词模板API测试")
    print("=" * 60)
    
    # 测试1: 获取智能体类型
    if not test_get_agent_types():
        print("❌ 获取智能体类型失败")
        return
    
    # 测试2: 列出模板（可能为空）
    test_list_templates()
    
    # 测试3: 获取默认模板（可能不存在）
    test_get_default_template()
    
    # 测试4: 创建模板（需要认证）
    if AUTH_TOKEN:
        template_id = test_create_template()
        if template_id:
            # 测试5: 获取创建的模板
            test_get_template(template_id)
            # 测试6: 再次列出模板
            test_list_templates()
    else:
        print("\n⚠️  未提供认证token，跳过需要认证的测试")
        print("   请设置 AUTH_TOKEN 变量以测试创建模板等功能")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)


if __name__ == "__main__":
    # 如果需要测试需要认证的接口，请设置AUTH_TOKEN
    # AUTH_TOKEN = "your_token_here"
    main()

