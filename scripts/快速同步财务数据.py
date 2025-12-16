#!/usr/bin/env python3
"""
快速同步财务数据脚本

用于手动触发财务数据同步，解决基本面数据不足的问题
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.worker.financial_data_sync_service import get_financial_sync_service
from app.core.config import settings


async def sync_financial_data_for_stocks(symbols=None, data_sources=None):
    """
    同步财务数据
    
    Args:
        symbols: 股票代码列表，None表示同步所有股票
        data_sources: 数据源列表，None表示使用所有可用数据源
    """
    print("="*70)
    print("🔄 开始同步财务数据")
    print("="*70)
    
    if symbols:
        print(f"📊 同步股票: {', '.join(symbols)}")
    else:
        print("📊 同步所有股票")
    
    if data_sources:
        print(f"📡 数据源: {', '.join(data_sources)}")
    else:
        print("📡 数据源: 所有可用数据源")
    
    print()
    
    try:
        service = await get_financial_sync_service()
        
        # 执行同步
        results = await service.sync_financial_data(
            symbols=symbols,
            data_sources=data_sources,
            report_types=["quarterly", "annual"],  # 同时同步季报和年报
            batch_size=50,
            delay_seconds=1.0
        )
        
        # 显示结果
        print("\n" + "="*70)
        print("✅ 同步完成")
        print("="*70)
        
        total_success = 0
        total_symbols = 0
        
        for data_source, stats in results.items():
            print(f"\n{data_source.upper()}:")
            print(f"  • 总股票数: {stats.total_symbols}")
            print(f"  • 成功: {stats.success_count}")
            print(f"  • 失败: {stats.error_count}")
            print(f"  • 跳过: {stats.skipped_count}")
            print(f"  • 成功率: {stats.success_count/max(stats.total_symbols,1)*100:.1f}%")
            print(f"  • 耗时: {stats.duration:.2f}秒")
            
            total_success += stats.success_count
            total_symbols += stats.total_symbols
            
            if stats.errors:
                print(f"  • 错误示例（前3个）:")
                for error in stats.errors[:3]:
                    print(f"    - {error.get('symbol')}: {error.get('error')}")
        
        print(f"\n总计:")
        print(f"  • 总股票数: {total_symbols}")
        print(f"  • 总成功数: {total_success}")
        print(f"  • 总成功率: {total_success/max(total_symbols,1)*100:.1f}%")
        
    except Exception as e:
        print(f"\n❌ 同步失败: {e}")
        import traceback
        traceback.print_exc()


async def sync_single_stock(symbol: str):
    """同步单只股票的财务数据"""
    print(f"🔄 同步单只股票: {symbol}")
    await sync_financial_data_for_stocks(symbols=[symbol])


async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="快速同步财务数据")
    parser.add_argument(
        "--symbols",
        nargs="+",
        help="股票代码列表（如：000001 600000）"
    )
    parser.add_argument(
        "--sources",
        nargs="+",
        choices=["tushare", "akshare", "baostock"],
        help="数据源列表（如：tushare akshare）"
    )
    parser.add_argument(
        "--single",
        type=str,
        help="同步单只股票（快捷方式）"
    )
    
    args = parser.parse_args()
    
    if args.single:
        await sync_single_stock(args.single)
    else:
        await sync_financial_data_for_stocks(
            symbols=args.symbols,
            data_sources=args.sources
        )


if __name__ == "__main__":
    asyncio.run(main())

