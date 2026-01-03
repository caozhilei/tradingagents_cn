#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
诊断 get_stock_news_unified 函数调用失败的原因
"""

import os
import sys
import traceback
from datetime import datetime

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# 设置环境变量
os.environ.setdefault("TUSHARE_ENABLED", "true")

# 设置Windows控制台编码
if sys.platform == 'win32':
    try:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except:
        pass


def print_section(title: str):
    """打印分节标题"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def print_result(success: bool, message: str, details: str = ""):
    """打印测试结果"""
    try:
        icon = "[OK]" if success else "[FAIL]"
        print(f"{icon} {message}")
    except UnicodeEncodeError:
        icon = "[OK]" if success else "[FAIL]"
        print(f"{icon} {message}")
    if details:
        print(f"   {details}")


def test_import():
    """测试导入"""
    print_section("1. 测试模块导入")
    
    try:
        from tradingagents.tools.unified_news_tool import create_unified_news_tool
        print_result(True, "统一新闻工具模块导入成功")
        return True, create_unified_news_tool
    except Exception as e:
        print_result(False, "统一新闻工具模块导入失败", f"错误: {e}")
        print(f"   堆栈跟踪:\n{traceback.format_exc()}")
        return False, None


def test_toolkit_creation():
    """测试工具包创建"""
    print_section("2. 测试工具包创建")
    
    try:
        from tradingagents.agents.utils.agent_utils import Toolkit
        toolkit = Toolkit()
        print_result(True, "工具包创建成功")
        
        # 检查必要的工具是否存在
        required_tools = [
            'get_realtime_stock_news',
            'get_google_news',
            'get_global_news_openai'
        ]
        
        for tool_name in required_tools:
            if hasattr(toolkit, tool_name):
                print_result(True, f"工具 {tool_name} 存在")
            else:
                print_result(False, f"工具 {tool_name} 不存在")
        
        return True, toolkit
    except Exception as e:
        print_result(False, "工具包创建失败", f"错误: {e}")
        print(f"   堆栈跟踪:\n{traceback.format_exc()}")
        return False, None


def test_unified_news_tool_creation(toolkit, create_unified_news_tool):
    """测试统一新闻工具创建"""
    print_section("3. 测试统一新闻工具创建")
    
    try:
        unified_news_tool = create_unified_news_tool(toolkit)
        print_result(True, "统一新闻工具创建成功")
        
        # 检查工具属性
        if hasattr(unified_news_tool, 'name'):
            print_result(True, f"工具名称: {unified_news_tool.name}")
        if hasattr(unified_news_tool, 'description'):
            desc = unified_news_tool.description[:100] if unified_news_tool.description else ""
            print_result(True, f"工具描述: {desc}...")
        
        return True, unified_news_tool
    except Exception as e:
        print_result(False, "统一新闻工具创建失败", f"错误: {e}")
        print(f"   堆栈跟踪:\n{traceback.format_exc()}")
        return False, None


def test_database_connection():
    """测试数据库连接"""
    print_section("4. 测试数据库连接")
    
    try:
        from tradingagents.dataflows.cache.app_adapter import get_mongodb_client
        client = get_mongodb_client()
        
        if client:
            print_result(True, "MongoDB客户端创建成功")
            
            # 测试连接
            try:
                db = client.get_database('tradingagents')
                collection = db.stock_news
                count = collection.count_documents({})
                print_result(True, f"数据库连接成功，stock_news集合有 {count} 条记录")
                return True
            except Exception as e:
                print_result(False, "数据库查询失败", f"错误: {e}")
                return False
        else:
            print_result(False, "MongoDB客户端创建失败", "返回None")
            return False
    except Exception as e:
        print_result(False, "数据库连接测试失败", f"错误: {e}")
        print(f"   堆栈跟踪:\n{traceback.format_exc()}")
        return False


