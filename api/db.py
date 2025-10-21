import aiosqlite

async def init_db(db_path: str):
    async with aiosqlite.connect(db_path) as db:
        # legacy dedup/events tables (kept for compatibility)
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
        # User-provided schema: records table with unique hash and payload
        await db.execute("""
        CREATE TABLE IF NOT EXISTS records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hash TEXT UNIQUE,
            payload TEXT
        )""")
        await db.commit()
