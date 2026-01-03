#!/usr/bin/env python3
"""
检查ETH缓存数据的脚本
"""

import os
from pathlib import Path

def check_cache_dirs():
    """检查可能的缓存目录"""
    cache_dirs = [
        Path.home() / '.tradingagents' / 'cache',
        Path('/tmp/tradingagents_cache'),
        Path('/app/cache'),
        Path('/app/data/cache'),
        Path('/root/.cache/tradingagents')
    ]

    print('检查缓存目录:')
    for cache_dir in cache_dirs:
        if cache_dir.exists():
            print(f'  ✓ {cache_dir} 存在')
            try:
                file_count = len(list(cache_dir.rglob('*')))
                print(f'    文件数量: {file_count}')

                # 查找ETH相关文件
                eth_files = []
                for file_path in cache_dir.rglob('*'):
                    if file_path.is_file() and 'ETH' in file_path.name.upper():
                        eth_files.append(file_path)

                if eth_files:
                    print(f'    ETH相关文件: {len(eth_files)} 个')
                    for f in eth_files[:3]:  # 只显示前3个
                        print(f'      - {f.name}')

            except Exception as e:
                print(f'    检查失败: {e}')
        else:
            print(f'  ✗ {cache_dir} 不存在')

if __name__ == "__main__":
    check_cache_dirs()
