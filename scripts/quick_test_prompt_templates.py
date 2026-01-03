"""
快速测试提示词模板系统
简化版本，只测试核心功能
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_imports():
    """测试所有必要的导入"""
    print("=" * 60)
    print("测试1: 导入检查")
    print("=" * 60)
    
    try:
        from app.models.prompt_template import PromptTemplate, PromptTemplateCreate
        print("✅ 模型导入成功")
        
        from app.services.prompt_template_service import PromptTemplateService
        print("✅ 服务导入成功")
        
        from app.routers.prompt_template import router
        print("✅ 路由导入成功")
        
        from tradingagents.config.prompt_manager import get_prompt_manager
        print("✅ 管理器导入成功")
        
        return True
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_service_init():
    """测试服务初始化"""
    print("\n" + "=" * 60)
    print("测试2: 服务初始化")
    print("=" * 60)
    
    try:
        from app.services.prompt_template_service import PromptTemplateService
        service = PromptTemplateService()
        print("✅ 服务初始化成功")
        print(f"   数据库: {service.db.name}")
        print(f"   集合: prompt_templates, prompt_template_versions, agent_template_configs")
        return True
    except Exception as e:
        print(f"❌ 服务初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_manager_init():
    """测试管理器初始化"""
    print("\n" + "=" * 60)
    print("测试3: 管理器初始化")
    print("=" * 60)
    
    try:
        from tradingagents.config.prompt_manager import get_prompt_manager
        manager = get_prompt_manager()
        print("✅ 管理器初始化成功")
        print(f"   缓存大小: {len(manager._cache)}")
        return True
    except Exception as e:
        print(f"❌ 管理器初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_api_router():
    """测试API路由"""
    print("\n" + "=" * 60)
    print("测试4: API路由检查")
    print("=" * 60)
    
    try:
        from app.routers.prompt_template import router
        routes = [r.path for r in router.routes]
        print(f"✅ 路由注册成功，共 {len(routes)} 个端点")
        print("   主要端点:")
        for route in routes[:5]:
            print(f"     - {route}")
        if len(routes) > 5:
            print(f"     ... 还有 {len(routes) - 5} 个端点")
        return True
    except Exception as e:
        print(f"❌ 路由检查失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """运行所有快速测试"""
    print("\n" + "=" * 60)
    print("提示词模板系统 - 快速测试")
    print("=" * 60)
    
    results = []
    
    # 测试1: 导入
    results.append(("导入检查", test_imports()))
    
    # 测试2: 服务初始化
    results.append(("服务初始化", test_service_init()))
    
    # 测试3: 管理器初始化
    results.append(("管理器初始化", test_manager_init()))
    
    # 测试4: API路由
    results.append(("API路由检查", test_api_router()))
    
    # 输出结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    failed = len(results) - passed
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{name}: {status}")
    
    print(f"\n总计: {passed} 通过, {failed} 失败")
    print("=" * 60)
    
    if failed == 0:
        print("\n🎉 所有快速测试通过！")
        print("\n下一步:")
        print("1. 启动后端服务: python -m app.main")
        print("2. 测试API: curl http://localhost:8000/api/prompt-templates/agents")
        print("3. 初始化模板: python scripts/init_default_prompt_templates.py")
    else:
        print(f"\n⚠️  有 {failed} 个测试失败，请检查错误信息。")


if __name__ == "__main__":
    main()

