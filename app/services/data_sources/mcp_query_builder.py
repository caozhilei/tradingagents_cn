"""
Tdx Wenda（tdx_wenda_quotes）查询构造器：
- 规范化入参，满足官方的改写规则与分页/市场字段。
- 仅做轻量拼接，复杂语义拆分仍需上层根据业务定制。
"""

from dataclasses import dataclass
from typing import List, Dict, Any


def _normalize_market(market: str) -> str:
    market = (market or "AG").upper()
    if market not in {"AG", "JJ", "ZS"}:
        return "AG"
    return market


@dataclass
class WendaQuery:
    question: str
    market: str = "AG"
    page: int = 1
    size: int = 10

    def to_payload(self) -> Dict[str, Any]:
        return {
            "question": self.question,
            "range": _normalize_market(self.market),
            "page": str(self.page),
            "size": str(self.size),
        }


class TdxWendaQueryBuilder:
    """
    规则摘要（与官方描述对齐）：
    - 单票：`{code/name}{条件}`，可用“且/或”组合。
    - 多票对比：拆成多条独立查询。
    - 行业/板块：`{行业}{指标}`。
    - 复杂条件：不同时间/维度需拆分；冲突条件拒绝。
    - 情绪/资金：涨跌停对比需拆分；资金流向拆分主力/北向；行业排名取前N。
    """

    @staticmethod
    def single(code_or_name: str, condition: str, market: str = "AG", page: int = 1, size: int = 10) -> WendaQuery:
        question = f"{code_or_name}{condition}"
        return WendaQuery(question=question, market=market, page=page, size=size)

    @staticmethod
    def industry(industry_name: str, metric: str, market: str = "AG", page: int = 1, size: int = 10) -> WendaQuery:
        question = f"{industry_name}{metric}"
        return WendaQuery(question=question, market=market, page=page, size=size)

    @staticmethod
    def multi_compare(items: List[str], condition: str, market: str = "AG", page: int = 1, size: int = 10) -> List[WendaQuery]:
        # 按规则拆分为多条独立查询
        return [WendaQuery(question=f"{it}{condition}", market=market, page=page, size=size) for it in items]

    @staticmethod
    def raw(question: str, market: str = "AG", page: int = 1, size: int = 10) -> WendaQuery:
        # 已经符合官方规则的场景直接包装
        return WendaQuery(question=question, market=market, page=page, size=size)

