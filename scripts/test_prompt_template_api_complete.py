"""
完整的提示词模板API测试脚本
测试所有API端点功能
"""

import sys
import requests
import json
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/prompt-templates"

def print_section(title):
    """打印章节标题"""
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)

def print_result(test_name, success, message=""):
    """打印测试结果"""
    status = "[OK]" if success else "[FAIL]"
    print(f"{status} {test_name}")
    if message:
        print(f"    {message}")

def test_get_agent_types():
    """测试获取智能体类型"""
    print_section("测试1: 获取智能体类型")
    try:
        response = requests.get(f"{API_BASE}/agents", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print_result("获取智能体类型", True, f"找到 {len(data)} 个分类")
            for category, agents in data.items():
                print(f"  - {category}: {len(agents)} 个智能体")
                for agent in agents[:3]:  # 只显示前3个
                    print(f"    * {agent.get('name', 'N/A')} ({agent.get('type', 'N/A')})")
            return True, data
        else:
            print_result("获取智能体类型", False, f"HTTP {response.status_code}: {response.text}")
            return False, None
    except Exception as e:
        print_result("获取智能体类型", False, str(e))
        return False, None

def test_list_templates(agent_type="fundamentals_analyst"):
    """测试获取模板列表"""
    print_section(f"测试2: 获取模板列表 (agent_type={agent_type})")
    try:
        response = requests.get(f"{API_BASE}?agent_type={agent_type}", timeout=10)
        if response.status_code == 200:
            data = response.json()
            templates = data if isinstance(data, list) else data.get('items', [])
            print_result("获取模板列表", True, f"找到 {len(templates)} 个模板")
            for template in templates[:3]:  # 只显示前3个
                template_id = template.get('id') or template.get('_id', 'N/A')
                name = template.get('template_display_name', 'N/A')
                is_default = template.get('is_default', False)
                print(f"  - {name} (ID: {template_id}, 默认: {is_default})")
            return True, templates
        else:
            print_result("获取模板列表", False, f"HTTP {response.status_code}: {response.text}")
            return False, None
    except Exception as e:
        print_result("获取模板列表", False, str(e))
        return False, None

def test_get_template(template_id):
    """测试获取单个模板"""
    print_section(f"测试3: 获取模板详情 (ID: {template_id})")
    try:
        response = requests.get(f"{API_BASE}/{template_id}", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print_result("获取模板详情", True)
            print(f"  模板名称: {data.get('template_display_name', 'N/A')}")
            print(f"  智能体类型: {data.get('agent_type', 'N/A')}")
            print(f"  版本: {data.get('version', 'N/A')}")
            print(f"  是否默认: {data.get('is_default', False)}")
            print(f"  是否系统: {data.get('is_system', False)}")
            return True, data
        else:
            print_result("获取模板详情", False, f"HTTP {response.status_code}: {response.text}")
            return False, None
    except Exception as e:
        print_result("获取模板详情", False, str(e))
        return False, None

def test_get_default_template(agent_type="fundamentals_analyst"):
    """测试获取默认模板"""
    print_section(f"测试4: 获取默认模板 (agent_type={agent_type})")
    try:
        response = requests.get(f"{API_BASE}/default/{agent_type}", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print_result("获取默认模板", True)
            print(f"  模板名称: {data.get('template_display_name', 'N/A')}")
            return True, data
        else:
            print_result("获取默认模板", False, f"HTTP {response.status_code}: {response.text}")
            return False, None
    except Exception as e:
        print_result("获取默认模板", False, str(e))
        return False, None

def main():
    """主测试函数"""
    print("=" * 60)
    print("提示词模板API完整测试")
    print("=" * 60)
    print(f"\n测试服务器: {BASE_URL}")
    print(f"API基础路径: {API_BASE}")
    
    # 检查服务是否运行
    try:
        health_response = requests.get(f"{BASE_URL}/api/health", timeout=5)
        if health_response.status_code != 200:
            print("\n[WARNING] 后端服务可能未运行或未响应")
            print("请确保后端服务已启动: uvicorn app.main:app --reload")
    except Exception as e:
        print(f"\n[ERROR] 无法连接到后端服务: {e}")
        print("请确保后端服务已启动: uvicorn app.main:app --reload")
        return
    
    results = {}
    
    # 测试1: 获取智能体类型
    success, agent_types = test_get_agent_types()
    results["获取智能体类型"] = success
    
    # 测试2: 获取模板列表
    success, templates = test_list_templates("fundamentals_analyst")
    results["获取模板列表"] = success
    
    # 测试3: 获取模板详情（如果有模板）
    if templates and len(templates) > 0:
        template_id = templates[0].get('id') or templates[0].get('_id')
        if template_id:
            success, _ = test_get_template(template_id)
            results["获取模板详情"] = success
    
    # 测试4: 获取默认模板
    success, _ = test_get_default_template("fundamentals_analyst")
    results["获取默认模板"] = success
    
    # 测试总结
    print_section("测试总结")
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    failed = total - passed
    
    print(f"总测试数: {total}")
    print(f"通过: {passed}")
    print(f"失败: {failed}")
    
    if failed == 0:
        print("\n[SUCCESS] 所有测试通过！")
    else:
        print(f"\n[WARNING] {failed} 个测试失败")
        for test_name, success in results.items():
            if not success:
                print(f"  - {test_name}")

if __name__ == "__main__":
    main()

