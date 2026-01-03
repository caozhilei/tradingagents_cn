from typing import Optional, Dict, List, Any
import logging
import os

from .base import DataSourceAdapter
from .tdx_adapter import TDXAdapter

logger = logging.getLogger(__name__)


class MCPAdapter(DataSourceAdapter):
    """
    MCP 通达信问小达数据源适配器
    - 基于 TDXAdapter 的 MCP 接口（SSE 调用）
    - 主要用于连通性检测和单标的快照获取
    """

    def __init__(self):
        super().__init__()
        self._provider = TDXAdapter()

        # 启用 MCP：若设置了 API Key 则默认开启
        api_key = os.getenv("MCP_API_KEY", "").strip()
        sse_url = os.getenv("MCP_SSE_URL", "https://dashscope.aliyuncs.com/api/v1/mcps/tendency-software/sse").strip()
        bsp_num = os.getenv("MCP_BSP_NUM", "5").strip()
        enable_env = os.getenv("MCP_ENABLE", "").strip().lower()

        # 满足任一条件则开启
        self._provider._mcp_enabled = (enable_env == "true") or bool(api_key)
        if api_key:
            self._provider._mcp_api_key = api_key
        if sse_url:
            self._provider._mcp_sse_url = sse_url
        if bsp_num:
            self._provider._mcp_bsp_num = bsp_num

    @property
    def name(self) -> str:
        return "mcp_tdx"

    def _get_default_priority(self) -> int:
        # 低于本地 TDX，高于开源源
        return 8

    def is_available(self) -> bool:
        # 优先以配置可用性为准，减少前端状态页超时
        if not getattr(self._provider, "_mcp_enabled", False):
            logger.warning("MCPAdapter disabled: MCP_ENABLE未开启或缺少MCP_API_KEY")
            return False
        if not getattr(self._provider, "_mcp_api_key", ""):
            logger.warning("MCPAdapter missing MCP_API_KEY")
            return False
        try:
            # 快速探活：如失败仅记录，不阻断可用性展示
            result = self._provider.get_quote_via_mcp("000001", "1")
            if result:
                return True
        except Exception as e:
            logger.warning(f"MCPAdapter probe failed (忽略为可用): {e}")
        return True

    # 以下接口可按需扩展，目前多源管理仅做可用性检测
    def get_stock_list(self) -> Optional["pd.DataFrame"]:  # type: ignore
        return None

    def get_daily_basic(self, trade_date: str) -> Optional["pd.DataFrame"]:  # type: ignore
        return None

    def find_latest_trade_date(self) -> Optional[str]:
        return None

    def get_realtime_quotes(self) -> Optional[Dict[str, Dict[str, Optional[float]]]]:
        return None

    def get_kline(self, code: str, period: str = "day", limit: int = 120, adj: Optional[str] = None) -> Optional[List[Dict]]:
        return None

    def get_news(self, code: str, days: int = 2, limit: int = 50, include_announcements: bool = True) -> Optional[List[Dict]]:
        return None

    # MCP 专用扩展
    def query_wenda(
        self,
        question: str,
        market: str = "AG",
        page: int = 1,
        size: int = 10,
        structured: bool = False,
        store: bool = False,
        tags: Optional[Dict[str, Any]] = None,
    ) -> Optional[Any]:
        """调用 MCP 问答接口，可选结构化输出与入库。"""
        if not self._provider:
            return None
        return self._provider.query_wenda_via_mcp(
            question=question, market=market, page=page, size=size, structured=structured, store=store, tags=tags
        )

    def get_quote(self, code: str, setcode: str = "1") -> Optional[Dict[str, Any]]:
        """获取单标的行情快照（MCP）- 同步版本。"""
        if not self._provider:
            return None
        return self._provider.get_quote_via_mcp(code, setcode)

    async def get_quote_async(self, code: str, setcode: str = "1") -> Optional[Dict[str, Any]]:
        """获取单标的行情快照（MCP）- 异步版本（用于 FastAPI）。"""
        if not self._provider:
            return None
        return await self._provider.get_quote_via_mcp_async(code, setcode)

