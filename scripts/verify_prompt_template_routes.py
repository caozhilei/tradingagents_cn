"""
验证提示词模板路由是否正确注册
"""

import requests
import sys

BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/prompt-templates"

def test_endpoint(path, name):
    """测试API端点"""
    url = f"{API_BASE}{path}"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            print(f"[OK] {name}: {url}")
            return True
        else:
            print(f"[FAIL] {name}: {url} - HTTP {response.status_code}")
            print(f"      Response: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"[ERROR] {name}: {url} - {str(e)}")
        return False

def main():
    print("=" * 60)
    print("验证提示词模板API路由")
    print("=" * 60)
    print(f"\n测试服务器: {BASE_URL}")
    print(f"API基础路径: {API_BASE}\n")
    
    # 检查服务是否运行
    try:
        health = requests.get(f"{BASE_URL}/api/health", timeout=5)
        if health.status_code == 200:
            print("[OK] 后端服务正在运行\n")
        else:
            print(f"[WARNING] 后端服务响应异常: HTTP {health.status_code}\n")
    except Exception as e:
        print(f"[ERROR] 无法连接到后端服务: {e}")
        print("\n请确保后端服务已启动:")
        print("  uvicorn app.main:app --reload")
        return
    
    # 测试端点
    results = []
    
    results.append(test_endpoint("/agents", "获取智能体类型"))
    results.append(test_endpoint("?agent_type=fundamentals_analyst", "获取模板列表"))
    results.append(test_endpoint("/default/fundamentals_analyst", "获取默认模板"))
    
    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"通过: {passed}/{total}")
    
    if passed == 0:
        print("\n[WARNING] 所有测试失败，可能的原因:")
        print("1. 后端服务需要重启以加载新路由")
        print("2. 路由注册有问题")
        print("3. 检查服务启动日志中的错误信息")
        print("\n建议:")
        print("1. 重启后端服务: uvicorn app.main:app --reload")
        print("2. 检查 app/main.py 第699行的路由注册")
        print("3. 访问 http://localhost:8000/docs 查看API文档")
    elif passed < total:
        print(f"\n[WARNING] {total - passed} 个测试失败")
    else:
        print("\n[SUCCESS] 所有测试通过！")

if __name__ == "__main__":
    main()

