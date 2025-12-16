"""
TDX (通达信) data source adapter
"""
from typing import Optional, Dict, List
import logging
from datetime import datetime, timedelta
import pandas as pd

from .base import DataSourceAdapter

logger = logging.getLogger(__name__)


class TDXAdapter(DataSourceAdapter):
    """TDX（通达信）数据源适配器"""

    def __init__(self):
        super().__init__()  # 调用父类初始化
        self._provider = None

    @property
    def name(self) -> str:
        return "tdx"

    def _get_default_priority(self) -> int:
        return 10  # TDX作为默认数据源，优先级最高

    def is_available(self) -> bool:
        """检查TDX是否可用"""
        try:
            from data.tdx_utils import get_tdx_provider
            provider = get_tdx_provider()
            if provider:
                # 尝试连接
                if not provider.connected:
                    return provider.connect()
                return provider.connected
            return False
        except Exception as e:
            logger.warning(f"TDX适配器不可用: {e}")
            return False

    def _get_provider(self):
        """获取TDX数据提供器"""
        if self._provider is None:
            try:
                from data.tdx_utils import get_tdx_provider
                self._provider = get_tdx_provider()
            except Exception as e:
                logger.error(f"获取TDX提供器失败: {e}")
                return None
        return self._provider

    def get_stock_list(self) -> Optional[pd.DataFrame]:
        """获取股票列表"""
        if not self.is_available():
            return None
        try:
            # TDX不直接提供股票列表，需要从MongoDB或其他数据源获取
            # 这里返回None，让系统使用其他数据源
            logger.info("TDX: 不提供股票列表，建议使用其他数据源")
            return None
        except Exception as e:
            logger.error(f"TDX获取股票列表失败: {e}")
            return None

    def get_daily_basic(self, trade_date: str) -> Optional[pd.DataFrame]:
        """获取每日基础财务数据"""
        if not self.is_available():
            return None
        try:
            # TDX主要用于实时行情，不提供每日基础财务数据
            # 这里返回None，让系统使用其他数据源
            logger.info(f"TDX: 不提供每日基础财务数据，建议使用其他数据源")
            return None
        except Exception as e:
            logger.error(f"TDX获取每日基础数据失败: {e}")
            return None

    def find_latest_trade_date(self) -> Optional[str]:
        """查找最新交易日期"""
        if not self.is_available():
            return None
        try:
            # TDX不直接提供交易日期查询，使用当前日期
            today = datetime.now()
            # 如果是周末，返回上一个交易日
            if today.weekday() >= 5:  # 周六或周日
                days_back = today.weekday() - 4
                today = today - timedelta(days=days_back)
            return today.strftime("%Y%m%d")
        except Exception as e:
            logger.error(f"TDX查找最新交易日期失败: {e}")
            return None

    def get_realtime_quotes(self) -> Optional[Dict[str, Dict[str, Optional[float]]]]:
        """获取全市场实时快照"""
        if not self.is_available():
            return None
        try:
            provider = self._get_provider()
            if not provider:
                return None
            
            # TDX主要用于实时行情，但获取全市场数据需要遍历所有股票
            # 这里返回None，让系统使用其他数据源
            logger.info("TDX: 获取全市场实时快照需要遍历所有股票，建议使用其他数据源")
            return None
        except Exception as e:
            logger.error(f"TDX获取实时快照失败: {e}")
            return None

    def get_kline(self, code: str, period: str = "day", limit: int = 120, adj: Optional[str] = None) -> Optional[List[Dict]]:
        """获取K线数据"""
        if not self.is_available():
            return None
        try:
            provider = self._get_provider()
            if not provider:
                return None
            
            # 转换周期格式
            period_map = {
                "day": "daily",
                "week": "weekly",
                "month": "monthly"
            }
            tdx_period = period_map.get(period, "daily")
            
            # 获取历史K线数据
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=limit * 2)).strftime("%Y-%m-%d")
            
            # 使用TDX获取历史数据
            # 注意：这里需要根据实际的tdx_utils接口调整
            logger.info(f"TDX: 获取K线数据 - {code}, 周期: {period}, 限制: {limit}")
            return None  # TDX主要用于实时行情，K线数据建议使用其他数据源
        except Exception as e:
            logger.error(f"TDX获取K线数据失败: {e}")
            return None

    def get_news(self, code: str, days: int = 2, limit: int = 50, include_announcements: bool = True) -> Optional[List[Dict]]:
        """获取新闻与公告"""
        if not self.is_available():
            return None
        try:
            # TDX不提供新闻和公告数据
            logger.info("TDX: 不提供新闻和公告数据")
            return None
        except Exception as e:
            logger.error(f"TDX获取新闻失败: {e}")
            return None

