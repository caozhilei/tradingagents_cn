"""
将 MCP 通达信问小达数据源（MCP_TDX）写入 Mongo 的 system_configs.active 配置：
- 如果已存在则跳过；
- 如果不存在则追加一条 DataSourceConfig。

依赖：
- 读取现有 system_configs 中 is_active=true 的最新版本。
- 不改动其他字段。

可通过环境变量覆盖连接：
- MONGODB_URI 或 MONGODB_HOST/MONGODB_PORT/MONGODB_USERNAME/MONGODB_PASSWORD/MONGODB_AUTH_SOURCE
- REDIS_HOST/REDIS_PORT（虽然此脚本只用 Mongo）
"""

import asyncio
import os
from copy import deepcopy

os.environ["PYDANTIC_DISABLE_PLUGINS"] = "1"
os.environ.setdefault("TUSHARE_ENABLED", "false")

# 默认本地直连
if not os.environ.get("MONGODB_HOST") or os.environ.get("MONGODB_HOST") == "mongodb":
    os.environ["MONGODB_HOST"] = "127.0.0.1"
if not os.environ.get("MONGODB_PORT"):
    os.environ["MONGODB_PORT"] = "27017"
if not os.environ.get("REDIS_HOST") or os.environ.get("REDIS_HOST") == "redis":
    os.environ["REDIS_HOST"] = "127.0.0.1"
if not os.environ.get("REDIS_PORT"):
    os.environ["REDIS_PORT"] = "6379"

from app.core import database


MCP_ENTRY = {
    "name": "MCP_TDX",
    "type": "mcp_tdx",
    "endpoint": "https://dashscope.aliyuncs.com/api/v1/mcps/tendency-software/sse",
    "api_key": os.getenv("MCP_API_KEY", ""),
    "enabled": True,
    "priority": 8,
    "market_categories": ["a_shares"],
    "description": "阿里百炼 MCP 通达信问小达：SSE 直连行情快照与问答榜单",
    "config_params": {
        "sse_url": os.getenv("MCP_SSE_URL", "https://dashscope.aliyuncs.com/api/v1/mcps/tendency-software/sse"),
        "bsp_num": os.getenv("MCP_BSP_NUM", "5"),
    },
    "provider": "Aliyun Bailian MCP",
    "display_name": "MCP 通达信问小达",
    "timeout": 30,
    "rate_limit": 100,
}


async def main() -> None:
    await database.init_database()
    db = database.get_mongo_db()
    coll = db["system_configs"]

    doc = await coll.find_one({"is_active": True}, sort=[("version", -1)])
    if not doc:
        print("⚠️ 未找到 is_active=true 的 system_configs，未作修改")
        await database.close_database()
        return

    configs = doc.get("data_source_configs", []) or []
    if any((c.get("name") == "MCP_TDX" or c.get("type") == "mcp_tdx") for c in configs):
        print("✅ 已存在 MCP_TDX，未重复添加")
    else:
        new_configs = deepcopy(configs)
        new_configs.append(MCP_ENTRY)
        await coll.update_one({"_id": doc["_id"]}, {"$set": {"data_source_configs": new_configs}})
        print(f"✅ 已追加 MCP_TDX 到 system_configs (id={doc['_id']})")

    await database.close_database()


if __name__ == "__main__":
    asyncio.run(main())

