"""
启动服务并测试提示词模板功能
"""

import sys
import subprocess
import time
import requests
from pathlib import Path

BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/prompt-templates"

def check_service(url, name, timeout=5):
    """检查服务是否运行"""
    try:
        response = requests.get(url, timeout=timeout)
        return response.status_code == 200
    except:
        return False

def test_api_endpoints():
    """测试API端点"""
    print("\n" + "=" * 60)
    print("测试提示词模板API端点")
    print("=" * 60)
    
    results = {}
    
    # 测试1: 获取智能体类型
    print("\n[测试1] 获取智能体类型...")
    try:
        response = requests.get(f"{API_BASE}/agents", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"  [OK] 成功获取 {len(data)} 个分类")
            for category, agents in data.items():
                print(f"    - {category}: {len(agents)} 个智能体")
            results["获取智能体类型"] = True
        else:
            print(f"  [FAIL] HTTP {response.status_code}: {response.text}")
            results["获取智能体类型"] = False
    except Exception as e:
        print(f"  [FAIL] 错误: {e}")
        results["获取智能体类型"] = False
    
    # 测试2: 获取模板列表
    print("\n[测试2] 获取模板列表...")
    try:
        response = requests.get(f"{API_BASE}?agent_type=fundamentals_analyst", timeout=10)
        if response.status_code == 200:
            data = response.json()
            templates = data if isinstance(data, list) else data.get('items', [])
            print(f"  [OK] 找到 {len(templates)} 个模板")
            for template in templates[:3]:
                name = template.get('template_display_name', 'N/A')
                is_default = template.get('is_default', False)
                print(f"    - {name} (默认: {is_default})")
            results["获取模板列表"] = True
        else:
            print(f"  [FAIL] HTTP {response.status_code}: {response.text}")
            results["获取模板列表"] = False
    except Exception as e:
        print(f"  [FAIL] 错误: {e}")
        results["获取模板列表"] = False
    
    # 测试3: 获取默认模板
    print("\n[测试3] 获取默认模板...")
    try:
        response = requests.get(f"{API_BASE}/default/fundamentals_analyst", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"  [OK] 默认模板: {data.get('template_display_name', 'N/A')}")
            results["获取默认模板"] = True
        else:
            print(f"  [FAIL] HTTP {response.status_code}: {response.text}")
            results["获取默认模板"] = False
    except Exception as e:
        print(f"  [FAIL] 错误: {e}")
        results["获取默认模板"] = False
    
    # 测试总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    failed = total - passed
    
    print(f"总测试数: {total}")
    print(f"通过: {passed}")
    print(f"失败: {failed}")
    
    if failed == 0:
        print("\n[SUCCESS] 所有API测试通过！")
    else:
        print(f"\n[WARNING] {failed} 个测试失败")
    
    return results

def main():
    """主函数"""
    print("=" * 60)
    print("提示词模板系统服务测试")
    print("=" * 60)
    
    # 检查后端服务
    print("\n[1] 检查后端服务...")
    if check_service(f"{BASE_URL}/api/health", "后端服务"):
        print("  [OK] 后端服务正在运行")
    else:
        print("  [WARNING] 后端服务未运行")
        print("  请运行: uvicorn app.main:app --reload")
        print("  或: python -m uvicorn app.main:app --reload")
        return
    
    # 检查前端服务
    print("\n[2] 检查前端服务...")
    if check_service("http://localhost:3000", "前端服务"):
        print("  [OK] 前端服务正在运行")
        print("  访问: http://localhost:3000/settings/agents")
    else:
        print("  [INFO] 前端服务未运行（可选）")
        print("  启动命令: cd frontend && npm run dev")
    
    # 测试API
    print("\n[3] 测试API端点...")
    results = test_api_endpoints()
    
    # 提供下一步建议
    print("\n" + "=" * 60)
    print("下一步操作")
    print("=" * 60)
    print("\n1. 前端界面测试:")
    print("   - 访问: http://localhost:3000/settings/agents")
    print("   - 验证模板列表显示")
    print("   - 测试创建/编辑功能")
    
    print("\n2. 完整功能测试:")
    print("   - 创建新模板")
    print("   - 设置默认模板")
    print("   - 配置用户模板")
    print("   - 测试模板版本管理")
    
    print("\n3. 集成测试:")
    print("   - 提交分析请求")
    print("   - 验证智能体使用模板")
    print("   - 检查日志确认模板加载")

if __name__ == "__main__":
    main()

