import asyncio
import json
from typing import Any, Dict, List

import aiosqlite

DB_PATH = "log_store.db"


class LogStore:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_lock = asyncio.Lock()

    async def initialize(self) -> None:
        async with self._init_lock:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    """
                    CREATE TABLE IF NOT EXISTS events (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        topic TEXT NOT NULL,
                        event_id TEXT NOT NULL,
                        timestamp TEXT,
                        source TEXT,
                        payload TEXT,
                        UNIQUE(topic, event_id)
                    )
                    """
                )
                await db.commit()

    async def insert_event(self, event: Dict[str, Any]) -> bool:
        """Insert event into DB. Return True if inserted, False if duplicate."""
        async with aiosqlite.connect(self.db_path) as db:
            try:
                await db.execute(
                    "INSERT INTO events (topic, event_id, timestamp, source, payload) VALUES (?, ?, ?, ?, ?)",
                    (
                        event.get("topic"),
                        event.get("event_id"),
                        event.get("timestamp"),
                        event.get("source"),
                        json.dumps(event.get("payload") or {}),
                    ),
                )
                await db.commit()
                return True
            except aiosqlite.IntegrityError:
                return False

    async def get_events_by_topic(self, topic: str) -> List[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute(
                "SELECT topic, event_id, timestamp, source, payload FROM events WHERE topic = ? ORDER BY id",
                (topic,),
            )
            rows = await cur.fetchall()
            await cur.close()
            result = []
            for r in rows:
                try:
                    payload = json.loads(r[4]) if r[4] else {}
                except Exception:
                    payload = {}
                result.append(
                    {
                        "topic": r[0],
                        "event_id": r[1],
                        "timestamp": r[2],
                        "source": r[3],
                        "payload": payload,
                    }
                )
            return result

    async def list_topics(self) -> List[str]:
        async with aiosqlite.connect(self.db_path) as db:
            cur = await db.execute("SELECT DISTINCT topic FROM events")
            rows = await cur.fetchall()
            await cur.close()
            return [r[0] for r in rows]
import asyncio
import json
from typing import Any, Dict, List

import aiosqlite

DB_PATH = "log_store.db"


class LogStore:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_lock = asyncio.Lock()

    async def initialize(self) -> None:
        async with self._init_lock:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    """
                    CREATE TABLE IF NOT EXISTS events (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        topic TEXT NOT NULL,
                        event_id TEXT NOT NULL,
                        timestamp TEXT,
                        source TEXT,
                        payload TEXT,
                        UNIQUE(topic, event_id)
                    )
                    """
                )
                # stats table to persist counters
                await db.execute(
                    """
                    CREATE TABLE IF NOT EXISTS stats (
                        key TEXT PRIMARY KEY,
                        value INTEGER NOT NULL
                    )
                    """
                )
                # ensure default counters exist
                for k in ("received", "unique_processed", "duplicate_dropped"):
                    await db.execute(
                        "INSERT OR IGNORE INTO stats (key, value) VALUES (?, ?)",
                        (k, 0),
                    )
                await db.commit()

    async def insert_event(self, event: Dict[str, Any]) -> bool:
        """Insert event into DB. Return True if inserted, False if duplicate."""
        async with aiosqlite.connect(self.db_path) as db:
            try:
                await db.execute(
                    "INSERT INTO events (topic, event_id, timestamp, source, payload) VALUES (?, ?, ?, ?, ?)",
                    (
                        event.get("topic"),
                        event.get("event_id"),
                        event.get("timestamp"),
                        event.get("source"),
                        json.dumps(event.get("payload") or {}),
                    ),
                )
                await db.commit()
                return True
            except aiosqlite.IntegrityError:
                return False

    async def increment_stat(self, key: str, delta: int = 1) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT INTO stats(key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = value + ?",
                (key, delta, delta),
            )
            await db.commit()

    async def get_all_stats(self) -> Dict[str, int]:
        async with aiosqlite.connect(self.db_path) as db:
            cur = await db.execute("SELECT key, value FROM stats")
            rows = await cur.fetchall()
            await cur.close()
            result = {"received": 0, "unique_processed": 0, "duplicate_dropped": 0}
            for r in rows:
                result[r[0]] = int(r[1])
            return result

    async def get_events_by_topic(self, topic: str) -> List[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute(
                "SELECT topic, event_id, timestamp, source, payload FROM events WHERE topic = ? ORDER BY id",
                (topic,),
            )
            rows = await cur.fetchall()
            await cur.close()
            result = []
            for r in rows:
                payload = {}
                try:
                    payload = json.loads(r[4]) if r[4] else {}
                except Exception:
                    payload = {}
                result.append(
                    {
                        "topic": r[0],
                        "event_id": r[1],
                        "timestamp": r[2],
                        "source": r[3],
                        "payload": payload,
                    }
                )
            return result

    async def list_topics(self) -> List[str]:
        async with aiosqlite.connect(self.db_path) as db:
            cur = await db.execute("SELECT DISTINCT topic FROM events")
            rows = await cur.fetchall()
            await cur.close()
            return [r[0] for r in rows]
