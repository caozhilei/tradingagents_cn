#!/usr/bin/env python3
"""
清理ETH数字货币缓存数据的脚本

此脚本会清理tradingagents缓存中所有与ETH相关的缓存数据，
确保下次分析时获取最新数据。
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tradingagents.utils.logging_manager import get_logger
logger = get_logger('cache_cleaner')

class ETHCacheCleaner:
    """ETH缓存清理器"""

    def __init__(self):
        self.cache_dir = Path.home() / '.tradingagents' / 'cache'
        self.cleared_count = 0

    def find_eth_cache_files(self):
        """查找所有包含ETH的缓存文件"""
        eth_files = []

        if not self.cache_dir.exists():
            logger.info("缓存目录不存在，无需清理")
            return eth_files

        # 遍历所有缓存文件
        for cache_file in self.cache_dir.rglob("*"):
            if cache_file.is_file():
                try:
                    # 检查文件名是否包含ETH
                    if 'ETH' in cache_file.name.upper():
                        eth_files.append(cache_file)
                        continue

                    # 检查文件内容是否包含ETH
                    if cache_file.suffix == '.json':
                        try:
                            with open(cache_file, 'r', encoding='utf-8') as f:
                                content = f.read()
                                if '"ETH"' in content or "'ETH'" in content:
                                    eth_files.append(cache_file)
                        except:
                            pass

                except Exception as e:
                    logger.debug(f"检查文件时出错: {cache_file} - {e}")

        return eth_files

    def find_eth_metadata(self):
        """查找包含ETH的元数据文件"""
        eth_metadata = []

        if not self.cache_dir.exists():
            logger.info("缓存目录不存在，无需清理")
            return eth_metadata

        # 查找所有元数据文件
        for meta_file in self.cache_dir.rglob("*_meta.json"):
            try:
                with open(meta_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)

                # 检查元数据中的各种字段
                symbol = metadata.get('symbol', '').upper()
                code = metadata.get('code', '').upper()
                ticker = metadata.get('ticker', '').upper()

                if 'ETH' in symbol or 'ETH' in code or 'ETH' in ticker:
                    eth_metadata.append(meta_file)

            except Exception as e:
                logger.debug(f"读取元数据文件出错: {meta_file} - {e}")

        return eth_metadata

    def clear_eth_cache(self):
        """清理所有ETH相关的缓存"""
        logger.info("🔍 开始查找ETH相关的缓存文件...")

        # 查找直接包含ETH的文件
        eth_files = self.find_eth_cache_files()
        logger.info(f"找到 {len(eth_files)} 个直接包含ETH的缓存文件")

        # 查找包含ETH的元数据文件
        eth_metadata = self.find_eth_metadata()
        logger.info(f"找到 {len(eth_metadata)} 个ETH相关的元数据文件")

        # 合并所有要删除的文件
        files_to_delete = set(eth_files + eth_metadata)

        logger.info(f"📋 总共需要清理 {len(files_to_delete)} 个文件")

        # 删除文件
        for file_path in files_to_delete:
            try:
                if file_path.exists():
                    file_path.unlink()
                    self.cleared_count += 1
                    logger.debug(f"🗑️ 已删除: {file_path}")
            except Exception as e:
                logger.warning(f"删除文件失败: {file_path} - {e}")

        logger.info(f"✅ 缓存清理完成，共清理了 {self.cleared_count} 个文件")

    def clear_mongodb_eth_data(self):
        """清理MongoDB中的ETH数据"""
        try:
            from app.core.database import init_database, get_mongo_db
            import asyncio

            async def clear_mongo_data():
                await init_database()
                db = get_mongo_db()

                collections_to_clear = [
                    'stock_basic_info',
                    'stock_daily_quotes',
                    'stock_financial_data',
                    'market_quotes',
                    'mcp_queries',
                    'analysis_reports'
                ]

                cleared_records = 0

                for collection_name in collections_to_clear:
                    try:
                        # 删除所有包含ETH的记录
                        result = await db[collection_name].delete_many({
                            '$or': [
                                {'code': {'$regex': 'ETH', '$options': 'i'}},
                                {'symbol': {'$regex': 'ETH', '$options': 'i'}},
                                {'ticker': {'$regex': 'ETH', '$options': 'i'}},
                                {'stock_code': {'$regex': 'ETH', '$options': 'i'}},
                                {'content': {'$regex': 'ETH', '$options': 'i'}},  # 分析报告内容
                                {'query': {'$regex': 'ETH', '$options': 'i'}}  # MCP查询
                            ]
                        })

                        if result.deleted_count > 0:
                            cleared_records += result.deleted_count
                            logger.info(f"🗑️ 从 {collection_name} 删除了 {result.deleted_count} 条ETH记录")

                    except Exception as e:
                        logger.warning(f"清理集合 {collection_name} 时出错: {e}")

                logger.info(f"✅ MongoDB数据清理完成，共清理了 {cleared_records} 条记录")

            # 运行异步清理
            asyncio.run(clear_mongo_data())

        except Exception as e:
            logger.error(f"清理MongoDB数据时出错: {e}")

def main():
    """主函数"""
    logger.info("🚀 开始清理ETH缓存数据...")

    cleaner = ETHCacheCleaner()

    # 清理文件缓存
    cleaner.clear_eth_cache()

    # 清理MongoDB数据
    cleaner.clear_mongodb_eth_data()

    logger.info(f"🎉 ETH缓存清理完成！总共清理了 {cleaner.cleared_count} 个文件")

if __name__ == "__main__":
    main()
