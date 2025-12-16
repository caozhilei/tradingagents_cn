#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将TDX数据源添加到数据库配置中
如果数据库中已有配置，则更新；如果没有，则添加
"""

import sys
import asyncio
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

async def add_tdx_to_database():
    """将TDX数据源添加到数据库配置"""
    try:
        from app.core.database import get_mongo_db
        from app.models.config import DataSourceConfig, DataSourceType
        
        db = get_mongo_db()
        config_collection = db.system_configs
        
        # 获取激活的配置
        config = await config_collection.find_one({"is_active": True})
        
        if not config:
            print("⚠️ 数据库中没有激活的配置，将创建新配置")
            # 使用ConfigService创建默认配置
            from app.services.config_service import ConfigService
            config_service = ConfigService()
            config = await config_service._create_default_config()
            config_dict = config.model_dump()
            config_dict['is_active'] = True
            config_dict['version'] = 1
            await config_collection.insert_one(config_dict)
            print("✅ 已创建新配置，包含TDX数据源")
            return
        
        print(f"📊 找到激活配置，版本: {config.get('version', '未知')}")
        
        # 检查是否已有TDX配置
        data_source_configs = config.get('data_source_configs', [])
        tdx_exists = any(ds.get('type') == 'tdx' or ds.get('name', '').upper() == 'TDX' for ds in data_source_configs)
        
        if tdx_exists:
            print("✅ TDX数据源已存在于数据库配置中")
            # 更新TDX配置确保正确
            for i, ds in enumerate(data_source_configs):
                if ds.get('type') == 'tdx' or ds.get('name', '').upper() == 'TDX':
                    data_source_configs[i] = {
                        'name': 'TDX',
                        'type': 'tdx',
                        'timeout': 30,
                        'rate_limit': 100,
                        'enabled': True,
                        'priority': 10,
                        'description': '通达信实时行情接口，提供A股实时行情和历史K线数据，完全免费且无需API Key',
                        'config_params': {},
                        'display_name': '通达信',
                        'provider': '通达信'
                    }
                    print("✅ 已更新TDX数据源配置")
                    break
        else:
            # 添加TDX配置
            tdx_config = {
                'name': 'TDX',
                'type': 'tdx',
                'timeout': 30,
                'rate_limit': 100,
                'enabled': True,
                'priority': 10,
                'description': '通达信实时行情接口，提供A股实时行情和历史K线数据，完全免费且无需API Key',
                'config_params': {},
                'display_name': '通达信',
                'provider': '通达信'
            }
            data_source_configs.append(tdx_config)
            print("✅ 已添加TDX数据源配置")
        
        # 更新默认数据源为TDX
        if config.get('default_data_source', '').upper() != 'TDX':
            config['default_data_source'] = 'TDX'
            print("✅ 已设置TDX为默认数据源")
        
        # 按优先级排序
        data_source_configs.sort(key=lambda x: x.get('priority', 0), reverse=True)
        
        # 更新配置
        config['data_source_configs'] = data_source_configs
        config['updated_at'] = asyncio.get_event_loop().time()
        
        await config_collection.update_one(
            {"is_active": True},
            {"$set": config}
        )
        
        print("✅ 数据库配置已更新")
        print(f"   数据源数量: {len(data_source_configs)}")
        print(f"   默认数据源: {config.get('default_data_source')}")
        
    except Exception as e:
        print(f"❌ 更新数据库配置失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

async def main():
    """主函数"""
    print("="*80)
    print("🔧 将TDX数据源添加到数据库配置")
    print("="*80)
    
    success = await add_tdx_to_database()
    
    if success:
        print("\n✅ 完成！TDX数据源已添加到数据库配置")
        print("\n💡 下一步:")
        print("   1. 刷新前端页面 (http://localhost:3000/settings/sync)")
        print("   2. 应该能看到TDX数据源配置")
    else:
        print("\n❌ 操作失败，请检查错误信息")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))

