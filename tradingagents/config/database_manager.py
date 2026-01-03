#!/usr/bin/env python3
"""
智能数据库管理器
自动检测MongoDB和Redis可用性，提供降级方案
使用项目现有的.env配置
"""

import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

class DatabaseManager:
    """智能数据库管理器"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # 加载.env配置
        self._load_env_config()

        # 数据库连接状态
        self.mongodb_available = False
        self.redis_available = False
        self.mongodb_client = None
        self.redis_client = None

        # 检测数据库可用性
        self._detect_databases()

        # 初始化连接
        self._initialize_connections()

        self.logger.info(f"数据库管理器初始化完成 - MongoDB: {self.mongodb_available}, Redis: {self.redis_available}")
    
    def _load_env_config(self):
        """从.env文件加载配置"""
        # 尝试加载python-dotenv
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            self.logger.info("python-dotenv未安装，直接读取环境变量")

        # 使用强健的布尔值解析（兼容Python 3.13+）
        from .env_utils import parse_bool_env
        self.mongodb_enabled = parse_bool_env("MONGODB_ENABLED", False)
        self.redis_enabled = parse_bool_env("REDIS_ENABLED", False)

        # 🔥 优先使用 MONGODB_CONNECTION_STRING，如果存在则解析它
        connection_string = os.getenv("MONGODB_CONNECTION_STRING")
        if connection_string:
            self.logger.info("🔍 检测到 MONGODB_CONNECTION_STRING，将使用连接字符串方式")
            # 解析连接字符串
            from urllib.parse import urlparse, parse_qs
            try:
                parsed = urlparse(connection_string)
                
                # 提取数据库名（从路径或查询参数）
                database = parsed.path.strip('/') if parsed.path.strip('/') else "tradingagents"
                
                # 从查询参数提取 authSource
                query_params = parse_qs(parsed.query)
                auth_source = query_params.get('authSource', ['admin'])[0]
                
                # 提取用户名和密码
                username = parsed.username
                password = parsed.password
                
                # 提取主机和端口
                host = parsed.hostname or "localhost"
                port = parsed.port or 27017
                
                self.mongodb_config = {
                    "enabled": self.mongodb_enabled,
                    "connection_string": connection_string,  # 保存原始连接字符串
                    "host": host,
                    "port": port,
                    "username": username,
                    "password": password,
                    "database": database,
                    "auth_source": auth_source,
                    "timeout": 2000,
                    "connect_timeout": int(os.getenv("MONGO_CONNECT_TIMEOUT_MS", "30000")),
                    "socket_timeout": int(os.getenv("MONGO_SOCKET_TIMEOUT_MS", "60000")),
                    "server_selection_timeout": int(os.getenv("MONGO_SERVER_SELECTION_TIMEOUT_MS", "5000"))
                }
                self.logger.info(f"✅ 已解析 MONGODB_CONNECTION_STRING: {host}:{port}/{database} (authSource: {auth_source})")
            except Exception as e:
                self.logger.warning(f"⚠️ 解析 MONGODB_CONNECTION_STRING 失败: {e}，将使用分离配置项")
                # 降级到分离配置项
                connection_string = None
        
        # 如果没有连接字符串，使用分离的配置项
        if not connection_string:
            self.mongodb_config = {
                "enabled": self.mongodb_enabled,
                "connection_string": None,
                "host": os.getenv("MONGODB_HOST", "localhost"),
                "port": int(os.getenv("MONGODB_PORT", "27017")),
                "username": os.getenv("MONGODB_USERNAME"),
                "password": os.getenv("MONGODB_PASSWORD"),
                "database": os.getenv("MONGODB_DATABASE", "tradingagents"),
                "auth_source": os.getenv("MONGODB_AUTH_SOURCE", "admin"),
                "timeout": 2000,
                # MongoDB超时参数（毫秒）- 用于处理大量历史数据
                "connect_timeout": int(os.getenv("MONGO_CONNECT_TIMEOUT_MS", "30000")),
                "socket_timeout": int(os.getenv("MONGO_SOCKET_TIMEOUT_MS", "60000")),
                "server_selection_timeout": int(os.getenv("MONGO_SERVER_SELECTION_TIMEOUT_MS", "5000"))
            }

        # 从环境变量读取Redis配置
        self.redis_config = {
            "enabled": self.redis_enabled,
            "host": os.getenv("REDIS_HOST", "localhost"),
            "port": int(os.getenv("REDIS_PORT", "6379")),
            "password": os.getenv("REDIS_PASSWORD"),
            "db": int(os.getenv("REDIS_DB", "0")),
            "timeout": 2
        }

        self.logger.info(f"MongoDB启用: {self.mongodb_enabled}")
        self.logger.info(f"Redis启用: {self.redis_enabled}")
        if self.mongodb_enabled:
            self.logger.info(f"MongoDB配置: {self.mongodb_config['host']}:{self.mongodb_config['port']}")
        if self.redis_enabled:
            self.logger.info(f"Redis配置: {self.redis_config['host']}:{self.redis_config['port']}")
    

    
    def _detect_mongodb(self) -> Tuple[bool, str]:
        """检测MongoDB是否可用"""
        # 首先检查是否启用
        if not self.mongodb_enabled:
            return False, "MongoDB未启用 (MONGODB_ENABLED=false)"

        try:
            import pymongo
            from pymongo import MongoClient

            # 🔥 优先使用连接字符串
            if self.mongodb_config.get("connection_string"):
                try:
                    client = MongoClient(
                        self.mongodb_config["connection_string"],
                        serverSelectionTimeoutMS=self.mongodb_config["server_selection_timeout"],
                        connectTimeoutMS=self.mongodb_config["connect_timeout"],
                        socketTimeoutMS=self.mongodb_config["socket_timeout"]
                    )
                    # 测试连接
                    client.server_info()
                    client.close()
                    return True, "MongoDB连接成功（使用连接字符串）"
                except Exception as e:
                    return False, f"MongoDB连接失败（连接字符串方式）: {str(e)}"
            
            # 降级到分离配置项方式
            # 构建连接参数
            connect_kwargs = {
                "host": self.mongodb_config["host"],
                "port": self.mongodb_config["port"],
                "serverSelectionTimeoutMS": self.mongodb_config["server_selection_timeout"],
                "connectTimeoutMS": self.mongodb_config["connect_timeout"],
                "socketTimeoutMS": self.mongodb_config["socket_timeout"]
            }

            # 如果有用户名和密码，添加认证
            if self.mongodb_config["username"] and self.mongodb_config["password"]:
                connect_kwargs.update({
                    "username": self.mongodb_config["username"],
                    "password": self.mongodb_config["password"],
                    "authSource": self.mongodb_config["auth_source"]
                })

            client = MongoClient(**connect_kwargs)

            # 测试连接
            client.server_info()
            client.close()

            return True, "MongoDB连接成功（使用分离配置项）"

        except ImportError:
            return False, "pymongo未安装"
        except Exception as e:
            return False, f"MongoDB连接失败: {str(e)}"
    
    def _detect_redis(self) -> Tuple[bool, str]:
        """检测Redis是否可用"""
        # 首先检查是否启用
        if not self.redis_enabled:
            return False, "Redis未启用 (REDIS_ENABLED=false)"

        try:
            import redis

            # 构建连接参数
            connect_kwargs = {
                "host": self.redis_config["host"],
                "port": self.redis_config["port"],
                "db": self.redis_config["db"],
                "socket_timeout": self.redis_config["timeout"],
                "socket_connect_timeout": self.redis_config["timeout"]
            }

            # 如果有密码，添加密码
            if self.redis_config["password"]:
                connect_kwargs["password"] = self.redis_config["password"]

            client = redis.Redis(**connect_kwargs)

            # 测试连接
            client.ping()

            return True, "Redis连接成功"

        except ImportError:
            return False, "redis未安装"
        except Exception as e:
            return False, f"Redis连接失败: {str(e)}"
    
    def _detect_databases(self):
        """检测所有数据库"""
        self.logger.info("开始检测数据库可用性...")
        
        # 检测MongoDB
        mongodb_available, mongodb_msg = self._detect_mongodb()
        self.mongodb_available = mongodb_available
        
        if mongodb_available:
            self.logger.info(f"✅ MongoDB: {mongodb_msg}")
        else:
            self.logger.info(f"❌ MongoDB: {mongodb_msg}")
        
        # 检测Redis
        redis_available, redis_msg = self._detect_redis()
        self.redis_available = redis_available
        
        if redis_available:
            self.logger.info(f"✅ Redis: {redis_msg}")
        else:
            self.logger.info(f"❌ Redis: {redis_msg}")
        
        # 更新配置
        self._update_config_based_on_detection()
    
    def _update_config_based_on_detection(self):
        """根据检测结果更新配置"""
        # 确定缓存后端
        if self.redis_available:
            self.primary_backend = "redis"
        elif self.mongodb_available:
            self.primary_backend = "mongodb"
        else:
            self.primary_backend = "file"

        self.logger.info(f"主要缓存后端: {self.primary_backend}")
    
    def _initialize_connections(self):
        """初始化数据库连接"""
        # 初始化MongoDB连接
        if self.mongodb_available:
            try:
                import pymongo

                # 🔥 优先使用连接字符串
                if self.mongodb_config.get("connection_string"):
                    self.mongodb_client = pymongo.MongoClient(
                        self.mongodb_config["connection_string"],
                        serverSelectionTimeoutMS=self.mongodb_config["server_selection_timeout"],
                        connectTimeoutMS=self.mongodb_config["connect_timeout"],
                        socketTimeoutMS=self.mongodb_config["socket_timeout"]
                    )
                    self.logger.info("MongoDB客户端初始化成功（使用连接字符串）")
                else:
                    # 降级到分离配置项方式
                    # 构建连接参数
                    connect_kwargs = {
                        "host": self.mongodb_config["host"],
                        "port": self.mongodb_config["port"],
                        "serverSelectionTimeoutMS": self.mongodb_config["server_selection_timeout"],
                        "connectTimeoutMS": self.mongodb_config["connect_timeout"],
                        "socketTimeoutMS": self.mongodb_config["socket_timeout"]
                    }

                    # 如果有用户名和密码，添加认证
                    if self.mongodb_config["username"] and self.mongodb_config["password"]:
                        connect_kwargs.update({
                            "username": self.mongodb_config["username"],
                            "password": self.mongodb_config["password"],
                            "authSource": self.mongodb_config["auth_source"]
                        })

                    self.mongodb_client = pymongo.MongoClient(**connect_kwargs)
                    self.logger.info("MongoDB客户端初始化成功（使用分离配置项）")
            except Exception as e:
                self.logger.error(f"MongoDB客户端初始化失败: {e}")
                import traceback
                self.logger.error(traceback.format_exc())
                self.mongodb_available = False

        # 初始化Redis连接
        if self.redis_available:
            try:
                import redis

                # 构建连接参数
                connect_kwargs = {
                    "host": self.redis_config["host"],
                    "port": self.redis_config["port"],
                    "db": self.redis_config["db"],
                    "socket_timeout": self.redis_config["timeout"]
                }

                # 如果有密码，添加密码
                if self.redis_config["password"]:
                    connect_kwargs["password"] = self.redis_config["password"]

                self.redis_client = redis.Redis(**connect_kwargs)
                self.logger.info("Redis客户端初始化成功")
            except Exception as e:
                self.logger.error(f"Redis客户端初始化失败: {e}")
                self.redis_available = False
    
    def get_mongodb_client(self):
        """获取MongoDB客户端"""
        if self.mongodb_available and self.mongodb_client:
            return self.mongodb_client
        return None

    def get_mongodb_db(self):
        """获取MongoDB数据库实例"""
        if self.mongodb_available and self.mongodb_client:
            db_name = self.mongodb_config.get("database", "tradingagents")
            return self.mongodb_client[db_name]
        return None

    def get_redis_client(self):
        """获取Redis客户端"""
        if self.redis_available and self.redis_client:
            return self.redis_client
        return None
    
    def is_mongodb_available(self) -> bool:
        """检查MongoDB是否可用"""
        return self.mongodb_available
    
    def is_redis_available(self) -> bool:
        """检查Redis是否可用"""
        return self.redis_available
    
    def is_database_available(self) -> bool:
        """检查是否有任何数据库可用"""
        return self.mongodb_available or self.redis_available
    
    def get_cache_backend(self) -> str:
        """获取当前缓存后端"""
        return self.primary_backend

    def get_config(self) -> Dict[str, Any]:
        """获取配置信息"""
        return {
            "mongodb": self.mongodb_config,
            "redis": self.redis_config,
            "primary_backend": self.primary_backend,
            "mongodb_available": self.mongodb_available,
            "redis_available": self.redis_available,
            "cache": {
                "primary_backend": self.primary_backend,
                "fallback_enabled": True,  # 总是启用降级
                "ttl_settings": {
                    # 美股数据TTL（秒）
                    "us_stock_data": 7200,  # 2小时
                    "us_news": 21600,  # 6小时
                    "us_fundamentals": 86400,  # 24小时
                    # A股数据TTL（秒）
                    "china_stock_data": 3600,  # 1小时
                    "china_news": 14400,  # 4小时
                    "china_fundamentals": 43200,  # 12小时
                }
            }
        }

    def get_status_report(self) -> Dict[str, Any]:
        """获取状态报告"""
        return {
            "database_available": self.is_database_available(),
            "mongodb": {
                "available": self.mongodb_available,
                "host": self.mongodb_config["host"],
                "port": self.mongodb_config["port"]
            },
            "redis": {
                "available": self.redis_available,
                "host": self.redis_config["host"],
                "port": self.redis_config["port"]
            },
            "cache_backend": self.get_cache_backend(),
            "fallback_enabled": True  # 总是启用降级
        }

    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        stats = {
            "mongodb_available": self.mongodb_available,
            "redis_available": self.redis_available,
            "redis_keys": 0,
            "redis_memory": "N/A"
        }

        # Redis统计
        if self.redis_available and self.redis_client:
            try:
                info = self.redis_client.info()
                stats["redis_keys"] = self.redis_client.dbsize()
                stats["redis_memory"] = info.get("used_memory_human", "N/A")
            except Exception as e:
                self.logger.error(f"获取Redis统计失败: {e}")

        return stats

    def cache_clear_pattern(self, pattern: str) -> int:
        """清理匹配模式的缓存"""
        cleared_count = 0

        if self.redis_available and self.redis_client:
            try:
                keys = self.redis_client.keys(pattern)
                if keys:
                    cleared_count += self.redis_client.delete(*keys)
            except Exception as e:
                self.logger.error(f"Redis缓存清理失败: {e}")

        return cleared_count


# 全局数据库管理器实例
_database_manager = None

def get_database_manager() -> DatabaseManager:
    """获取全局数据库管理器实例"""
    global _database_manager
    if _database_manager is None:
        _database_manager = DatabaseManager()
    return _database_manager

def is_mongodb_available() -> bool:
    """检查MongoDB是否可用"""
    return get_database_manager().is_mongodb_available()

def is_redis_available() -> bool:
    """检查Redis是否可用"""
    return get_database_manager().is_redis_available()

def get_cache_backend() -> str:
    """获取当前缓存后端"""
    return get_database_manager().get_cache_backend()

def get_mongodb_client():
    """获取MongoDB客户端"""
    return get_database_manager().get_mongodb_client()

def get_redis_client():
    """获取Redis客户端"""
    return get_database_manager().get_redis_client()
