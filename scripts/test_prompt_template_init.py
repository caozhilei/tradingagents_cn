"""
测试提示词模板初始化脚本
直接测试数据库操作，不依赖API服务
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 设置环境变量避免配置错误
import os
os.environ.setdefault('TUSHARE_ENABLED', 'false')
os.environ.setdefault('MONGO_URI', 'mongodb://localhost:27017')
os.environ.setdefault('MONGO_DB', 'tradingagents')

try:
    from app.services.prompt_template_service import PromptTemplateService
    from app.models.prompt_template import PromptTemplateCreate, PromptTemplateContent
    from bson import ObjectId
    
    print("=" * 60)
    print("测试提示词模板服务")
    print("=" * 60)
    
    service = PromptTemplateService()
    print("✅ 服务初始化成功")
    
    # 测试获取智能体类型
    print("\n测试获取智能体类型...")
    try:
        agent_types = service.get_agent_types()
        print(f"✅ 获取到 {len(agent_types)} 个智能体类型")
        for category, agents in agent_types.items():
            print(f"  - {category}: {len(agents)} 个智能体")
    except Exception as e:
        print(f"❌ 获取智能体类型失败: {e}")
    
    # 测试获取模板列表
    print("\n测试获取模板列表...")
    try:
        templates = service.list_templates(agent_type="fundamentals_analyst")
        print(f"✅ 获取到 {len(templates)} 个模板")
        for template in templates[:3]:  # 只显示前3个
            print(f"  - {template.template_display_name} ({template.template_name})")
    except Exception as e:
        print(f"❌ 获取模板列表失败: {e}")
    
    # 测试获取默认模板
    print("\n测试获取默认模板...")
    try:
        default_template = service.get_default_template("fundamentals_analyst")
        if default_template:
            print(f"✅ 找到默认模板: {default_template.template_display_name}")
        else:
            print("⚠️  未找到默认模板")
    except Exception as e:
        print(f"❌ 获取默认模板失败: {e}")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
    
except Exception as e:
    print(f"❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

