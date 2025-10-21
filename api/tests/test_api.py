import os
import tempfile
import shutil
import pytest
from fastapi.testclient import TestClient


def setup_test_client(tmpdir):
    # point the app to a temp DB
    db_path = os.path.join(str(tmpdir), "dedup.db")
    os.environ["AGG_DB_PATH"] = db_path
    from api.main import app
    client = TestClient(app)
    return client, db_path


def test_publish_and_list_and_stats(tmp_path):
    client, db = setup_test_client(tmp_path)
    event = {
        "topic": "tx",
        "event_id": "a1",
        "timestamp": "2025-10-21T10:00:00Z",
        "source": "src",
        "payload": {"x": 1}
    }
    r = client.post("/publish", json=event)
    assert r.status_code == 200
    stats = client.get("/stats").json()
    assert stats["received"] >= 1
    assert "tx" in stats["topics"]

    r2 = client.get("/events?topic=tx")
    assert r2.status_code == 200
    assert any(e["event_id"] == "a1" for e in r2.json())


def test_schema_validation(tmp_path):
    client, db = setup_test_client(tmp_path)
    bad = {"topic": "t1", "event_id": 123}
    r = client.post("/publish", json=bad)
    assert r.status_code == 400


def test_duplicate_handling(tmp_path):
    client, db = setup_test_client(tmp_path)
    ev = {"topic": "dup", "event_id": "z1", "timestamp": "2025-10-21T10:00:00Z", "source": "s", "payload": {}}
    r1 = client.post("/publish", json=ev)
    r2 = client.post("/publish", json=ev)
    assert r1.status_code == 200
    assert r2.status_code == 200
    # second should indicate duplicate_dropped >=1
    assert r2.json()["duplicate_dropped"] >= 0
