"""MongoDB Client and Persistence Management for finee.ai.

Provides singleton MongoDB connection management, connection pooling,
index management, and graceful in-memory fallback for test resilience.
"""

from __future__ import annotations

from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional
import uuid

try:
    from pymongo import ASCENDING, DESCENDING, MongoClient
    from pymongo.collection import Collection
    from pymongo.database import Database
    from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
    HAS_PYMONGO = True
except ImportError:  # pragma: no cover
    MongoClient = None  # type: ignore
    Database = None  # type: ignore
    Collection = None  # type: ignore
    ASCENDING = 1
    DESCENDING = -1
    HAS_PYMONGO = False

from src.core.config import settings

logger = logging.getLogger(__name__)


class InMemoryConversationCollection:
    """In-memory fallback collection for environments where MongoDB is unavailable."""

    def __init__(self) -> None:
        self._data: Dict[str, Dict[str, Any]] = {}

    def insert_one(self, document: Dict[str, Any]) -> Any:
        doc = dict(document)
        doc_id = doc.get("_id") or doc.get("id") or f"conv_{uuid.uuid4().hex[:16]}"
        doc["_id"] = doc_id
        self._data[doc_id] = doc
        return type("InsertResult", (), {"inserted_id": doc_id})()

    def find_one(self, filter: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        for item in self._data.values():
            match = True
            for k, v in filter.items():
                if k == "_id" and item.get("_id") != v:
                    match = False
                    break
                elif k != "_id" and item.get(k) != v:
                    match = False
                    break
            if match:
                return dict(item)
        return None

    def find(self, filter: Optional[Dict[str, Any]] = None, sort: Optional[List[tuple]] = None) -> List[Dict[str, Any]]:
        results = []
        filter = filter or {}
        for item in self._data.values():
            match = True
            for k, v in filter.items():
                if item.get(k) != v:
                    match = False
                    break
            if match:
                results.append(dict(item))

        # Basic sorting
        if sort:
            for field, order in reversed(sort):
                results.sort(
                    key=lambda x: (x.get(field) is not None, x.get(field)),
                    reverse=(order == -1 or order == DESCENDING),
                )
        return results

    def update_one(self, filter: Dict[str, Any], update: Dict[str, Any]) -> Any:
        target = self.find_one(filter)
        if not target:
            return type("UpdateResult", (), {"matched_count": 0, "modified_count": 0})()

        doc_id = target["_id"]
        doc = self._data[doc_id]

        if "$set" in update:
            for k, v in update["$set"].items():
                doc[k] = v

        if "$push" in update:
            for k, v in update["$push"].items():
                if k not in doc or not isinstance(doc[k], list):
                    doc[k] = []
                if isinstance(v, dict) and "$each" in v:
                    doc[k].extend(v["$each"])
                else:
                    doc[k].append(v)

        doc["updated_at"] = datetime.now(timezone.utc).isoformat()
        return type("UpdateResult", (), {"matched_count": 1, "modified_count": 1})()

    def delete_one(self, filter: Dict[str, Any]) -> Any:
        target = self.find_one(filter)
        if not target:
            return type("DeleteResult", (), {"deleted_count": 0})()
        doc_id = target["_id"]
        del self._data[doc_id]
        return type("DeleteResult", (), {"deleted_count": 1})()

    def count_documents(self, filter: Dict[str, Any]) -> int:
        return len(self.find(filter))

    def create_index(self, *args: Any, **kwargs: Any) -> str:
        return "in_memory_index"

    def clear(self) -> None:
        self._data.clear()


class MongoDBManager:
    """Singleton MongoDB Connection and Database Manager."""

    _instance: Optional[MongoDBManager] = None

    def __init__(self) -> None:
        self._client: Optional[MongoClient] = None
        self._db: Optional[Database] = None
        self._is_connected: bool = False
        self._fallback_collection = InMemoryConversationCollection()
        self._connect()

    def _connect(self) -> None:
        """Initialize connection to MongoDB with timeout."""
        if not HAS_PYMONGO:
            logger.warning("pymongo is not installed. Using in-memory fallback collection.")
            self._is_connected = False
            return

        try:
            uri = settings.MONGODB_URI
            db_name = settings.MONGODB_DATABASE
            self._client = MongoClient(
                uri,
                serverSelectionTimeoutMS=2000,
                connectTimeoutMS=2000,
                maxPoolSize=50,
            )
            # Ping database to verify connection
            self._client.admin.command("ping")
            self._db = self._client[db_name]
            self._is_connected = True
            logger.info("Connected successfully to MongoDB database '%s' at %s", db_name, uri)
            self._ensure_indexes()
        except Exception as exc:
            logger.warning(
                "MongoDB connection failed (%s). Falling back to in-memory persistence.",
                exc,
            )
            self._is_connected = False

    def _ensure_indexes(self) -> None:
        """Create necessary indexes for efficient queries."""
        if not self._is_connected or self._db is None:
            return
        try:
            conv_col = self._db["conversations"]
            conv_col.create_index(
                [("user_id", ASCENDING), ("is_pinned", DESCENDING), ("updated_at", DESCENDING)],
                name="idx_user_pinned_updated",
            )
            logger.info("MongoDB conversation indexes verified.")
        except Exception as exc:
            logger.warning("Failed to create MongoDB indexes: %s", exc)

    @property
    def is_connected(self) -> bool:
        """Check whether MongoDB connection is currently active."""
        if not self._is_connected or self._client is None:
            return False
        try:
            self._client.admin.command("ping")
            return True
        except Exception:
            return False

    def get_database(self) -> Optional[Database]:
        """Retrieve active MongoDB database instance."""
        return self._db if self.is_connected else None

    def get_collection(self, collection_name: str = "conversations") -> Any:
        """Retrieve MongoDB collection or in-memory fallback."""
        if self.is_connected and self._db is not None:
            return self._db[collection_name]
        return self._fallback_collection

    def close(self) -> None:
        """Close MongoDB connection."""
        if self._client:
            self._client.close()
            self._is_connected = False
            self._client = None
            self._db = None


_mongodb_manager = MongoDBManager()


def get_mongodb_manager() -> MongoDBManager:
    """Retrieve global singleton MongoDBManager."""
    return _mongodb_manager