def test_news_query(stock_code: str):
    """测试新闻查询"""
    print_section(f"5. 测试新闻查询 (股票代码: {stock_code})")
    
    try:
        from tradingagents.dataflows.cache.app_adapter import get_mongodb_client
        from datetime import timedelta
        
        client = get_mongodb_client()
        if not client:
            print_result(False, "无法连接到MongoDB", "跳过数据库查询测试")
            return False
        
        db = client.get_database('tradingagents')
        collection = db.stock_news
        
        # 标准化股票代码
        clean_code = stock_code.replace('.SH', '').replace('.SZ', '').replace('.SS', '')\
                               .replace('.XSHE', '').replace('.XSHG', '').replace('.HK', '')
        
        print(f"   清理后的股票代码: {clean_code}")
        
        # 尝试多种查询方式
        query_list = [
            {'symbol': clean_code},
            {'symbol': stock_code},
            {'symbols': clean_code},
        ]
        
        found_news = False
        for query in query_list:
            try:
                cursor = collection.find(query).sort('publish_time', -1).limit(5)
                news_items = list(cursor)
                if news_items:
                    print_result(True, f"使用查询 {query} 找到 {len(news_items)} 条新闻")
                    found_news = True
                    
                    # 显示第一条新闻的标题
                    if news_items:
                        first_news = news_items[0]
                        title = first_news.get('title', '无标题')
                        publish_time = first_news.get('publish_time', '未知时间')
                        print(f"   示例新闻: {title} ({publish_time})")
                    break
            except Exception as e:
                print_result(False, f"查询 {query} 失败", f"错误: {e}")
        
        if not found_news:
            print_result(False, "数据库中没有找到新闻", f"股票代码: {stock_code}")
        
        return found_news
    except Exception as e:
        print_result(False, "新闻查询测试失败", f"错误: {e}")
        print(f"   堆栈跟踪:\n{traceback.format_exc()}")
        return False


def test_akshare_provider():
    """测试AKShare Provider"""
    print_section("6. 测试AKShare Provider")
    
    try:
        from tradingagents.dataflows.providers.china.akshare import AKShareProvider
        provider = AKShareProvider()
        print_result(True, "AKShare Provider创建成功")
        
        # 检查是否有get_stock_news方法
        if hasattr(provider, 'get_stock_news'):
            print_result(True, "Provider有get_stock_news方法")
        else:
            print_result(False, "Provider没有get_stock_news方法")
        
        return True, provider
    except Exception as e:
        print_result(False, "AKShare Provider测试失败", f"错误: {e}")
        print(f"   堆栈跟踪:\n{traceback.format_exc()}")
        return False, None


def test_unified_news_call(unified_news_tool, stock_code: str, max_news: int = 10):
    """测试统一新闻工具调用"""
    print_section(f"7. 测试统一新闻工具调用 (股票代码: {stock_code}, max_news: {max_news})")
    
    try:
        print(f"   调用参数:")
        print(f"     stock_code: {stock_code}")
        print(f"     max_news: {max_news}")
        
        # 调用工具
        print(f"   正在调用工具...")
        result = unified_news_tool(stock_code=stock_code, max_news=max_news)
        
        if result:
            print_result(True, "工具调用成功", f"返回结果长度: {len(result)} 字符")
            
            # 显示结果预览
            preview = result[:500] if len(result) > 500 else result
            print(f"\n   结果预览 (前500字符):")
            print(f"   {preview}")
            
            # 检查结果是否包含错误信息
            if "❌" in result or "失败" in result or "错误" in result:
                print_result(False, "返回结果包含错误信息", "请查看上面的结果预览")
            
            return True, result
        else:
            print_result(False, "工具调用返回空结果", "")
            return False, None
            
    except Exception as e:
        print_result(False, "工具调用失败", f"错误: {e}")
        print(f"   错误类型: {type(e).__name__}")
        print(f"   堆栈跟踪:\n{traceback.format_exc()}")
        return False, None


