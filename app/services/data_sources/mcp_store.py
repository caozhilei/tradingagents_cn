import logging
import os
from datetime import datetime
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

try:
    from pymongo import MongoClient

    MONGO_AVAILABLE = True
except Exception:
    MongoClient = None  # type: ignore
    MONGO_AVAILABLE = False
    logger.debug("pymongo 未安装，MCP Mongo 存储不可用")


class MCPMongoStore:
    """MCP 问答结果的简单 MongoDB 存储器（可选启用）。"""

    def __init__(self):
        self.enabled = os.getenv("MCP_STORE_ENABLE", "false").lower() == "true"
        self.db_name = os.getenv("MCP_STORE_DB", os.getenv("MONGODB_DATABASE", "tradingagents"))
        self.collection_name = os.getenv("MCP_STORE_COLLECTION", "mcp_queries")

        self._client: Optional[MongoClient] = None
        self._collection = None
        self.connected = False

        if self.enabled and MONGO_AVAILABLE:
            self._connect()
        elif self.enabled:
            logger.warning("MCP 存储已启用但未安装 pymongo，跳过连接")

    def _connect(self):
        host = os.getenv("MONGODB_HOST", "localhost")
        port = int(os.getenv("MONGODB_PORT", "27017"))
        username = os.getenv("MONGODB_USERNAME", "")
        password = os.getenv("MONGODB_PASSWORD", "")
        auth_source = os.getenv("MONGODB_AUTH_SOURCE", "admin")

        kwargs: Dict[str, Any] = {
            "host": host,
            "port": port,
            "serverSelectionTimeoutMS": 5000,
            "connectTimeoutMS": 5000,
        }
        if username and password:
            kwargs.update({"username": username, "password": password, "authSource": auth_source})

        try:
            self._client = MongoClient(**kwargs)
            self._client.admin.command("ping")
            db = self._client[self.db_name]
            self._collection = db[self.collection_name]
            self._collection.create_index([("question", 1), ("market", 1), ("created_at", -1)])
            self.connected = True
            logger.info(f"✅ MCP Mongo 存储已连接: {self.db_name}.{self.collection_name}")
        except Exception as e:
            logger.warning(f"⚠️ MCP Mongo 连接失败: {e}")
            self.connected = False

    def save_wenda_result(
        self, question: str, market: str, structured: Dict[str, Any], tags: Optional[Dict[str, Any]] = None
    ) -> bool:
        """将结构化问答结果写入 Mongo（无连接时安全失败）。"""
        if not self.enabled or not self.connected or self._collection is None:
            return False

        doc: Dict[str, Any] = {
            "question": question,
            "market": market,
            "total": structured.get("total", 0),
            "columns": structured.get("columns", []),
            "records": structured.get("records", []),
            "meta": structured.get("meta", {}),
            "created_at": datetime.utcnow(),
        }
        if tags:
            doc["tags"] = tags

        try:
            self._collection.insert_one(doc)
            return True
        except Exception as e:
            logger.warning(f"⚠️ 保存 MCP 问答结果失败: {e}")
            return False

