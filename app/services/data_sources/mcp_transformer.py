import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# MCP 问答返回的特殊字段黑名单
BLACKLIST_FIELDS = {"POS", "show_url", "market", "index_market", "index_code", "timestamps"}


def _try_fix_encoding(text: str) -> str:
    """尝试修复 GBK 被误解为 latin1/utf8 造成的乱码。"""
    try:
        # 常见场景：服务端返回 GBK 但被当 latin1 解码
        return text.encode("latin1").decode("gbk", errors="ignore")
    except Exception:
        return text


def _clean_value(value: Any, fix_encoding: bool = True) -> Any:
    """清理占位符/空白字符串，并可选修复中文乱码。"""
    if isinstance(value, str):
        # MCP 可能返回 @@xxx@@ 这样的占位符
        if value.startswith("@@") and value.endswith("@@"):
            value = value.strip("@")
        # 尝试修复乱码
        if fix_encoding:
            value = _try_fix_encoding(value)
        stripped = value.strip()
        return stripped if stripped else value
    return value


def parse_wenda_response(
    raw: Any,
    question: Optional[str] = None,
    market: Optional[str] = None,
    fix_encoding: bool = True,
) -> Dict[str, Any]:
    """
    将 tdx_wenda_quotes 的原始二维数组转换为结构化结果：
    {
        "total": int,
        "columns": [...],
        "rows": [[...], ...],
        "records": [ {col: val}, ... ],
        "meta": {"question": "", "market": ""},
        "raw": raw
    }
    """
    parsed: Dict[str, Any] = {
        "total": 0,
        "columns": [],
        "rows": [],
        "records": [],
        "meta": {},
        "raw": raw,
    }

    if question:
        parsed["meta"]["question"] = question
    if market:
        parsed["meta"]["market"] = market

    if not isinstance(raw, list) or not raw:
        return parsed

    # 1) 元信息行获取总量
    try:
        meta_row = raw[0] if isinstance(raw[0], list) else []
        if len(meta_row) >= 3 and isinstance(meta_row[2], (int, float, str)):
            parsed["total"] = int(float(meta_row[2])) if str(meta_row[2]).replace(".", "", 1).isdigit() else 0
    except Exception as e:
        logger.debug(f"MCP 解析元信息失败: {e}")

    # 2) 表头行：元信息行之后的第一行非空列表
    header: List[str] = []
    header_idx = None
    for idx, row in enumerate(raw[1:], start=1):
        if isinstance(row, list) and row and any(str(v).strip() for v in row):
            header = [str(col).strip() for col in row if str(col).strip() != ""]
            header_idx = idx
            break

    if not header:
        return parsed

    # 3) 过滤黑名单列（同时修复表头乱码）
    keep_indices: List[int] = []
    filtered_header: List[str] = []
    for i, col in enumerate(header):
        if col in BLACKLIST_FIELDS:
            continue
        keep_indices.append(i)
        # 修复表头乱码
        if fix_encoding:
            col = _try_fix_encoding(col)
        filtered_header.append(col)

    # 4) 数据行：表头行之后的有效行
    data_rows: List[List[Any]] = []
    if header_idx is not None:
        for row in raw[header_idx + 1 :]:
            if not isinstance(row, list):
                continue
            if row == []:  # 分隔行
                continue
            # 对齐长度
            row = list(row)
            if len(row) < len(header):
                row += [None] * (len(header) - len(row))
            cleaned_row = [_clean_value(row[i], fix_encoding=fix_encoding) if i < len(row) else None for i in keep_indices]
            data_rows.append(cleaned_row)

    records = [{col: row[idx] for idx, col in enumerate(filtered_header)} for row in data_rows]

    parsed.update({"columns": filtered_header, "rows": data_rows, "records": records})
    return parsed


def to_markdown_table(parsed: Dict[str, Any], max_rows: int = 20) -> str:
    """
    将结构化结果转为 Markdown 表格，便于报告插入。
    超过 max_rows 时只展示前 max_rows 行。
    """
    cols: List[str] = parsed.get("columns", [])
    rows: List[List[Any]] = parsed.get("rows", [])
    if not cols or not rows:
        return ""

    limited_rows = rows[:max_rows]
    lines = []
    lines.append("| " + " | ".join(cols) + " |")
    lines.append("| " + " | ".join(["---"] * len(cols)) + " |")
    for row in limited_rows:
        display = ["" if v is None else str(v) for v in row]
        lines.append("| " + " | ".join(display) + " |")
    if len(rows) > max_rows:
        lines.append(f"\n> 仅展示前 {max_rows} 行，更多数据请查看存储结果。")
    return "\n".join(lines)

