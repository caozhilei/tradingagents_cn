"""
为 market_quotes 集合批量补充 MCP 扩展字段占位，避免查询时报缺字段。
默认直连本地 Mongo/Redis，可通过环境变量覆盖：
- MONGODB_URI 或 MONGODB_HOST/MONGODB_PORT/MONGODB_USERNAME/MONGODB_PASSWORD/MONGODB_AUTH_SOURCE
- REDIS_HOST/REDIS_PORT（但脚本仅需 Mongo）
"""

import asyncio
import os

# 环境兜底，避免插件警告与脏布尔值
os.environ["PYDANTIC_DISABLE_PLUGINS"] = "1"
os.environ.setdefault("TUSHARE_ENABLED", "false")

# 默认直连本地 Mongo
if not os.environ.get("MONGODB_HOST") or os.environ.get("MONGODB_HOST") == "mongodb":
    os.environ["MONGODB_HOST"] = "127.0.0.1"
if not os.environ.get("MONGODB_PORT"):
    os.environ["MONGODB_PORT"] = "27017"
# 默认直连本地 Redis（虽不使用，但避免初始化报错）
if not os.environ.get("REDIS_HOST") or os.environ.get("REDIS_HOST") == "redis":
    os.environ["REDIS_HOST"] = "127.0.0.1"
if not os.environ.get("REDIS_PORT"):
    os.environ["REDIS_PORT"] = "6379"

from app.core import database


NEW_FIELDS_NONE = {
    "total_mv": None,
    "float_mv": None,
    "pe": None,
    "pe_ttm": None,
    "pb": None,
    "mcp_raw": None,
    "mcp_pro_info": None,
    "mcp_stat_info": None,
}

NEW_FIELDS_LIST = {
    "bid_prices": [],
    "bid_volumes": [],
    "ask_prices": [],
    "ask_volumes": [],
    "mcp_bsp": [],
}


async def main() -> None:
    await database.init_database()
    db = database.get_mongo_db()

    # 分两次 set，避免 $setOnInsert 与空数组冲突
    if NEW_FIELDS_NONE:
        await db["market_quotes"].update_many({}, {"$set": NEW_FIELDS_NONE})
    if NEW_FIELDS_LIST:
        await db["market_quotes"].update_many({}, {"$set": NEW_FIELDS_LIST})

    print("✅ 已为 market_quotes 补充 MCP 扩展字段占位")
    await database.close_database()


if __name__ == "__main__":
    asyncio.run(main())

