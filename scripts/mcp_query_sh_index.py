"""
使用开源 mcp Python SDK 调用“通达信问小达” MCP 服务器的示例脚本。

前置条件：
1) 安装 SDK：  pip install mcp
2) 本地可启动对应的 MCP 服务器（通过标准输入输出 stdio 暴露接口）。
   默认使用环境变量 MCP_SERVER_CMD / MCP_SERVER_ARGS 指定启动命令。
   如果不知道命令，可用 --server-cmd / --server-args 手动覆盖。

工具说明（阿里百炼“通达信问小达” MCP 工具）：
- tdx_wenda_quotes：金融问答/列表类查询，支持行情、财务、技术指标、板块/指数、资金流向、行业/概念等。入参 `question`
  需按规则改写：单票查询用“代码+条件”；多票对比拆分；行业用“行业+指标”；复杂条件拆分时间/维度；冲突条件拒绝；
  涨跌停对比拆分；资金流向拆分主力/北向；行业排名取前 N。分页参数：`page`(默认1)、`size`(1-100，默认10)；
  市场范围 `range`：AG(默认 A 股)、JJ(基金)、ZS(指数)。返回形如二维数组：元信息行、表头行、分隔行、数据行。
- tdx_PBHQInfo_quotes：单个证券/指数行情快照。SSE 入口 `https://dashscope.aliyuncs.com/api/v1/mcps/tendency-software/sse`，Header
  需 `Authorization: Bearer <API Key>`。必填：`code`(6 位)、`setcode`(1=沪/0=深)。可选：`hasHQInfo`/`hasExtInfo`/`hasProInfo`/
  `hasCalcInfo`/`hasCwInfo`/`hasStatInfo`/`bspNum`。本脚本固定：行情+扩展+盘口(bspNum=5)。
  返回：`HQInfo`(时间、价格、量额、涨跌幅、量比、换手率等)、`ExtInfo`(市值/股本/市盈率)、`BspInfo`(五档买卖盘)、`BaseInfo`
  (名称/代码/市场/单位) 等。

调用方式：
- SSE 直连（推荐，官方托管服务）：提供 `--sse-url` 与 `--sse-header "Authorization=Bearer <token>"`。
- stdio 进程：提供 `--server-cmd/--server-args`，脚本以 stdio 方式拉起自建 MCP server。
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import shlex
from typing import Any, Dict, Iterable, List, Optional

# 禁用 pydantic 插件，避免 logfire-plugin 触发 opentelemetry 兼容性警告
os.environ.setdefault("PYDANTIC_DISABLE_PLUGINS", "1")

from mcp.client.session import ClientSession
from mcp.client.sse import sse_client
from mcp.client.stdio import StdioServerParameters, stdio_client


def _contents_to_data(contents: Iterable[Any]) -> List[Any]:
    """
    将 MCP Tool 的返回内容转换成可 JSON 序列化的结构。
    兼容 text / blob / json 等常见 content 类型。
    """
    data: List[Any] = []
    for item in contents:
        if hasattr(item, "text"):
            data.append(item.text)
        elif hasattr(item, "json"):
            data.append(item.json)
        elif hasattr(item, "uri"):
            data.append({"uri": getattr(item, "uri", None), "mimeType": getattr(item, "mimeType", None)})
        else:
            data.append(repr(item))
    return data


async def query_index(
    code: str,
    setcode: str,
    server_cmd: str,
    server_args: str,
    sse_url: Optional[str],
    sse_headers: Optional[Dict[str, str]],
) -> None:
    """
    根据传入参数选择 stdio 或 SSE 方式连接 MCP server，然后调用工具。
    """
    transport_ctx = None

    if sse_url:
        # 使用 SSE 直连已有的远程 MCP 服务
        headers = sse_headers or {}
        transport_ctx = sse_client(sse_url, headers=headers)
    else:
        cmd = server_cmd or os.environ.get("MCP_SERVER_CMD", "")
        args_str = server_args or os.environ.get("MCP_SERVER_ARGS", "")
        if not cmd:
            raise SystemExit("缺少 MCP 服务器启动命令，请通过 --server-cmd 或 MCP_SERVER_CMD 设置，或改用 --sse-url")
        args = shlex.split(args_str) if args_str else []
        transport_ctx = stdio_client(StdioServerParameters(command=cmd, args=args))

    async with transport_ctx as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tool_name = "tdx_PBHQInfo_quotes"
            payload = {
                "code": code,
                "setcode": setcode,
                "hasHQInfo": "1",
                "hasExtInfo": "1",
                "bspNum": "5",
                "hasProInfo": "0",
                "hasCalcInfo": "0",
                "hasCwInfo": "0",
                "hasStatInfo": "0",
            }

            result = await session.call_tool(tool_name, arguments=payload)
            printable = _contents_to_data(result.content) if hasattr(result, "content") else result
            print(json.dumps(printable, ensure_ascii=False, indent=2))


def _parse_headers(header_items: Optional[List[str]]) -> Dict[str, str]:
    """
    将 ["Authorization=Bearer xxx", "X-Token=abc"] 转换为 dict。
    """
    if not header_items:
        return {}
    headers: Dict[str, str] = {}
    for item in header_items:
        if "=" in item:
            k, v = item.split("=", 1)
            headers[k.strip()] = v.strip()
    return headers


def main() -> None:
    parser = argparse.ArgumentParser(description="查询上证指数（000001，setcode=1）的 MCP 示例")
    parser.add_argument("--code", default="000001", help="证券代码，默认 000001（上证指数）")
    parser.add_argument("--setcode", default="1", help="市场代码：1=沪市，0=深市，默认 1")
    # stdio 模式参数
    parser.add_argument("--server-cmd", default=os.environ.get("MCP_SERVER_CMD", ""), help="MCP 服务器启动命令（stdio）")
    parser.add_argument("--server-args", default=os.environ.get("MCP_SERVER_ARGS", ""), help="MCP 服务器命令行参数（stdio）")
    # SSE 模式参数
    parser.add_argument("--sse-url", default=os.environ.get("MCP_SSE_URL", ""), help="MCP SSE 服务端地址，例如 https://.../sse")
    parser.add_argument(
        "--sse-header",
        action="append",
        default=None,
        help="SSE 额外 Header，格式：Key=Value，可重复传入多次",
    )
    args = parser.parse_args()

    headers = _parse_headers(args.sse_header)
    asyncio.run(
        query_index(
            args.code,
            args.setcode,
            args.server_cmd,
            args.server_args,
            args.sse_url or None,
            headers or None,
        )
    )


if __name__ == "__main__":
    main()

