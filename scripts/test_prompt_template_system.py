"""
测试提示词模板系统 - 完整测试脚本
包括数据库连接、API测试、模板创建等
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import logging
from bson import ObjectId
from app.services.prompt_template_service import PromptTemplateService
from app.models.prompt_template import PromptTemplateCreate, PromptTemplateContent
from tradingagents.config.prompt_manager import get_prompt_manager

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_database_connection():
    """测试数据库连接"""
    print("\n" + "=" * 60)
    print("测试1: 数据库连接")
    print("=" * 60)
    
    try:
        service = PromptTemplateService()
        # 尝试查询集合
        count = service.templates_collection.count_documents({})
        print(f"✅ 数据库连接成功")
        print(f"   当前模板数量: {count}")
        return True
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return False


def test_create_default_template():
    """测试创建默认模板"""
    print("\n" + "=" * 60)
    print("测试2: 创建默认模板")
    print("=" * 60)
    
    try:
        service = PromptTemplateService()
        
        # 检查模板是否已存在
        existing = service.get_template_by_name("fundamentals_analyst", "default")
        if existing:
            print(f"✅ 默认模板已存在: {existing.id}")
            return existing.id
        
        # 创建模板
        template = PromptTemplateCreate(
            agent_type="fundamentals_analyst",
            agent_name="基本面分析师",
            template_name="default",
            template_display_name="默认模板",
            description="标准的基本面分析提示词",
            content=PromptTemplateContent(
                system_prompt="""你是一位专业的股票基本面分析师。
⚠️ 绝对强制要求：你必须调用工具获取真实数据！不允许任何假设或编造！

任务：分析{company_name}（股票代码：{ticker}，{market_name}）

🔴 立即调用 get_stock_fundamentals_unified 工具
参数：ticker='{ticker}', start_date='{start_date}', end_date='{current_date}'

📊 分析要求：
- 基于真实数据进行深度基本面分析
- 计算并提供合理价位区间（使用{currency_name}{currency_symbol}）
- 分析当前股价是否被低估或高估
- 提供基于基本面的目标价位建议
- 包含PE、PB、PEG等估值指标分析

🌍 语言要求：
- 所有分析内容必须使用中文
- 投资建议必须使用中文：买入、持有、卖出

🚫 严格禁止：
- 不允许假设任何数据
- 不允许编造公司信息
- 不允许使用英文投资建议

现在立即开始调用工具！"""
            ),
            tags=["default", "fundamentals"],
            is_default=True,
            is_system=True
        )
        
        result = service.create_template(template, user_id=None)
        print(f"✅ 创建默认模板成功")
        print(f"   模板ID: {result.id}")
        print(f"   模板名称: {result.template_display_name}")
        return result.id
        
    except Exception as e:
        print(f"❌ 创建模板失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_list_templates():
    """测试列出模板"""
    print("\n" + "=" * 60)
    print("测试3: 列出模板")
    print("=" * 60)
    
    try:
        service = PromptTemplateService()
        templates = service.list_templates(agent_type="fundamentals_analyst")
        print(f"✅ 找到 {len(templates)} 个模板")
        for template in templates:
            print(f"   - {template.template_display_name} ({template.template_name})")
            print(f"     默认: {template.is_default}, 系统: {template.is_system}")
        return True
    except Exception as e:
        print(f"❌ 列出模板失败: {e}")
        return False


def test_template_manager():
    """测试提示词管理器"""
    print("\n" + "=" * 60)
    print("测试4: 提示词管理器")
    print("=" * 60)
    
    try:
        manager = get_prompt_manager()
        
        # 准备变量
        variables = {
            "ticker": "000001",
            "company_name": "平安银行",
            "market_name": "A股",
            "currency_name": "人民币",
            "currency_symbol": "¥",
            "current_date": "2024-01-15",
            "start_date": "2024-01-05"
        }
        
        # 获取系统提示词
        system_prompt = manager.get_system_prompt(
            agent_type="fundamentals_analyst",
            variables=variables
        )
        
        print(f"✅ 成功获取系统提示词")
        print(f"   提示词长度: {len(system_prompt)}")
        print(f"   前100字符: {system_prompt[:100]}...")
        
        # 验证变量是否被替换
        if "000001" in system_prompt and "平安银行" in system_prompt:
            print(f"✅ 变量替换成功")
        else:
            print(f"⚠️  变量替换可能未生效")
        
        return True
    except Exception as e:
        print(f"❌ 提示词管理器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_template_rendering():
    """测试模板渲染"""
    print("\n" + "=" * 60)
    print("测试5: 模板渲染")
    print("=" * 60)
    
    try:
        service = PromptTemplateService()
        template = service.get_default_template("fundamentals_analyst")
        
        if not template:
            print("⚠️  未找到默认模板，跳过渲染测试")
            return False
        
        variables = {
            "ticker": "000001",
            "company_name": "平安银行",
            "market_name": "A股",
            "currency_name": "人民币",
            "currency_symbol": "¥",
            "current_date": "2024-01-15",
            "start_date": "2024-01-05"
        }
        
        rendered = service.render_template(template, variables)
        system_prompt = rendered.get("system_prompt", "")
        
        print(f"✅ 模板渲染成功")
        print(f"   原始长度: {len(template.content.system_prompt)}")
        print(f"   渲染后长度: {len(system_prompt)}")
        
        # 验证变量替换
        if "000001" in system_prompt and "平安银行" in system_prompt:
            print(f"✅ 变量替换验证通过")
        else:
            print(f"⚠️  变量替换验证失败")
        
        return True
    except Exception as e:
        print(f"❌ 模板渲染失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """运行所有测试"""
    print("=" * 60)
    print("提示词模板系统 - 完整测试")
    print("=" * 60)
    
    results = []
    
    # 测试1: 数据库连接
    results.append(("数据库连接", test_database_connection()))
    
    # 测试2: 创建默认模板
    template_id = test_create_default_template()
    results.append(("创建默认模板", template_id is not None))
    
    # 测试3: 列出模板
    results.append(("列出模板", test_list_templates()))
    
    # 测试4: 提示词管理器
    results.append(("提示词管理器", test_template_manager()))
    
    # 测试5: 模板渲染
    results.append(("模板渲染", test_template_rendering()))
    
    # 输出测试结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{name}: {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\n总计: {passed} 通过, {failed} 失败")
    print("=" * 60)
    
    if failed == 0:
        print("\n🎉 所有测试通过！系统已准备就绪。")
    else:
        print(f"\n⚠️  有 {failed} 个测试失败，请检查错误信息。")


if __name__ == "__main__":
    main()

