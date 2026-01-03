"""
TDX (通达信) data source adapter
"""
from typing import Optional, Dict, List, Any
import logging
from datetime import datetime, timedelta
import os
import json
import asyncio
import pandas as pd

# MCP 依赖
os.environ.setdefault("PYDANTIC_DISABLE_PLUGINS", "1")
try:
    from mcp.client.session import ClientSession
    from mcp.client.sse import sse_client
except Exception:
    ClientSession = None  # type: ignore
    sse_client = None  # type: ignore

from .base import DataSourceAdapter
from .mcp_field_mapping import MCP_QUOTE_FIELD_MAP
from .mcp_transformer import parse_wenda_response

try:
    from .mcp_store import MCPMongoStore
except Exception:
    MCPMongoStore = None  # type: ignore

logger = logging.getLogger(__name__)


class TDXAdapter(DataSourceAdapter):
    """TDX（通达信）数据源适配器"""

    def __init__(self):
        super().__init__()  # 调用父类初始化
        self._provider = None
        self._mcp_enabled = os.getenv("MCP_ENABLE", "false").lower() == "true"
        self._mcp_sse_url = os.getenv("MCP_SSE_URL", "https://dashscope.aliyuncs.com/api/v1/mcps/tendency-software/sse")
        self._mcp_api_key = os.getenv("MCP_API_KEY", "")
        self._mcp_bsp_num = os.getenv("MCP_BSP_NUM", "5")
        self._mcp_store = MCPMongoStore() if MCPMongoStore else None

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

    # ============== MCP 增强：单标的行情快照 ==============
    async def get_quote_via_mcp_async(self, code: str, setcode: str = "1") -> Optional[Dict[str, Any]]:
        """
        异步版本：通过 MCP (tdx_PBHQInfo_quotes) 获取单个证券/指数的行情快照。
        - 需配置环境变量 MCP_ENABLE=true 且 MCP_API_KEY。
        - 默认走官方 SSE 服务，可通过 MCP_SSE_URL/MCP_BSP_NUM 覆盖。
        """
        if not (self._mcp_enabled and ClientSession and sse_client and self._mcp_api_key):
            return None

        payload = {
            "code": code,
            "setcode": setcode,
            "hasHQInfo": "1",
            "hasExtInfo": "1",
            "hasProInfo": "0",
            "hasCalcInfo": "0",
            "hasCwInfo": "0",
            "hasStatInfo": "0",
            "bspNum": self._mcp_bsp_num,
        }

        try:
            result = await self._call_mcp_tool("tdx_PBHQInfo_quotes", payload)
            if not result:
                return None
            
            # 如果 result 是字符串，尝试解析 JSON
            if isinstance(result, str):
                try:
                    result = json.loads(result)
                except Exception:
                    logger.warning(f"MCP 返回结果无法解析为 JSON: {result[:100] if len(str(result)) > 100 else result}")
                    return None
            
            # 如果 result 是字典但包含 text 字段，尝试解析 text 字段中的 JSON（嵌套 JSON 字符串）
            if isinstance(result, dict) and "text" in result:
                try:
                    text_content = result["text"]
                    if isinstance(text_content, str):
                        # 尝试解析 text 字段中的 JSON
                        parsed = json.loads(text_content)
                        result = parsed
                    else:
                        result = text_content
                except (json.JSONDecodeError, TypeError) as e:
                    logger.debug(f"MCP result.text 无法解析为 JSON: {e}")
                    # 如果解析失败，保持原样
            
            mapped = self._map_mcp_quote(result)
            return mapped
        except Exception as e:
            logger.warning(f"MCP 行情调用失败 code={code} setcode={setcode}: {e}", exc_info=True)
            return None

    def get_quote_via_mcp(self, code: str, setcode: str = "1") -> Optional[Dict[str, Any]]:
        """
        同步版本：通过 MCP (tdx_PBHQInfo_quotes) 获取单个证券/指数的行情快照。
        - 在异步上下文中请使用 get_quote_via_mcp_async
        """
        try:
            # 检查是否在运行的事件循环中
            loop = None
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                pass
            
            if loop:
                # 如果在事件循环中，无法使用 asyncio.run()
                logger.warning("get_quote_via_mcp 在异步上下文中被调用，请使用 get_quote_via_mcp_async")
                return None
            else:
                # 如果不在事件循环中，可以使用 asyncio.run()
                return asyncio.run(self.get_quote_via_mcp_async(code, setcode))
        except Exception as e:
            logger.warning(f"MCP 行情调用失败 code={code} setcode={setcode}: {e}", exc_info=True)
            return None

    # ============== MCP 增强：问答/榜单查询 ==============
    async def query_wenda_via_mcp_async(
        self,
        question: str,
        market: str = "AG",
        page: int = 1,
        size: int = 10,
        structured: bool = False,
        store: bool = False,
        tags: Optional[Dict[str, Any]] = None,
    ) -> Optional[Any]:
        """
        通过 MCP (tdx_wenda_quotes) 执行问答/榜单/条件查询（异步版本）。
        - structured=True 时返回解析后的表格结构。
        - store=True 且配置了 Mongo 时，会将结构化结果入库。
        question 建议先用 query builder 规范化后传入。
        """
        if not (self._mcp_enabled and ClientSession and sse_client and self._mcp_api_key):
            return None

        payload = {"question": question, "range": market, "page": str(page), "size": str(size)}
        try:
            result = await self._call_mcp_tool("tdx_wenda_quotes", payload)
            if not result:
                return None

            if structured or store:
                parsed_input: Any = result
                # 如果返回是 JSON 字符串或包含 text 字段的字典，尝试提取真实表格
                if isinstance(result, str):
                    try:
                        obj = json.loads(result)
                        if isinstance(obj, dict) and "text" in obj:
                            try:
                                parsed_input = json.loads(obj.get("text", ""))
                            except Exception:
                                parsed_input = obj.get("text")
                        else:
                            parsed_input = obj
                    except Exception:
                        parsed_input = result
                elif isinstance(result, dict) and "text" in result:
                    try:
                        parsed_input = json.loads(result.get("text", ""))
                    except Exception:
                        parsed_input = result.get("text")

                parsed = parse_wenda_response(parsed_input, question=question, market=market)
                if store and self._mcp_store:
                    try:
                        self._mcp_store.save_wenda_result(question, market, parsed, tags=tags)
                    except Exception as store_err:
                        logger.warning(f"MCP 问答结果入库失败: {store_err}")
                return parsed if structured else result

            return result
        except Exception as e:
            logger.warning(f"MCP 问答调用失败: {e}")
            return None
    
    def query_wenda_via_mcp(
        self,
        question: str,
        market: str = "AG",
        page: int = 1,
        size: int = 10,
        structured: bool = False,
        store: bool = False,
        tags: Optional[Dict[str, Any]] = None,
    ) -> Optional[Any]:
        """
        通过 MCP (tdx_wenda_quotes) 执行问答/榜单/条件查询（同步包装，向后兼容）。
        注意：如果在异步上下文中调用，请使用 query_wenda_via_mcp_async。
        """
        try:
            # 尝试获取当前事件循环
            try:
                loop = asyncio.get_running_loop()
                # 如果事件循环正在运行，使用 nest_asyncio 或返回 None
                logger.warning("在运行的事件循环中调用同步方法，请使用 query_wenda_via_mcp_async")
                return None
            except RuntimeError:
                # 如果没有运行的事件循环，使用asyncio.run
                return asyncio.run(
                    self.query_wenda_via_mcp_async(
                        question, market, page, size, structured, store, tags
                    )
                )
        except Exception as e:
            logger.warning(f"MCP 同步调用失败: {e}")
            return None

    # ============== MCP 内部工具方法 ==============
    async def _call_mcp_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Optional[Any]:
        headers = {"Authorization": f"Bearer {self._mcp_api_key}"}
        async with sse_client(self._mcp_sse_url, headers=headers) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(tool_name, arguments=arguments)
                # 优先 structuredContent；否则从 content 中解析 JSON/text
                if hasattr(result, "structuredContent") and result.structuredContent:
                    return result.structuredContent
                if hasattr(result, "content") and result.content:
                    item = result.content[0]
                    if hasattr(item, "json") and item.json:
                        try:
                            return item.json() if callable(item.json) else item.json
                        except Exception:
                            logger.debug("MCP item.json 调用失败，回退文本解析")
                    if hasattr(item, "text") and item.text:
                        try:
                            parsed = json.loads(item.text)
                            # 如果解析后的结果包含 text 字段，尝试再次解析（处理嵌套 JSON 字符串）
                            if isinstance(parsed, dict) and "text" in parsed and isinstance(parsed["text"], str):
                                try:
                                    return json.loads(parsed["text"])
                                except Exception:
                                    return parsed
                            return parsed
                        except Exception:
                            return item.text
                return result

    def _map_mcp_quote(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """将 MCP 行情结果映射为通用字段，方便上层消费。"""
        hq = data.get("HQInfo", {}) if isinstance(data, dict) else {}
        ext = data.get("ExtInfo", {}) if isinstance(data, dict) else {}
        base = data.get("BaseInfo", {}) if isinstance(data, dict) else {}
        pro = data.get("ProInfo", {}) if isinstance(data, dict) else {}
        stat = data.get("StatInfo", {}) if isinstance(data, dict) else {}
        bsp = data.get("BspInfo", []) if isinstance(data, dict) else []

        def _get(d: Dict[str, Any], key: str) -> Any:
            return d.get(key)

        mapped = {
            "code": _get(base, "Code"),
            "name": _get(base, "Name"),
            "market": _get(base, "Setcode"),
            "price": _get(hq, "Now"),
            "pre_close": _get(hq, "Close"),
            "open": _get(hq, "Open"),
            "high": _get(hq, "MaxP"),
            "low": _get(hq, "MinP"),
            "volume": _get(hq, "Volume"),
            "amount": _get(hq, "Amount"),
            "change_pct": _get(hq, "Lead"),
            "avg_price": _get(hq, "Average"),
            "lb": _get(hq, "LB"),
            "hsl": _get(hq, "HSL"),
            "total_mv": _get(ext, "ZSZ"),
            "total_shares": _get(ext, "ZGB"),
            "float_shares": _get(ext, "LTGB"),
            "pe": _get(ext, "SYL"),
            "pe_ttm": _get(pro, "PETTM"),
            # 盘口聚合（买卖1-5）
            "bid_prices": [item.get("BuyP") for item in bsp if isinstance(item, dict) and item.get("BuyP") is not None],
            "bid_volumes": [item.get("BuyV") for item in bsp if isinstance(item, dict) and item.get("BuyV") is not None],
            "ask_prices": [item.get("SellP") for item in bsp if isinstance(item, dict) and item.get("SellP") is not None],
            "ask_volumes": [item.get("SellV") for item in bsp if isinstance(item, dict) and item.get("SellV") is not None],
        }

        # 补充字段含义，便于调试/文档
        mapped["_raw_map"] = MCP_QUOTE_FIELD_MAP
        mapped["_raw"] = data
        mapped["mcp_bsp"] = bsp
        mapped["mcp_pro_info"] = pro
        mapped["mcp_stat_info"] = stat
        return mapped

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

