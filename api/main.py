import asyncio
import time
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, ValidationError
from typing import List, Dict, Any, Optional
from .dedup import DedupStore
from .db import init_db
from .utils import get_uptime
import os

app = FastAPI()
# compute a robust absolute path for the sqlite file (repo root/data/dedup.db)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
# Allow overriding DB path for tests or containers via environment variable
DEFAULT_DB = os.path.join(BASE_DIR, 'data', 'dedup.db')
DB_PATH = os.environ.get('AGG_DB_PATH', DEFAULT_DB)
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
dedup_store = DedupStore(DB_PATH)
start_time = time.time()

class EventPayload(BaseModel):
    # Accept any payload
    __root__: Dict[str, Any]

class Event(BaseModel):
    topic: str
    event_id: str
    timestamp: str
    source: str
    payload: EventPayload

@app.on_event("startup")
async def startup_event():
    await init_db(DB_PATH)
    await dedup_store.load()

@app.post("/publish")
async def publish(request: Request):
    try:
        data = await request.json()
        events = data if isinstance(data, list) else [data]
        valid_events = []
        for e in events:
            try:
                event = Event(**e)
                valid_events.append(event)
            except ValidationError as ve:
                continue
        if not valid_events:
            raise HTTPException(status_code=400, detail="No valid events")
        results = await dedup_store.enqueue_events(valid_events)
        return JSONResponse({"received": len(events), "unique_processed": results["unique"], "duplicate_dropped": results["duplicate"]})
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/events")
async def get_events(topic: Optional[str] = None):
    events = await dedup_store.get_events(topic)
    return events

@app.get("/stats")
async def get_stats():
    stats = await dedup_store.get_stats()
    stats["uptime"] = get_uptime(start_time)
    return stats
