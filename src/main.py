import asyncio
import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field

from .store import LogStore

app = FastAPI()

# logger
logger = logging.getLogger("aggregator")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

store = LogStore()

start_time = time.time()

# in-memory cache of stats (DB is authoritative)
stats: Dict[str, int] = {"received": 0, "unique_processed": 0, "duplicate_dropped": 0}


class EventModel(BaseModel):
    topic: str = Field(...)
    event_id: str = Field(...)
    timestamp: Optional[datetime]
    source: Optional[str]
    payload: Optional[Dict[str, Any]]


@app.on_event("startup")
async def startup_event():
    await store.initialize()
    # create queue bound to event loop
    app.state.queue = asyncio.Queue()
    # load persisted stats
    try:
        persisted = await store.get_all_stats()
        stats.update(persisted)
        logger.info("Loaded persisted stats: %s", persisted)
    except Exception:
        logger.exception("Failed to load persisted stats")
    app.state.consumer = asyncio.create_task(consumer())


@app.on_event("shutdown")
async def shutdown_event():
    task = getattr(app.state, "consumer", None)
    if task:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


async def consumer():
    while True:
        q: asyncio.Queue = getattr(app.state, "queue", None)
        if q is None:
            await asyncio.sleep(0.1)
            continue
        event = await q.get()
        inserted = await store.insert_event(event)
        if inserted:
            stats["unique_processed"] += 1
            try:
                await store.increment_stat("unique_processed", 1)
            except Exception:
                logger.exception("Failed to increment unique_processed in DB")
            logger.info("Inserted unique event %s %s", event.get("topic"), event.get("event_id"))
        else:
            stats["duplicate_dropped"] += 1
            try:
                await store.increment_stat("duplicate_dropped", 1)
            except Exception:
                logger.exception("Failed to increment duplicate_dropped in DB")
            logger.info("Duplikasi terdeteksi %s %s", event.get("topic"), event.get("event_id"))
        q.task_done()


@app.post("/publish")
async def publish(request: Request):
    """
    Read raw JSON body to avoid automatic Pydantic validation 422 errors.
    Accept a single object or a list of objects.
    """
    try:
        payload = await request.json()
    except Exception:
        logger.exception("Failed to parse JSON body for /publish")
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    events: List[Dict[str, Any]] = []
    if isinstance(payload, list):
        events = payload
    elif isinstance(payload, dict):
        events = [payload]
    else:
        raise HTTPException(status_code=400, detail="Invalid payload type")

    accepted = 0
    for ev in events:
        if not isinstance(ev, dict):
            logger.warning("Skipping non-dict event: %s", type(ev))
            continue
        # basic validation
        if not ev.get("topic") or not ev.get("event_id"):
            logger.warning("Skipping event missing topic/event_id: %s", ev)
            continue
        stats["received"] += 1
        try:
            await store.increment_stat("received", 1)
        except Exception:
            logger.exception("Failed to increment received in DB")
        # normalize timestamp
        if ev.get("timestamp") and not isinstance(ev.get("timestamp"), str):
            try:
                ev["timestamp"] = ev["timestamp"].isoformat()
            except Exception:
                ev["timestamp"] = str(ev.get("timestamp"))
        await app.state.queue.put(ev)
        accepted += 1

    return {"accepted": accepted}


@app.get("/events")
async def get_events(topic: Optional[str] = None):
    if not topic:
        raise HTTPException(status_code=400, detail="topic is required")
    events = await store.get_events_by_topic(topic)
    return {"events": events}


@app.get("/stats")
async def get_stats():
    uptime = int(time.time() - start_time)
    topics = await store.list_topics()
    persisted = {}
    try:
        persisted = await store.get_all_stats()
    except Exception:
        logger.exception("Failed to read persisted stats")
    merged = {**persisted, **stats}
    return {
        "received": merged.get("received", 0),
        "unique_processed": merged.get("unique_processed", 0),
        "duplicate_dropped": merged.get("duplicate_dropped", 0),
        "topics": topics,
        "uptime": uptime,
    }
import asyncio
import time
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException

from .store import LogStore

app = FastAPI()

store = LogStore()

start_time = time.time()

# in-memory stats
stats: Dict[str, int] = {"received": 0, "unique_processed": 0, "duplicate_dropped": 0}


@app.on_event("startup")
async def startup_event():
    await store.initialize()
    app.state.queue = asyncio.Queue()
    app.state.consumer = asyncio.create_task(consumer())


@app.on_event("shutdown")
async def shutdown_event():
    task = getattr(app.state, "consumer", None)
    if task:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


async def consumer():
    while True:
        q = getattr(app.state, "queue", None)
        if q is None:
            await asyncio.sleep(0.1)
            continue
        event = await q.get()
        inserted = await store.insert_event(event)
        if inserted:
            stats["unique_processed"] += 1
        else:
            stats["duplicate_dropped"] += 1
            print("Duplikasi terdeteksi", event.get("topic"), event.get("event_id"))
        q.task_done()


