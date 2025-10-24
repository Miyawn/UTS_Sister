import asyncio
import time

import pytest
from fastapi.testclient import TestClient

from src.main import app, store, stats


@pytest.fixture(autouse=True)
def isolate_db(tmp_path, monkeypatch):
    db_file = tmp_path / "log_store.db"
    monkeypatch.setattr(store, "db_path", str(db_file))
    asyncio.get_event_loop().run_until_complete(store.initialize())
    stats["received"] = 0
    stats["unique_processed"] = 0
    stats["duplicate_dropped"] = 0
    q = getattr(app.state, "queue", None)
    if q is not None:
        while not q.empty():
            try:
                q.get_nowait()
                q.task_done()
            except Exception:
                break
    yield


def test_validation_rejects_missing_event_id():
    client = TestClient(app)
    resp = client.post("/publish", json={"topic": "t1"})
    assert resp.status_code == 200
    assert resp.json()["accepted"] == 0


def test_deduplication_counts():
    client = TestClient(app)
    ev = {"topic": "t1", "event_id": "a", "timestamp": "2020-01-01T00:00:00", "source": "x", "payload": {}}
    resp = client.post("/publish", json=ev)
    assert resp.status_code == 200
    resp = client.post("/publish", json=ev)
    assert resp.status_code == 200
    q = getattr(app.state, "queue", None)
    if q is not None:
        asyncio.get_event_loop().run_until_complete(q.join())
    resp = client.get("/stats")
    data = resp.json()
    assert data["unique_processed"] == 1
    assert data["duplicate_dropped"] == 1


def test_persistence_across_restarts(tmp_path, monkeypatch):
    client = TestClient(app)
    db_file = tmp_path / "log_store.db"
    monkeypatch.setattr(store, "db_path", str(db_file))
    asyncio.get_event_loop().run_until_complete(store.initialize())
    ev = {"topic": "t2", "event_id": "persist1", "timestamp": "2020-01-01T00:00:00", "source": "x", "payload": {}}
    resp = client.post("/publish", json=ev)
    q = getattr(app.state, "queue", None)
    if q is not None:
        asyncio.get_event_loop().run_until_complete(q.join())

    # simulate restart by creating new LogStore pointing to same DB
    from src.store import LogStore

    new_store = LogStore(db_path=str(db_file))
    asyncio.get_event_loop().run_until_complete(new_store.initialize())

    resp = client.post("/publish", json=ev)
    if q is not None:
        asyncio.get_event_loop().run_until_complete(q.join())
    resp = client.get("/stats")
    data = resp.json()
    assert data["unique_processed"] == 1
    assert data["duplicate_dropped"] == 1


def test_stats_consistency_multiple_events():
    client = TestClient(app)
    events = [
        {"topic": "t3", "event_id": "1"},
        {"topic": "t3", "event_id": "2"},
        {"topic": "t3", "event_id": "3"},
        {"topic": "t3", "event_id": "1"},
        {"topic": "t3", "event_id": "2"},
    ]
    resp = client.post("/publish", json=events)
    assert resp.status_code == 200
    q = getattr(app.state, "queue", None)
    if q is not None:
        asyncio.get_event_loop().run_until_complete(q.join())
    resp = client.get("/stats")
    data = resp.json()
    assert data["received"] == 5
    assert data["unique_processed"] == 3
    assert data["duplicate_dropped"] == 2
import asyncio
import os
import shutil
import tempfile
import time

import pytest
from fastapi.testclient import TestClient

from src.main import app, store, queue, stats
from src.store import LogStore


@pytest.fixture(autouse=True)
def isolate_db(tmp_path, monkeypatch):
    # Put DB in a temporary directory for each test
    db_file = tmp_path / "log_store.db"
    monkeypatch.setattr(store, "db_path", str(db_file))
    # re-initialize store
    asyncio.get_event_loop().run_until_complete(store.initialize())
    # reset stats
    stats["received"] = 0
    stats["unique_processed"] = 0
    stats["duplicate_dropped"] = 0
    # drain queue
    q = getattr(app.state, "queue", None)
    if q is not None:
        while not q.empty():
            try:
                q.get_nowait()
                q.task_done()
            except Exception:
                break
    yield


def test_validation_rejects_missing_event_id():
    client = TestClient(app)
    resp = client.post("/publish", json={"topic": "t1"})
    assert resp.status_code == 200
    assert resp.json()["accepted"] == 0


def test_deduplication_counts():
    client = TestClient(app)
    ev = {"topic": "t1", "event_id": "a", "timestamp": "2020-01-01T00:00:00", "source": "x", "payload": {}}
    resp = client.post("/publish", json=ev)
    assert resp.status_code == 200
    resp = client.post("/publish", json=ev)
    assert resp.status_code == 200

    # allow consumer to process
    q = getattr(app.state, "queue", None)
    if q is not None:
        asyncio.get_event_loop().run_until_complete(q.join())

    resp = client.get("/stats")
    data = resp.json()
    assert data["unique_processed"] == 1
    assert data["duplicate_dropped"] == 1


def test_persistence_across_restarts(tmp_path, monkeypatch):
    client = TestClient(app)
    db_file = tmp_path / "log_store.db"
    monkeypatch.setattr(store, "db_path", str(db_file))
    asyncio.get_event_loop().run_until_complete(store.initialize())
    ev = {"topic": "t2", "event_id": "persist1", "timestamp": "2020-01-01T00:00:00", "source": "x", "payload": {}}
    resp = client.post("/publish", json=ev)
    time.sleep(0.1)

    # simulate restart by creating a new LogStore instance pointing to same DB
    new_store = LogStore(db_path=str(db_file))
    asyncio.get_event_loop().run_until_complete(new_store.initialize())

    # publish same event again
    resp = client.post("/publish", json=ev)
    q = getattr(app.state, "queue", None)
    if q is not None:
        asyncio.get_event_loop().run_until_complete(q.join())
    resp = client.get("/stats")
    data = resp.json()
    assert data["unique_processed"] == 1
    assert data["duplicate_dropped"] == 1


def test_stats_consistency_multiple_events():
    client = TestClient(app)
    events = [
        {"topic": "t3", "event_id": "1"},
        {"topic": "t3", "event_id": "2"},
        {"topic": "t3", "event_id": "3"},
        {"topic": "t3", "event_id": "1"},
        {"topic": "t3", "event_id": "2"},
    ]
    resp = client.post("/publish", json=events)
    assert resp.status_code == 200
    asyncio.get_event_loop().run_until_complete(queue.join())
    resp = client.get("/stats")
    data = resp.json()
    assert data["received"] == 5
    assert data["unique_processed"] == 3
    assert data["duplicate_dropped"] == 2
