#!/usr/bin/env python3
"""
Tushare接口诊断脚本
用于验证tushare接口失败的原因
"""

import os
import sys
import traceback
from datetime import datetime, timedelta

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# 设置环境变量（避免某些模块初始化失败）
os.environ.setdefault("TUSHARE_ENABLED", "true")


def print_section(title: str):
    """打印分节标题"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def print_result(success: bool, message: str, details: str = ""):
    """打印测试结果"""
    icon = "✅" if success else "❌"
    print(f"{icon} {message}")
    if details:
        print(f"   {details}")


def check_tushare_library():
    """检查Tushare库是否安装"""
    print_section("1. 检查Tushare库安装")
    
    try:
        import tushare as ts
        version = getattr(ts, '__version__', '未知')
        print_result(True, f"Tushare库已安装", f"版本: {version}")
        return True, ts
    except ImportError as e:
        print_result(False, "Tushare库未安装", f"错误: {e}")
        print("   解决方案: pip install tushare")
        return False, None


def check_token_configuration():
    """检查Token配置"""
    print_section("2. 检查Token配置")
    
    results = {
        'env_token': None,
        'db_token': None,
        'provider_token': None,
        'token_source': None
    }
    
    # 检查环境变量Token
    env_token = os.getenv('TUSHARE_TOKEN')
    if env_token:
        if env_token.startswith('your_'):
            print_result(False, "环境变量TUSHARE_TOKEN", "值为占位符（your_xxx）")
        else:
            print_result(True, "环境变量TUSHARE_TOKEN", f"已设置 (长度: {len(env_token)})")
            results['env_token'] = env_token
    else:
        print_result(False, "环境变量TUSHARE_TOKEN", "未设置")
    
    # 检查数据库Token
    try:
        from app.core.database import get_mongo_db_sync
        db = get_mongo_db_sync()
        config_collection = db.system_configs
        
        config_data = config_collection.find_one(
            {"is_active": True},
            sort=[("version", -1)]
        )
        
        if config_data and config_data.get('data_source_configs'):
            for ds_config in config_data['data_source_configs']:
                if ds_config.get('type') == 'tushare':
                    db_token = ds_config.get('api_key')
                    if db_token:
                        if db_token.startswith('your_'):
                            print_result(False, "数据库TUSHARE_TOKEN", "值为占位符（your_xxx）")
                        else:
                            print_result(True, "数据库TUSHARE_TOKEN", f"已设置 (长度: {len(db_token)})")
                            results['db_token'] = db_token
                    else:
                        print_result(False, "数据库TUSHARE_TOKEN", "未设置")
                    break
        else:
            print_result(False, "数据库配置", "未找到激活的配置")
    except Exception as e:
        print_result(False, "数据库Token检查", f"错误: {e}")
        print(f"   堆栈跟踪:\n{traceback.format_exc()}")
    
    # 检查Provider中的Token
    try:
        from tradingagents.dataflows.providers.china.tushare import get_tushare_provider
        provider = get_tushare_provider()
        
        # 检查provider的token_source
        token_source = getattr(provider, 'token_source', None)
        if token_source:
            print_result(True, f"Provider Token来源", f"{token_source}")
            results['token_source'] = token_source
        
        # 尝试获取实际使用的token（通过config）
        if hasattr(provider, 'config'):
            provider_token = provider.config.get('token')
            if provider_token:
                print_result(True, "Provider配置Token", f"已设置 (长度: {len(provider_token)})")
                results['provider_token'] = provider_token
            else:
                print_result(False, "Provider配置Token", "未设置")
    except Exception as e:
        print_result(False, "Provider Token检查", f"错误: {e}")
        print(f"   堆栈跟踪:\n{traceback.format_exc()}")
    
    return results


def test_tushare_connection(ts_module):
    """测试Tushare API连接"""
    print_section("3. 测试Tushare API连接")
    
    if not ts_module:
        print_result(False, "跳过连接测试", "Tushare库未安装")
        return False, None
    
    # 获取Token
    token = os.getenv('TUSHARE_TOKEN')
    if not token or token.startswith('your_'):
        print_result(False, "Token未配置", "无法进行连接测试")
        return False, None
    
    try:
        # 设置Token
        ts_module.set_token(token)
        pro = ts_module.pro_api()
        
        # 测试连接 - 调用一个简单的API
        print("   正在测试API连接...")
        test_data = pro.stock_basic(list_status='L', limit=1)
        
        if test_data is not None and not test_data.empty:
            print_result(True, "API连接成功", f"返回 {len(test_data)} 条测试数据")
            return True, pro
        else:
            print_result(False, "API连接失败", "返回空数据")
            return False, None
            
    except Exception as e:
        error_msg = str(e)
        print_result(False, "API连接失败", f"错误: {error_msg}")
        
        # 分析错误类型
        if "token" in error_msg.lower() or "token" in error_msg:
            print("   💡 可能原因: Token无效或已过期")
        elif "积分" in error_msg or "point" in error_msg.lower():
            print("   💡 可能原因: Tushare积分不足")
        elif "权限" in error_msg or "permission" in error_msg.lower():
            print("   💡 可能原因: Token权限不足")
        elif "网络" in error_msg or "network" in error_msg.lower() or "timeout" in error_msg.lower():
            print("   💡 可能原因: 网络连接问题")
        else:
            print(f"   💡 完整错误信息:\n{traceback.format_exc()}")
        
        return False, None


def test_provider_connection():
    """测试Provider连接"""
    print_section("4. 测试Provider连接")
    
    try:
        from tradingagents.dataflows.providers.china.tushare import get_tushare_provider
        provider = get_tushare_provider()
        
        # 检查连接状态
        connected = getattr(provider, 'connected', False)
        if connected:
            print_result(True, "Provider已连接", "")
        else:
            print("   尝试连接Provider...")
            connected = provider.connect_sync()
            if connected:
                print_result(True, "Provider连接成功", "")
            else:
                print_result(False, "Provider连接失败", "请查看上面的错误信息")
                return False, None
        
        # 检查API对象
        api = getattr(provider, 'api', None)
        if api:
            print_result(True, "Provider API对象", "已初始化")
        else:
            print_result(False, "Provider API对象", "未初始化")
            return False, None
        
        return True, provider
        
    except Exception as e:
        print_result(False, "Provider连接测试失败", f"错误: {e}")
        print(f"   堆栈跟踪:\n{traceback.format_exc()}")
        return False, None


def test_api_calls(pro_api):
    """测试各种API调用"""
    print_section("5. 测试API调用")
    
    if not pro_api:
        print_result(False, "跳过API调用测试", "API未初始化")
        return
    
    test_cases = [
        {
            'name': 'stock_basic (股票列表)',
            'func': lambda: pro_api.stock_basic(list_status='L', limit=5),
            'required': True
        },
        {
            'name': 'daily (日线行情)',
            'func': lambda: pro_api.daily(ts_code='000001.SZ', start_date='20240101', end_date='20240110'),
            'required': False
        },
        {
            'name': 'daily_basic (每日指标)',
            'func': lambda: pro_api.daily_basic(trade_date='20240110', fields='ts_code,total_mv,pe'),
            'required': False
        },
        {
            'name': 'fina_indicator (财务指标)',
            'func': lambda: pro_api.fina_indicator(ts_code='000001.SZ', limit=1),
            'required': False
        },
    ]
    
    for test_case in test_cases:
        try:
            print(f"\n   测试: {test_case['name']}")
            result = test_case['func']()
            
            if result is not None and not result.empty:
                print_result(True, f"{test_case['name']}", f"成功，返回 {len(result)} 条数据")
            else:
                print_result(False, f"{test_case['name']}", "返回空数据")
        except Exception as e:
            error_msg = str(e)
            print_result(False, f"{test_case['name']}", f"失败: {error_msg}")
            
            # 分析错误
            if "积分" in error_msg or "point" in error_msg.lower():
                print("      💡 可能原因: 积分不足，该接口需要付费权限")
            elif "权限" in error_msg or "permission" in error_msg.lower():
                print("      💡 可能原因: Token权限不足")


def test_adapter():
    """测试Adapter"""
    print_section("6. 测试Adapter")
    
    try:
        from app.services.data_sources.tushare_adapter import TushareAdapter
        adapter = TushareAdapter()
        
        # 检查可用性
        is_available = adapter.is_available()
        if is_available:
            print_result(True, "Adapter可用", "")
        else:
            print_result(False, "Adapter不可用", "请检查Provider连接状态")
            return
        
        # 测试获取股票列表
        try:
            print("\n   测试: get_stock_list()")
            stock_list = adapter.get_stock_list()
            if stock_list is not None and not stock_list.empty:
                print_result(True, "get_stock_list()", f"成功，返回 {len(stock_list)} 条数据")
            else:
                print_result(False, "get_stock_list()", "返回空数据")
        except Exception as e:
            print_result(False, "get_stock_list()", f"失败: {e}")
        
        # 测试获取每日数据
        try:
            print("\n   测试: get_daily_basic()")
            today = datetime.now().strftime('%Y%m%d')
            daily_data = adapter.get_daily_basic(today)
            if daily_data is not None and not daily_data.empty:
                print_result(True, "get_daily_basic()", f"成功，返回 {len(daily_data)} 条数据")
            else:
                print_result(False, "get_daily_basic()", "返回空数据（可能是非交易日）")
        except Exception as e:
            print_result(False, "get_daily_basic()", f"失败: {e}")
        
    except Exception as e:
        print_result(False, "Adapter测试失败", f"错误: {e}")
        print(f"   堆栈跟踪:\n{traceback.format_exc()}")


def generate_summary():
    """生成诊断总结"""
    print_section("7. 诊断总结")
    
    print("\n📋 检查清单:")
    print("   □ Tushare库是否安装")
    print("   □ Token是否配置（环境变量或数据库）")
    print("   □ API连接是否成功")
    print("   □ Provider是否可用")
    print("   □ Adapter是否可用")
    
    print("\n💡 常见问题解决方案:")
    print("   1. Token未配置:")
    print("      - 在.env文件中设置 TUSHARE_TOKEN=your_token")
    print("      - 或在Web后台配置数据源")
    print("   2. Token无效:")
    print("      - 检查Token是否正确（不要包含空格）")
    print("      - 访问 https://tushare.pro 确认Token状态")
    print("   3. 积分不足:")
    print("      - 某些接口需要付费权限")
    print("      - 检查Tushare账户积分")
    print("   4. 网络问题:")
    print("      - 检查网络连接")
    print("      - 检查防火墙设置")
    print("   5. Provider连接失败:")
    print("      - 检查数据库配置是否正确")
    print("      - 检查config_bridge是否正确桥接配置")


def main():
    """主函数"""
    print("\n" + "=" * 80)
    print("  Tushare接口诊断工具")
    print("=" * 80)
    print("\n本工具将检查以下内容:")
    print("  1. Tushare库安装状态")
    print("  2. Token配置（环境变量和数据库）")
    print("  3. API连接测试")
    print("  4. Provider连接测试")
    print("  5. API调用测试")
    print("  6. Adapter功能测试")
    
    # 1. 检查库
    lib_ok, ts_module = check_tushare_library()
    
    # 2. 检查Token配置
    token_results = check_token_configuration()
    
    # 3. 测试API连接
    if lib_ok:
        api_ok, pro_api = test_tushare_connection(ts_module)
    else:
        api_ok, pro_api = False, None
    
    # 4. 测试Provider连接
    provider_ok, provider = test_provider_connection()
    
    # 5. 测试API调用
    if pro_api:
        test_api_calls(pro_api)
    
    # 6. 测试Adapter
    if provider_ok:
        test_adapter()
    
    # 7. 生成总结
    generate_summary()
    
    print("\n" + "=" * 80)
    print("  诊断完成")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ 用户中断")
    except Exception as e:
        print(f"\n\n❌ 诊断过程发生错误: {e}")
        print(traceback.format_exc())

