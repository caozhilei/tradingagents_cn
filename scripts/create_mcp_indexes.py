"""
辅助脚本：初始化数据库并创建/更新 Mongo 索引（含 market_quotes 新增字段）。
在脚本内部设置必要的环境变量，避免外部配置缺失导致的校验错误。
"""

import os
import asyncio

# 避免 pydantic 插件警告，并确保布尔环境变量合法（强制覆盖可能存在的脏值）
os.environ["PYDANTIC_DISABLE_PLUGINS"] = "1"
os.environ["TUSHARE_ENABLED"] = "false"
# 本地直连 Mongo（如未显式配置则回退 127.0.0.1:27017）
if not os.environ.get("MONGODB_HOST") or os.environ.get("MONGODB_HOST") == "mongodb":
    os.environ["MONGODB_HOST"] = "127.0.0.1"
if not os.environ.get("MONGODB_PORT"):
    os.environ["MONGODB_PORT"] = "27017"
# Redis 默认指向本地
if not os.environ.get("REDIS_HOST") or os.environ.get("REDIS_HOST") == "redis":
    os.environ["REDIS_HOST"] = "127.0.0.1"
if not os.environ.get("REDIS_PORT"):
    os.environ["REDIS_PORT"] = "6379"

from app.core import database


async def main() -> None:
    await database.init_database()
    db = database.get_mongo_db()
    await database.create_database_indexes(db)
    print("✅ index creation done")


if __name__ == "__main__":
    asyncio.run(main())

