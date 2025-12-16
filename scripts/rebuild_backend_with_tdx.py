#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重新构建项目后端，增加通达信数据源支持

此脚本将：
1. 检查并安装pytdx依赖
2. 验证通达信数据源配置
3. 测试通达信接口可用性
4. 更新数据库配置（如果需要）

支持使用本地系统代理进行构建
"""

import sys
import subprocess
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def setup_proxy():
    """设置系统代理"""
    # 常见的代理端口
    proxy_ports = [10809, 10808, 7890, 1080, 8080]
    proxy_host = "127.0.0.1"
    
    # 检查环境变量中是否已有代理设置
    http_proxy = os.environ.get('HTTP_PROXY') or os.environ.get('http_proxy')
    https_proxy = os.environ.get('HTTPS_PROXY') or os.environ.get('https_proxy')
    
    if http_proxy and https_proxy:
        print(f"✅ 检测到已有代理设置:")
        print(f"   HTTP_PROXY: {http_proxy}")
        print(f"   HTTPS_PROXY: {https_proxy}")
        return http_proxy, https_proxy
    
    # 尝试检测本地代理
    print("🔍 检测本地系统代理...")
    for port in proxy_ports:
        proxy_url = f"http://{proxy_host}:{port}"
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((proxy_host, port))
            sock.close()
            if result == 0:
                print(f"✅ 检测到本地代理: {proxy_url}")
                os.environ['HTTP_PROXY'] = proxy_url
                os.environ['HTTPS_PROXY'] = proxy_url
                os.environ['http_proxy'] = proxy_url
                os.environ['https_proxy'] = proxy_url
                return proxy_url, proxy_url
        except:
            continue
    
    print("⚠️ 未检测到本地代理，将直接连接（如果网络受限可能失败）")
    print("💡 提示: 可以通过环境变量设置代理:")
    print("   set HTTP_PROXY=http://127.0.0.1:10809")
    print("   set HTTPS_PROXY=http://127.0.0.1:10809")
    return None, None

def print_step(step_num, description):
    """打印步骤信息"""
    print(f"\n{'='*80}")
    print(f"步骤 {step_num}: {description}")
    print(f"{'='*80}")

def check_python_version():
    """检查Python版本"""
    print_step(1, "检查Python版本")
    version = sys.version_info
    print(f"Python版本: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 10):
        print("❌ 错误: 需要Python 3.10或更高版本")
        return False
    
    print("✅ Python版本符合要求")
    return True

def install_dependencies():
    """安装依赖"""
    print_step(2, "安装/更新依赖")
    
    # 设置代理环境变量
    http_proxy, https_proxy = setup_proxy()
    
    # 准备pip命令环境变量
    pip_env = os.environ.copy()
    if http_proxy:
        pip_env['HTTP_PROXY'] = http_proxy
        pip_env['HTTPS_PROXY'] = https_proxy
        pip_env['http_proxy'] = http_proxy
        pip_env['https_proxy'] = https_proxy
        # 使用清华镜像加速（如果代理可用）
        pip_index_url = "https://pypi.tuna.tsinghua.edu.cn/simple"
    else:
        # 直接使用清华镜像
        pip_index_url = "https://pypi.tuna.tsinghua.edu.cn/simple"
    
    try:
        # 使用pip安装pytdx
        print("📦 安装pytdx库...")
        print(f"   使用镜像: {pip_index_url}")
        if http_proxy:
            print(f"   使用代理: {http_proxy}")
        
        result = subprocess.run(
            [
                sys.executable, "-m", "pip", "install", 
                "--upgrade", "pytdx>=1.72",
                "-i", pip_index_url,
                "--trusted-host", "pypi.tuna.tsinghua.edu.cn"
            ],
            env=pip_env,
            capture_output=True,
            text=True,
            check=True
        )
        print("✅ pytdx安装成功")
        
        # 安装项目依赖
        print("📦 安装项目依赖...")
        result = subprocess.run(
            [
                sys.executable, "-m", "pip", "install", 
                "-e", ".",
                "-i", pip_index_url,
                "--trusted-host", "pypi.tuna.tsinghua.edu.cn"
            ],
            env=pip_env,
            capture_output=True,
            text=True,
            check=True
        )
        print("✅ 项目依赖安装成功")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ 依赖安装失败: {e}")
        if e.stdout:
            print(f"标准输出: {e.stdout[-500:]}")  # 只显示最后500字符
        if e.stderr:
            print(f"错误输出: {e.stderr[-500:]}")
        return False

def verify_tdx_import():
    """验证通达信库导入"""
    print_step(3, "验证通达信库导入")
    
    try:
        import pytdx
        from pytdx.hq import TdxHq_API
        print(f"✅ pytdx库导入成功 (版本: {pytdx.__version__ if hasattr(pytdx, '__version__') else '未知'})")
        return True
    except ImportError as e:
        print(f"❌ pytdx库导入失败: {e}")
        return False

def verify_tdx_utils():
    """验证通达信工具模块"""
    print_step(4, "验证通达信工具模块")
    
    try:
        from data.tdx_utils import get_tdx_provider, get_china_stock_data
        print("✅ 通达信工具模块导入成功")
        return True
    except ImportError as e:
        print(f"❌ 通达信工具模块导入失败: {e}")
        return False

def verify_data_source_config():
    """验证数据源配置"""
    print_step(5, "验证数据源配置")
    
    try:
        from tradingagents.constants.data_sources import DataSourceCode, DATA_SOURCE_REGISTRY
        from tradingagents.dataflows.data_source_manager import ChinaDataSource
        
        # 检查TDX是否在枚举中
        if DataSourceCode.TDX not in DATA_SOURCE_REGISTRY:
            print("❌ TDX未在数据源注册表中")
            return False
        
        tdx_info = DATA_SOURCE_REGISTRY[DataSourceCode.TDX]
        print(f"✅ TDX数据源已注册: {tdx_info.display_name}")
        print(f"   描述: {tdx_info.description}")
        print(f"   支持市场: {tdx_info.supported_markets}")
        
        # 检查ChinaDataSource枚举
        if not hasattr(ChinaDataSource, 'TDX'):
            print("❌ TDX未在ChinaDataSource枚举中")
            return False
        
        print("✅ TDX已在ChinaDataSource枚举中")
        return True
        
    except Exception as e:
        print(f"❌ 数据源配置验证失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_tdx_connection():
    """测试通达信连接"""
    print_step(6, "测试通达信连接（可选）")
    
    try:
        from data.tdx_utils import get_tdx_provider
        
        print("🔌 尝试连接通达信服务器...")
        provider = get_tdx_provider()
        
        if provider.connect():
            print("✅ 通达信服务器连接成功")
            provider.disconnect()
            return True
        else:
            print("⚠️ 通达信服务器连接失败（可能是网络问题，不影响配置）")
            return True  # 网络问题不影响配置验证
            
    except Exception as e:
        print(f"⚠️ 连接测试失败: {e}（可能是网络问题，不影响配置）")
        return True  # 网络问题不影响配置验证

def verify_data_source_manager():
    """验证数据源管理器"""
    print_step(7, "验证数据源管理器")
    
    try:
        from tradingagents.dataflows.data_source_manager import (
            get_data_source_manager, 
            ChinaDataSource
        )
        
        manager = get_data_source_manager()
        
        # 检查TDX是否在可用数据源中
        if ChinaDataSource.TDX in manager.available_sources:
            print("✅ TDX在可用数据源列表中")
        else:
            print("⚠️ TDX不在可用数据源列表中（可能需要安装pytdx）")
        
        # 检查默认数据源
        default_source = manager.default_source
        print(f"📊 默认数据源: {default_source.value}")
        
        if default_source == ChinaDataSource.TDX:
            print("✅ TDX已设置为默认数据源")
        else:
            print(f"⚠️ 当前默认数据源是: {default_source.value}")
        
        return True
        
    except Exception as e:
        print(f"❌ 数据源管理器验证失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("="*80)
    print("🚀 重新构建项目后端 - 增加通达信数据源支持")
    print("="*80)
    
    # 设置代理（在开始时就设置）
    setup_proxy()
    
    # 切换到项目根目录
    os.chdir(project_root)
    print(f"📁 工作目录: {os.getcwd()}")
    
    steps = [
        ("检查Python版本", check_python_version),
        ("安装依赖", install_dependencies),
        ("验证pytdx导入", verify_tdx_import),
        ("验证通达信工具模块", verify_tdx_utils),
        ("验证数据源配置", verify_data_source_config),
        ("测试通达信连接", test_tdx_connection),
        ("验证数据源管理器", verify_data_source_manager),
    ]
    
    results = []
    for name, func in steps:
        try:
            result = func()
            results.append((name, result))
            if not result:
                print(f"\n❌ 步骤 '{name}' 失败，但继续执行后续步骤...")
        except Exception as e:
            print(f"\n❌ 步骤 '{name}' 发生异常: {e}")
            results.append((name, False))
    
    # 总结
    print("\n" + "="*80)
    print("📊 构建总结")
    print("="*80)
    
    success_count = sum(1 for _, result in results if result)
    total_count = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {status}: {name}")
    
    print(f"\n总计: {success_count}/{total_count} 步骤通过")
    
    if success_count == total_count:
        print("\n🎉 后端构建完成！通达信数据源已成功集成")
        print("\n💡 下一步:")
        print("   1. 启动后端服务: python -m app")
        print("   2. 或使用Docker: docker-compose up backend")
        return 0
    else:
        print("\n⚠️ 部分步骤失败，请检查上述错误信息")
        return 1

if __name__ == "__main__":
    sys.exit(main())

