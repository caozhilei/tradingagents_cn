#!/usr/bin/env python3
"""
清理TDX数据源配置中的endpoint字段
TDX数据源不需要API端点，此脚本用于清理数据库中已存在的endpoint值
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import get_database
from app.models.config import SystemConfig
from bson import ObjectId
import asyncio

async def clean_tdx_endpoint():
    """清理TDX数据源配置中的endpoint字段"""
    db = await get_database()
    collection = db["system_configs"]
    
    # 查找所有系统配置
    configs = await collection.find({}).to_list(length=None)
    
    updated_count = 0
    
    for config_doc in configs:
        try:
            # 解析配置
            config = SystemConfig(**config_doc)
            
            # 检查是否有TDX数据源
            updated = False
            for ds_config in config.data_source_configs:
                ds_type = ds_config.type.value if hasattr(ds_config.type, 'value') else str(ds_config.type)
                if ds_type == 'tdx' and ds_config.endpoint:
                    print(f"🔍 找到TDX数据源 '{ds_config.name}'，当前endpoint: {ds_config.endpoint}")
                    # 设置为None
                    ds_config.endpoint = None
                    updated = True
                    print(f"✅ 已清理TDX数据源 '{ds_config.name}' 的endpoint字段")
            
            if updated:
                # 更新数据库
                config_dict = config.model_dump(by_alias=True, exclude={'id'})
                config_dict['_id'] = config_doc['_id']
                
                await collection.update_one(
                    {"_id": config_doc['_id']},
                    {"$set": config_dict}
                )
                updated_count += 1
                print(f"✅ 已更新配置文档: {config_doc['_id']}")
        except Exception as e:
            print(f"❌ 处理配置文档失败: {e}")
            continue
    
    print(f"\n✅ 完成！共更新 {updated_count} 个配置文档")
    return updated_count

if __name__ == "__main__":
    print("🔧 开始清理TDX数据源配置中的endpoint字段...")
    asyncio.run(clean_tdx_endpoint())

