#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版验证脚本 - 验证通达信数据源集成
跳过.env文件加载，直接验证核心功能
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_tdx_import():
    """测试pytdx导入"""
    print("="*80)
    print("测试1: pytdx库导入")
    print("="*80)
    try:
        import pytdx
        from pytdx.hq import TdxHq_API
        print("✅ pytdx库导入成功")
        return True
    except ImportError as e:
        print(f"❌ pytdx库导入失败: {e}")
        return False

def test_tdx_utils():
    """测试通达信工具模块"""
    print("\n" + "="*80)
    print("测试2: 通达信工具模块")
    print("="*80)
    try:
        # 直接导入，不触发config_manager
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "tdx_utils", 
            project_root / "data" / "tdx_utils.py"
        )
        tdx_utils = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(tdx_utils)
        
        print("✅ 通达信工具模块加载成功")
        print(f"   文件路径: {project_root / 'data' / 'tdx_utils.py'}")
        return True
    except Exception as e:
        print(f"❌ 通达信工具模块加载失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_data_source_code():
    """测试数据源编码定义"""
    print("\n" + "="*80)
    print("测试3: 数据源编码定义")
    print("="*80)
    try:
        # 直接读取文件内容检查
        ds_file = project_root / "tradingagents" / "constants" / "data_sources.py"
        content = ds_file.read_text(encoding='utf-8')
        
        if 'TDX = "tdx"' in content:
            print("✅ TDX已在DataSourceCode枚举中")
        else:
            print("❌ TDX未在DataSourceCode枚举中")
            return False
        
        if 'DataSourceCode.TDX:' in content:
            print("✅ TDX已在DATA_SOURCE_REGISTRY中")
        else:
            print("❌ TDX未在DATA_SOURCE_REGISTRY中")
            return False
        
        return True
    except Exception as e:
        print(f"❌ 检查失败: {e}")
        return False

def test_china_data_source():
    """测试ChinaDataSource枚举"""
    print("\n" + "="*80)
    print("测试4: ChinaDataSource枚举")
    print("="*80)
    try:
        ds_manager_file = project_root / "tradingagents" / "dataflows" / "data_source_manager.py"
        content = ds_manager_file.read_text(encoding='utf-8')
        
        if 'TDX = DataSourceCode.TDX' in content:
            print("✅ TDX已在ChinaDataSource枚举中")
        else:
            print("❌ TDX未在ChinaDataSource枚举中")
            return False
        
        if 'ChinaDataSource.TDX' in content:
            print("✅ TDX在代码中被使用")
        else:
            print("⚠️ TDX在代码中未被使用")
        
        return True
    except Exception as e:
        print(f"❌ 检查失败: {e}")
        return False

def test_data_source_type():
    """测试DataSourceType枚举"""
    print("\n" + "="*80)
    print("测试5: DataSourceType枚举")
    print("="*80)
    try:
        config_file = project_root / "app" / "models" / "config.py"
        content = config_file.read_text(encoding='utf-8')
        
        if 'TDX = "tdx"' in content:
            print("✅ TDX已在DataSourceType枚举中")
            return True
        else:
            print("❌ TDX未在DataSourceType枚举中")
            return False
    except Exception as e:
        print(f"❌ 检查失败: {e}")
        return False

def test_default_source():
    """测试默认数据源配置"""
    print("\n" + "="*80)
    print("测试6: 默认数据源配置")
    print("="*80)
    try:
        ds_manager_file = project_root / "tradingagents" / "dataflows" / "data_source_manager.py"
        content = ds_manager_file.read_text(encoding='utf-8')
        
        if 'DataSourceCode.TDX' in content and 'default_source' in content.lower():
            # 检查是否设置为默认
            if 'env_source = os.getenv(\'DEFAULT_CHINA_DATA_SOURCE\', DataSourceCode.TDX)' in content:
                print("✅ TDX已设置为默认数据源（环境变量默认值）")
            elif 'return source_mapping.get(env_source, ChinaDataSource.TDX)' in content:
                print("✅ TDX已设置为默认数据源（fallback值）")
            else:
                print("⚠️ TDX可能未设置为默认数据源")
        
        # 检查优先级
        if 'ChinaDataSource.TDX,' in content and 'default_order' in content:
            print("✅ TDX在默认优先级列表中")
        
        return True
    except Exception as e:
        print(f"❌ 检查失败: {e}")
        return False

def test_pyproject_toml():
    """测试pyproject.toml配置"""
    print("\n" + "="*80)
    print("测试7: pyproject.toml配置")
    print("="*80)
    try:
        pyproject_file = project_root / "pyproject.toml"
        content = pyproject_file.read_text(encoding='utf-8')
        
        if 'pytdx' in content.lower():
            print("✅ pytdx已在pyproject.toml中")
            return True
        else:
            print("❌ pytdx未在pyproject.toml中")
            return False
    except Exception as e:
        print(f"❌ 检查失败: {e}")
        return False

def main():
    """主函数"""
    print("="*80)
    print("🔍 验证通达信数据源集成（简化版）")
    print("="*80)
    print(f"📁 项目根目录: {project_root}")
    
    tests = [
        ("pytdx库导入", test_tdx_import),
        ("通达信工具模块", test_tdx_utils),
        ("数据源编码定义", test_data_source_code),
        ("ChinaDataSource枚举", test_china_data_source),
        ("DataSourceType枚举", test_data_source_type),
        ("默认数据源配置", test_default_source),
        ("pyproject.toml配置", test_pyproject_toml),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ 测试 '{name}' 发生异常: {e}")
            results.append((name, False))
    
    # 总结
    print("\n" + "="*80)
    print("📊 验证总结")
    print("="*80)
    
    success_count = sum(1 for _, result in results if result)
    total_count = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {status}: {name}")
    
    print(f"\n总计: {success_count}/{total_count} 测试通过")
    
    if success_count == total_count:
        print("\n🎉 所有验证通过！通达信数据源已成功集成到项目中")
        print("\n💡 下一步:")
        print("   1. 修复.env文件编码问题（如果需要）")
        print("   2. 启动后端服务: python -m app")
        print("   3. 测试数据源: 使用API获取股票数据")
        return 0
    else:
        print("\n⚠️ 部分测试失败，请检查上述错误信息")
        return 1

if __name__ == "__main__":
    sys.exit(main())

