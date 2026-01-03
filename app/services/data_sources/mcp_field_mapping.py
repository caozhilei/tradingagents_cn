"""
MCP 字段映射速查，用于 tdx_PBHQInfo_quotes 返回结果的含义提示。
可在上层日志/调试中引用，不强制参与业务逻辑。
"""

MCP_QUOTE_FIELD_MAP = {
    "HQInfo": {
        "HQDate": "行情日期(YYYYMMDD)",
        "HQTime": "行情时间(HHMMSS)",
        "Now": "现价",
        "Close": "昨收",
        "Open": "今开",
        "MaxP": "最高",
        "MinP": "最低",
        "Lead": "涨跌幅%",
        "Volume": "成交量(股)",
        "Amount": "成交额(元)",
        "LB": "量比",
        "HSL": "换手率%",
        "Average": "均价",
    },
    "ExtInfo": {
        "ZSZ": "总市值(亿元)",
        "ZGB": "总股本(万股)",
        "LTGB": "流通股本(万股)",
        "SYL": "市盈率",
        "FreeLtgb": "自由流通股本(万股)",
    },
    "BspInfo": {
        "BuyP/SellP": "买卖档价格",
        "BuyV/SellV": "买卖档数量(手)",
    },
    "BaseInfo": {
        "Setcode": "市场代码(1沪/0深)",
        "Code": "证券代码",
        "Name": "名称",
        "Unit": "成交量单位倍数",
    },
    "ProInfo": {
        "NowVol": "现手",
        "PEStatic": "静态PE",
        "PETTM": "TTM PE",
        "Volatility": "历史波幅%",
        "ThisYear": "年初至今涨幅%",
    },
}