@app.post("/publish")
async def publish(payload: Any):
    # accept single object or list
    events = []
    if isinstance(payload, list):
        events = payload
    elif isinstance(payload, dict):
        events = [payload]
    else:
        raise HTTPException(status_code=400, detail="Invalid payload")

    accepted = 0
    for ev in events:
        if not ev.get("topic") or not ev.get("event_id"):
            continue
        stats["received"] += 1
        if ev.get("timestamp") and not isinstance(ev.get("timestamp"), str):
            try:
                ev["timestamp"] = ev["timestamp"].isoformat()
            except Exception:
                ev["timestamp"] = str(ev.get("timestamp"))
        await app.state.queue.put(ev)
        accepted += 1

    return {"accepted": accepted}


@app.get("/events")
async def get_events(topic: Optional[str] = None):
    if not topic:
        raise HTTPException(status_code=400, detail="topic is required")
    events = await store.get_events_by_topic(topic)
    return {"events": events}


@app.get("/stats")
async def get_stats():
    uptime = int(time.time() - start_time)
    topics = await store.list_topics()
    return {
        "received": stats["received"],
        "unique_processed": stats["unique_processed"],
        "duplicate_dropped": stats["duplicate_dropped"],
        "topics": topics,
        "uptime": uptime,
    }
import asyncio
import json
import time
from datetime import datetime
import logging
from typing import Any, Dict, List, Optional

from fastapi import BackgroundTasks, FastAPI, HTTPException, Request
from pydantic import BaseModel, Field

from .store import LogStore

app = FastAPI()

# The queue will be created on startup so it's bound to the running event loop
queue: asyncio.Queue = None  # type: ignore
store = LogStore()

start_time = time.time()

# local in-memory cache (kept for speed) but persisted to DB as authoritative
stats: Dict[str, int] = {"received": 0, "unique_processed": 0, "duplicate_dropped": 0}

# logger
logger = logging.getLogger("aggregator")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


class EventModel(BaseModel):
    topic: str = Field(...)
    event_id: str = Field(...)
    timestamp: Optional[datetime]
    source: Optional[str]
    payload: Optional[Dict[str, Any]]


@app.on_event("startup")
async def startup_event():
    # initialize store and queue in the running event loop
    await store.initialize()
    app.state.queue = asyncio.Queue()
    # load persisted stats into memory
    try:
        persisted = await store.get_all_stats()
        stats.update(persisted)
    except Exception:
        logger.exception("Failed to load persisted stats")
    app.state.consumer_task = asyncio.create_task(consumer())


@app.on_event("shutdown")
async def shutdown_event():
    task = app.state.consumer_task
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


async def consumer():
    while True:
        q = getattr(app.state, "queue", None)
        if q is None:
            await asyncio.sleep(0.1)
            continue
        event = await q.get()
        inserted = await store.insert_event(event)
        if inserted:
            stats["unique_processed"] += 1
            try:
                await store.increment_stat("unique_processed", 1)
            except Exception:
                logger.exception("Failed to increment unique_processed in DB")
            logger.info("Inserted unique event %s %s", event.get("topic"), event.get("event_id"))
        else:
            stats["duplicate_dropped"] += 1
            try:
                await store.increment_stat("duplicate_dropped", 1)
            except Exception:
                logger.exception("Failed to increment duplicate_dropped in DB")
            logger.info("Duplikasi terdeteksi %s %s", event.get("topic"), event.get("event_id"))
        q.task_done()


@app.post("/publish")
async def publish(payload: Any):
    # Accept single object or list
    events = []
    if isinstance(payload, list):
        events = payload
    elif isinstance(payload, dict):
        events = [payload]
    else:
        raise HTTPException(status_code=400, detail="Invalid payload")

    accepted = 0
    for ev in events:
        # basic validation
        if not ev.get("topic") or not ev.get("event_id"):
            continue
        stats["received"] += 1
        try:
            await store.increment_stat("received", 1)
        except Exception:
            logger.exception("Failed to increment received in DB")
        # normalize timestamp to string
        if ev.get("timestamp") and not isinstance(ev.get("timestamp"), str):
            try:
                ev["timestamp"] = ev["timestamp"].isoformat()
            except Exception:
                ev["timestamp"] = str(ev.get("timestamp"))
        await app.state.queue.put(ev)
        accepted += 1

    return {"accepted": accepted}


@app.get("/events")
async def get_events(topic: str):
    if not topic:
        raise HTTPException(status_code=400, detail="topic is required")
    events = await store.get_events_by_topic(topic)
    return {"events": events}


@app.get("/stats")
async def get_stats():
    uptime = int(time.time() - start_time)
    topics = await store.list_topics()
    persisted = {}
    try:
        persisted = await store.get_all_stats()
    except Exception:
        logger.exception("Failed to read persisted stats")
    merged = {**persisted, **stats}
    return {
        "received": merged.get("received", 0),
        "unique_processed": merged.get("unique_processed", 0),
        "duplicate_dropped": merged.get("duplicate_dropped", 0),
        "topics": topics,
        "uptime": uptime,
    }
