#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接连接MongoDB，将TDX数据源添加到数据库配置中
绕过.env文件加载问题
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def add_tdx_to_database_direct():
    """直接连接MongoDB添加TDX数据源"""
    try:
        from pymongo import MongoClient
        from datetime import datetime
        
        # 直接连接MongoDB（使用Docker环境配置）
        mongodb_url = "mongodb://admin:tradingagents123@localhost:27017/tradingagents?authSource=admin"
        
        print("🔌 连接MongoDB...")
        client = MongoClient(mongodb_url, serverSelectionTimeoutMS=5000)
        
        # 测试连接
        client.admin.command('ping')
        print("✅ MongoDB连接成功")
        
        db = client['tradingagents']
        config_collection = db['system_configs']
        
        # 获取激活的配置
        config = config_collection.find_one({"is_active": True})
        
        if not config:
            print("⚠️ 数据库中没有激活的配置")
            print("💡 建议：通过前端界面初始化配置，或重启后端服务自动创建")
            return False
        
        print(f"📊 找到激活配置，版本: {config.get('version', '未知')}")
        
        # 检查是否已有TDX配置
        data_source_configs = config.get('data_source_configs', [])
        tdx_exists = any(
            ds.get('type') == 'tdx' or 
            ds.get('name', '').upper() == 'TDX' or
            ds.get('name', '').lower() == 'tdx'
            for ds in data_source_configs
        )
        
        updated = False
        
        if tdx_exists:
            print("✅ TDX数据源已存在于数据库配置中")
            # 更新TDX配置确保正确
            for i, ds in enumerate(data_source_configs):
                if ds.get('type') == 'tdx' or ds.get('name', '').upper() == 'TDX':
                    old_priority = ds.get('priority', 0)
                    data_source_configs[i] = {
                        'name': 'TDX',
                        'type': 'tdx',
                        'timeout': 30,
                        'rate_limit': 100,
                        'enabled': True,
                        'priority': 10,  # 最高优先级
                        'description': '通达信实时行情接口，提供A股实时行情和历史K线数据，完全免费且无需API Key',
                        'config_params': {},
                        'display_name': '通达信',
                        'provider': '通达信',
                        'created_at': ds.get('created_at', datetime.utcnow()),
                        'updated_at': datetime.utcnow()
                    }
                    if old_priority != 10:
                        print(f"✅ 已更新TDX数据源配置（优先级: {old_priority} -> 10）")
                    else:
                        print("✅ TDX数据源配置已是最新")
                    updated = True
                    break
        else:
            # 添加TDX配置
            tdx_config = {
                'name': 'TDX',
                'type': 'tdx',
                'timeout': 30,
                'rate_limit': 100,
                'enabled': True,
                'priority': 10,  # 最高优先级
                'description': '通达信实时行情接口，提供A股实时行情和历史K线数据，完全免费且无需API Key',
                'config_params': {},
                'display_name': '通达信',
                'provider': '通达信',
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            }
            data_source_configs.append(tdx_config)
            print("✅ 已添加TDX数据源配置")
            updated = True
        
        # 更新默认数据源为TDX
        if config.get('default_data_source', '').upper() != 'TDX':
            config['default_data_source'] = 'TDX'
            print("✅ 已设置TDX为默认数据源")
            updated = True
        
        # 按优先级排序
        data_source_configs.sort(key=lambda x: x.get('priority', 0), reverse=True)
        
        if updated:
            # 更新配置
            config['data_source_configs'] = data_source_configs
            config['updated_at'] = datetime.utcnow()
            
            result = config_collection.update_one(
                {"is_active": True},
                {"$set": config}
            )
            
            if result.modified_count > 0:
                print("✅ 数据库配置已更新")
            else:
                print("⚠️ 配置未修改（可能内容相同）")
        
        print(f"\n📊 当前数据源配置:")
        print(f"   数据源数量: {len(data_source_configs)}")
        print(f"   默认数据源: {config.get('default_data_source')}")
        print(f"\n   数据源列表（按优先级排序）:")
        for i, ds in enumerate(data_source_configs, 1):
            enabled = "✅" if ds.get('enabled') else "❌"
            print(f"   {i}. {enabled} {ds.get('display_name', ds.get('name'))} (优先级: {ds.get('priority', 0)}, 类型: {ds.get('type')})")
        
        client.close()
        return True
        
    except Exception as e:
        print(f"❌ 更新数据库配置失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("="*80)
    print("🔧 将TDX数据源添加到数据库配置（直接连接MongoDB）")
    print("="*80)
    
    success = add_tdx_to_database_direct()
    
    if success:
        print("\n✅ 完成！TDX数据源已添加到数据库配置")
        print("\n💡 下一步:")
        print("   1. 刷新前端页面 (http://localhost:3000/settings/sync)")
        print("   2. 应该能看到TDX数据源配置")
        print("   3. 如果还是看不到，检查后端日志")
    else:
        print("\n❌ 操作失败，请检查错误信息")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

