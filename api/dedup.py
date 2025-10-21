import aiosqlite
import asyncio
from typing import List, Dict, Optional

class DedupStore:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.queue = asyncio.Queue()
        self.stats = {"received": 0, "unique_processed": 0, "duplicate_dropped": 0, "topics": set()}
        self.events = []

    async def load(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
            CREATE TABLE IF NOT EXISTS dedup (
                topic TEXT,
                event_id TEXT,
                PRIMARY KEY (topic, event_id)
            )""")
            await db.execute("""
            CREATE TABLE IF NOT EXISTS events (
                topic TEXT,
                event_id TEXT,
                timestamp TEXT,
                source TEXT,
                payload TEXT
            )""")
            await db.commit()

    async def enqueue_events(self, events: List):
        unique = 0
        duplicate = 0
        for event in events:
            self.stats["received"] += 1
            self.stats["topics"].add(event.topic)
            async with aiosqlite.connect(self.db_path) as db:
                # Use records table with unique hash for durable dedup
                key = f"{event.topic}:{event.event_id}"
                # prepare payload serialization
                try:
                    payload_val = event.payload.dict()
                except Exception:
                    try:
                        payload_val = dict(event.payload)
                    except Exception:
                        payload_val = str(event.payload)
                # Try insert into records; if it violates unique constraint, it's a duplicate
                try:
                    await db.execute("INSERT INTO records (hash, payload) VALUES (?, ?)", (key, str(payload_val)))
                    # also insert into events table for listing
                    await db.execute("INSERT INTO events (topic, event_id, timestamp, source, payload) VALUES (?, ?, ?, ?, ?)", (event.topic, event.event_id, event.timestamp, event.source, str(payload_val)))
                    await db.commit()
                    self.stats["unique_processed"] += 1
                    unique += 1
                except aiosqlite.IntegrityError:
                    self.stats["duplicate_dropped"] += 1
                    duplicate += 1
        return {"unique": unique, "duplicate": duplicate}

    async def get_events(self, topic: Optional[str] = None):
        async with aiosqlite.connect(self.db_path) as db:
            if topic:
                cursor = await db.execute("SELECT topic, event_id, timestamp, source, payload FROM events WHERE topic=?", (topic,))
            else:
                cursor = await db.execute("SELECT topic, event_id, timestamp, source, payload FROM events")
            rows = await cursor.fetchall()
            return [dict(zip(["topic", "event_id", "timestamp", "source", "payload"], row)) for row in rows]

    async def get_stats(self):
        return {
            "received": self.stats["received"],
            "unique_processed": self.stats["unique_processed"],
            "duplicate_dropped": self.stats["duplicate_dropped"],
            "topics": list(self.stats["topics"])
        }
