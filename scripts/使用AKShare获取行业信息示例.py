#!/usr/bin/env python3
"""
使用AKShare获取股票行业信息的正确示例

这是对你提供的代码的改进版本，支持沪深两市，使用正确的API接口
"""

import sys
import os
from pathlib import Path
import re

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import akshare as ak
import pandas as pd

# 从.env文件读取代理配置并设置到环境变量
def setup_proxy_from_env():
    """从.env文件读取代理配置并设置到环境变量"""
    env_file = project_root / ".env"
    if env_file.exists():
        try:
            with open(env_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 提取NO_PROXY
            no_proxy_match = re.search(r'NO_PROXY=(.+)', content, re.MULTILINE)
            if no_proxy_match:
                no_proxy = no_proxy_match.group(1).strip().strip('"\'')
                os.environ['NO_PROXY'] = no_proxy
                os.environ['no_proxy'] = no_proxy
                print(f"[OK] 已设置NO_PROXY: {no_proxy}")
            
            # 提取HTTP_PROXY和HTTPS_PROXY（如果需要）
            http_match = re.search(r'HTTP_PROXY=(.+)', content, re.MULTILINE)
            if http_match:
                http_proxy = http_match.group(1).strip().strip('"\'')
                os.environ['HTTP_PROXY'] = http_proxy
                os.environ['http_proxy'] = http_proxy
            
            https_match = re.search(r'HTTPS_PROXY=(.+)', content, re.MULTILINE)
            if https_match:
                https_proxy = https_match.group(1).strip().strip('"\'')
                os.environ['HTTPS_PROXY'] = https_proxy
                os.environ['https_proxy'] = https_proxy
        except Exception as e:
            print(f"[WARN] 读取代理配置失败: {e}")

# 设置代理环境变量
setup_proxy_from_env()


def get_stock_industry_example(stock_code: str):
    """
    使用AKShare获取股票行业信息的正确方法
    
    Args:
        stock_code: 6位股票代码，如 "600519"（贵州茅台，上海）或 "000001"（平安银行，深圳）
    
    Returns:
        dict: 包含代码、名称、行业的字典
    """
    print(f"\n{'='*60}")
    print(f"[获取] 股票 {stock_code} 的行业信息")
    print(f"{'='*60}")
    
    try:
        # ⭐ 推荐方法：使用 stock_individual_info_em 接口
        # 这个接口支持沪深两市，且包含完整的行业信息
        stock_info_df = ak.stock_individual_info_em(symbol=stock_code)
        
        if stock_info_df is None or stock_info_df.empty:
            print(f"[错误] 未获取到股票 {stock_code} 的信息")
            return None
        
        # 提取信息
        result = {
            'code': stock_code,
            'name': '',
            'industry': '未知'
        }
        
        # 提取股票简称
        name_row = stock_info_df[stock_info_df['item'] == '股票简称']
        if not name_row.empty:
            result['name'] = str(name_row['value'].iloc[0])
        
        # 提取所属行业（关键字段）
        industry_row = stock_info_df[stock_info_df['item'] == '所属行业']
        if not industry_row.empty:
            result['industry'] = str(industry_row['value'].iloc[0])
        
        # 显示结果
        print(f"\n[成功] 获取成功:")
        print(f"   代码: {result['code']}")
        print(f"   名称: {result['name']}")
        print(f"   行业: {result['industry']}")
        
        # 显示所有可用信息（可选）
        print(f"\n[信息] 完整信息:")
        print(stock_info_df[['item', 'value']].to_string(index=False))
        
        return result
        
    except Exception as e:
        print(f"[错误] 获取失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def get_stock_industry_from_list_example(stock_code: str):
    """
    备选方法：从股票列表获取（仅深圳市场可用，且可能不包含行业信息）
    
    注意：此方法仅适用于深圳市场，且API可能已变更
    """
    print(f"\n{'='*60}")
    print(f"[备选] 尝试从股票列表获取 {stock_code} 的信息")
    print(f"{'='*60}")
    
    # 判断市场
    if stock_code.startswith(('000', '002', '003', '300')):
        # 深圳市场
        try:
            # ⚠️ 注意：stock_info_sz_name_code 接口可能已变更
            # 新版本可能不再支持 indicator 参数
            stock_list_df = ak.stock_info_sz_name_code()
            
            if stock_list_df is None or stock_list_df.empty:
                print("[错误] 股票列表为空")
                return None
            
            # 查找目标股票
            target = stock_list_df[stock_list_df['代码'] == stock_code]
            
            if target.empty:
                print(f"[错误] 未找到股票 {stock_code}")
                return None
            
            print(f"\n[成功] 找到股票:")
            print(target[['代码', '简称', '所属行业']].to_string(index=False))
            
            return {
                'code': target.iloc[0]['代码'],
                'name': target.iloc[0]['简称'],
                'industry': target.iloc[0].get('所属行业', '未知')
            }
            
        except Exception as e:
            print(f"[警告] 接口可能已变更或需要不同参数: {e}")
            print("[提示] 建议使用 stock_individual_info_em 接口（更可靠）")
            return None
    else:
        print(f"[警告] 股票 {stock_code} 是上海市场，此方法仅支持深圳市场")
        print("[提示] 建议使用 stock_individual_info_em 接口（支持沪深两市）")
        return None


if __name__ == "__main__":
    print("=" * 80)
    print("[示例] AKShare获取股票行业信息示例")
    print("=" * 80)
    
    # 测试多只股票
    test_stocks = [
        "600519",  # 贵州茅台（上海）
        "000001",  # 平安银行（深圳）
    ]
    
    for code in test_stocks:
        # 方法1：推荐方法（支持沪深两市）
        result = get_stock_industry_example(code)
        
        # 方法2：备选方法（仅深圳，可能不可用）
        if code.startswith(('000', '002', '003', '300')):
            get_stock_industry_from_list_example(code)
    
    print("\n" + "=" * 80)
    print("[总结]")
    print("=" * 80)
    print("""
[推荐] 推荐方法：
   ak.stock_individual_info_em(symbol=stock_code)
   - 支持沪深两市
   - 包含完整的行业信息
   - 接口稳定可靠
   
[注意] 注意事项：
   1. 你的原始代码使用了 stock_info_sz_name_code(indicator="A股列表")
      - 这个接口仅支持深圳市场
      - indicator 参数在新版本可能已移除
      - 600519 是上海股票，不适用此接口
   
   2. 网络代理问题：
      - 如果遇到代理连接错误，确保 NO_PROXY 配置正确
      - 运行修复脚本：python scripts/修复TDX行业查询问题.py
    """)

