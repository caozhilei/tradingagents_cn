#!/usr/bin/env python3
"""
测试使用AKShare获取股票行业信息
支持上海和深圳两个市场
"""

import akshare as ak
import pandas as pd

def get_stock_industry_akshare(stock_code: str):
    """
    使用AKShare获取股票的行业信息（支持沪深两市）
    
    Args:
        stock_code: 6位股票代码，如 "600519", "000001"
    
    Returns:
        dict: 包含代码、名称、行业的字典
    """
    try:
        result = {
            'code': stock_code,
            'name': '',
            'industry': '未知'
        }
        
        # 判断市场
        if stock_code.startswith(('600', '601', '603', '605', '688')):
            # 上海市场
            print(f"📊 获取上海股票 {stock_code} 的行业信息...")
            
            # 方法1: 使用个股信息接口（推荐，最可靠）
            # 这是项目中使用的方法
            try:
                stock_info = ak.stock_individual_info_em(symbol=stock_code)
                if stock_info is not None and not stock_info.empty:
                    # 提取行业信息
                    industry_row = stock_info[stock_info['item'] == '所属行业']
                    if not industry_row.empty:
                        result['industry'] = str(industry_row['value'].iloc[0])
                    
                    # 提取名称
                    name_row = stock_info[stock_info['item'] == '股票简称']
                    if not name_row.empty:
                        result['name'] = str(name_row['value'].iloc[0])
                    
                    if result['industry'] != '未知':
                        print(f"✅ 方法1成功: {result['name']} - {result['industry']}")
                        return result
            except Exception as e:
                print(f"⚠️  方法1失败: {e}")
            
            # 方法2: 使用个股信息接口
            try:
                stock_info = ak.stock_individual_info_em(symbol=stock_code)
                if stock_info is not None and not stock_info.empty:
                    # 提取行业信息
                    industry_row = stock_info[stock_info['item'] == '所属行业']
                    if not industry_row.empty:
                        result['industry'] = str(industry_row['value'].iloc[0])
                    
                    # 提取名称
                    name_row = stock_info[stock_info['item'] == '股票简称']
                    if not name_row.empty:
                        result['name'] = str(name_row['value'].iloc[0])
                    
                    print(f"✅ 方法2成功: {result['name']} - {result['industry']}")
                    return result
            except Exception as e:
                print(f"⚠️  方法2失败: {e}")
        
        elif stock_code.startswith(('000', '002', '003', '300')):
            # 深圳市场
            print(f"📊 获取深圳股票 {stock_code} 的行业信息...")
            
            # 方法1: 使用个股信息接口（推荐，最可靠）
            # 这是项目中使用的方法
            try:
                stock_info = ak.stock_individual_info_em(symbol=stock_code)
                if stock_info is not None and not stock_info.empty:
                    # 提取行业信息
                    industry_row = stock_info[stock_info['item'] == '所属行业']
                    if not industry_row.empty:
                        result['industry'] = str(industry_row['value'].iloc[0])
                    
                    # 提取名称
                    name_row = stock_info[stock_info['item'] == '股票简称']
                    if not name_row.empty:
                        result['name'] = str(name_row['value'].iloc[0])
                    
                    if result['industry'] != '未知':
                        print(f"✅ 方法1成功: {result['name']} - {result['industry']}")
                        return result
            except Exception as e:
                print(f"⚠️  方法1失败: {e}")
            
            # 方法2: 尝试使用股票列表接口（备选方案）
            # 注意：此接口可能不包含行业信息
            try:
                stock_list = ak.stock_info_a_code_name()
                if stock_list is not None and not stock_list.empty:
                    target = stock_list[stock_list['code'] == stock_code]
                    if not target.empty:
                        result['name'] = target.iloc[0].get('name', '')
                        print(f"✅ 方法2成功: {result['name']} (无行业信息)")
            except Exception as e:
                print(f"⚠️  方法2失败: {e}")
        
        else:
            print(f"⚠️  未知的股票代码格式: {stock_code}")
            return result
        
        print(f"❌ 所有方法都失败，无法获取 {stock_code} 的行业信息")
        return result
        
    except Exception as e:
        print(f"❌ 获取股票 {stock_code} 行业信息失败: {e}")
        return {'code': stock_code, 'name': '', 'industry': '未知'}


def test_multiple_stocks():
    """测试多只股票"""
    test_codes = [
        "600519",  # 贵州茅台 (上海)
        "000001",  # 平安银行 (深圳)
        "000002",  # 万科A (深圳)
        "600036",  # 招商银行 (上海)
        "300750",  # 宁德时代 (创业板)
    ]
    
    print("=" * 80)
    print("🧪 测试获取多只股票的行业信息")
    print("=" * 80)
    print()
    
    results = []
    for code in test_codes:
        print(f"\n📋 处理股票: {code}")
        print("-" * 80)
        result = get_stock_industry_akshare(code)
        results.append(result)
        print()
    
    # 汇总结果
    print("=" * 80)
    print("📊 测试结果汇总")
    print("=" * 80)
    df = pd.DataFrame(results)
    print(df.to_string(index=False))
    print()


if __name__ == "__main__":
    # 测试单只股票
    print("=" * 80)
    print("测试1: 获取单只股票行业信息")
    print("=" * 80)
    result = get_stock_industry_akshare("600519")
    print(f"\n结果: {result}")
    print()
    
    # 测试多只股票
    test_multiple_stocks()