def test_toolkit_tools(toolkit):
    """测试工具包中的各个工具"""
    print_section("8. 测试工具包中的各个工具")
    
    test_stock_code = "002549"
    curr_date = datetime.now().strftime("%Y-%m-%d")
    
    # 测试东方财富实时新闻
    try:
        if hasattr(toolkit, 'get_realtime_stock_news'):
            print(f"\n   测试: get_realtime_stock_news")
            result = toolkit.get_realtime_stock_news.invoke({
                "ticker": test_stock_code,
                "curr_date": curr_date
            })
            if result:
                print_result(True, "get_realtime_stock_news", f"返回 {len(result)} 字符")
            else:
                print_result(False, "get_realtime_stock_news", "返回空结果")
        else:
            print_result(False, "get_realtime_stock_news", "工具不存在")
    except Exception as e:
        print_result(False, "get_realtime_stock_news", f"错误: {e}")
    
    # 测试Google新闻
    try:
        if hasattr(toolkit, 'get_google_news'):
            print(f"\n   测试: get_google_news")
            query = f"{test_stock_code} 股票 新闻"
            result = toolkit.get_google_news.invoke({
                "query": query,
                "curr_date": curr_date
            })
            if result:
                print_result(True, "get_google_news", f"返回 {len(result)} 字符")
            else:
                print_result(False, "get_google_news", "返回空结果")
        else:
            print_result(False, "get_google_news", "工具不存在")
    except Exception as e:
        print_result(False, "get_google_news", f"错误: {e}")
    
    # 测试OpenAI全球新闻
    try:
        if hasattr(toolkit, 'get_global_news_openai'):
            print(f"\n   测试: get_global_news_openai")
            result = toolkit.get_global_news_openai.invoke({
                "curr_date": curr_date
            })
            if result:
                print_result(True, "get_global_news_openai", f"返回 {len(result)} 字符")
            else:
                print_result(False, "get_global_news_openai", "返回空结果")
        else:
            print_result(False, "get_global_news_openai", "工具不存在")
    except Exception as e:
        print_result(False, "get_global_news_openai", f"错误: {e}")


def generate_summary():
    """生成诊断总结"""
    print_section("9. 诊断总结")
    
    print("\n检查清单:")
    print("   □ 统一新闻工具模块是否导入成功")
    print("   □ 工具包是否创建成功")
    print("   □ 统一新闻工具是否创建成功")
    print("   □ 数据库连接是否正常")
    print("   □ 数据库中是否有新闻数据")
    print("   □ AKShare Provider是否可用")
    print("   □ 工具调用是否成功")
    
    print("\n常见问题解决方案:")
    print("   1. 模块导入失败:")
    print("      - 检查Python路径是否正确")
    print("      - 检查依赖是否安装")
    print("   2. 数据库连接失败:")
    print("      - 检查MongoDB是否运行")
    print("      - 检查MONGODB_CONNECTION_STRING配置")
    print("   3. 数据库中没有新闻:")
    print("      - 运行新闻同步脚本")
    print("      - 检查股票代码是否正确")
    print("   4. AKShare Provider失败:")
    print("      - 检查网络连接")
    print("      - 检查AKShare库是否安装")
    print("   5. 工具调用失败:")
    print("      - 查看详细错误信息")
    print("      - 检查工具参数是否正确")


def main():
    """主函数"""
    print("\n" + "=" * 80)
    print("  get_stock_news_unified 诊断工具")
    print("=" * 80)
    
    stock_code = "002549"
    max_news = 10
    
    print(f"\n测试参数:")
    print(f"  股票代码: {stock_code}")
    print(f"  最大新闻数: {max_news}")
    
    # 1. 测试导入
    import_ok, create_unified_news_tool = test_import()
    if not import_ok:
        print("\n❌ 模块导入失败，无法继续测试")
        return
    
    # 2. 测试工具包创建
    toolkit_ok, toolkit = test_toolkit_creation()
    if not toolkit_ok:
        print("\n❌ 工具包创建失败，无法继续测试")
        return
    
    # 3. 测试统一新闻工具创建
    tool_ok, unified_news_tool = test_unified_news_tool_creation(toolkit, create_unified_news_tool)
    if not tool_ok:
        print("\n❌ 统一新闻工具创建失败，无法继续测试")
        return
    
    # 4. 测试数据库连接
    db_ok = test_database_connection()
    
    # 5. 测试新闻查询
    if db_ok:
        test_news_query(stock_code)
    
    # 6. 测试AKShare Provider
    akshare_ok, provider = test_akshare_provider()
    
    # 7. 测试工具包中的各个工具
    test_toolkit_tools(toolkit)
    
    # 8. 测试统一新闻工具调用
    call_ok, result = test_unified_news_call(unified_news_tool, stock_code, max_news)
    
    # 9. 生成总结
    generate_summary()
    
    print("\n" + "=" * 80)
    print("  诊断完成")
    print("=" * 80 + "\n")
    
    if call_ok:
        print("\n✅ 工具调用成功！")
    else:
        print("\n❌ 工具调用失败，请查看上面的错误信息")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ 用户中断")
    except Exception as e:
        print(f"\n\n❌ 诊断过程发生错误: {e}")
        print(traceback.format_exc())

