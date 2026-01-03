"""
检查 Mongo 中 market_quotes 集合示例文档，验证新增字段是否写入。
可通过 MONGODB_URI/MONGODB_HOST/MONGODB_PORT 环境变量覆盖连接。
"""

import asyncio
import os
import pprint

# 避免 pydantic 插件警告，并确保布尔环境变量合法
os.environ["PYDANTIC_DISABLE_PLUGINS"] = "1"
os.environ.setdefault("TUSHARE_ENABLED", "false")
# 本地直连 Mongo（如未显式配置则回退 127.0.0.1:27017）
if not os.environ.get("MONGODB_HOST") or os.environ.get("MONGODB_HOST") == "mongodb":
    os.environ["MONGODB_HOST"] = "127.0.0.1"
if not os.environ.get("MONGODB_PORT"):
    os.environ["MONGODB_PORT"] = "27017"
# Redis 也默认指向本地
if not os.environ.get("REDIS_HOST") or os.environ.get("REDIS_HOST") == "redis":
    os.environ["REDIS_HOST"] = "127.0.0.1"
if not os.environ.get("REDIS_PORT"):
    os.environ["REDIS_PORT"] = "6379"

from app.core import database


async def main() -> None:
    await database.init_database()
    db = database.get_mongo_db()
    doc = await db["market_quotes"].find_one({}, {"_id": 0})
    if not doc:
        print("⚠️ market_quotes 无文档")
    else:
        print("✅ 获取示例文档字段：")
        print(sorted(doc.keys()))
        print("\n示例文档：")
        pprint.pp(doc)
    await database.close_database()


if __name__ == "__main__":
    asyncio.run(main())

