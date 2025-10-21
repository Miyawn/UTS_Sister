import asyncio
import os
import tempfile
import shutil
import time
import pytest

from api.dedup import DedupStore


def make_event(topic, eid, i=0):
    return type("Event", (), {
        "topic": topic,
        "event_id": eid,
        "timestamp": "2025-10-21T10:00:00Z",
        "source": "tests",
        "payload": {"n": i}
    })()


@pytest.mark.asyncio
async def test_enqueue_and_duplicate_detection():
    tmp = tempfile.mkdtemp()
    db = os.path.join(tmp, "dedup.db")
    store = DedupStore(db)
    await store.load()

    e = make_event("topicA", "id1")
    res1 = await store.enqueue_events([e])
    assert res1["unique"] == 1

    # duplicate
    res2 = await store.enqueue_events([e])
    assert res2["duplicate"] == 1

    shutil.rmtree(tmp)


@pytest.mark.asyncio
async def test_persistence_across_instances():
    tmp = tempfile.mkdtemp()
    db = os.path.join(tmp, "dedup.db")
    store = DedupStore(db)
    await store.load()
    e = make_event("topicB", "id2")
    await store.enqueue_events([e])

    # new instance should see duplicate
    store2 = DedupStore(db)
    await store2.load()
    res = await store2.enqueue_events([e])
    assert res["duplicate"] == 1

    shutil.rmtree(tmp)


@pytest.mark.asyncio
async def test_high_volume_small_stress():
    tmp = tempfile.mkdtemp()
    db = os.path.join(tmp, "dedup.db")
    store = DedupStore(db)
    await store.load()

    # 1000 events with 25% duplicates
    events = []
    for i in range(750):
        events.append(make_event("stress", f"id{i}", i))
    for i in range(250):
        # duplicates of first 250
        events.append(make_event("stress", f"id{i}", i))

    start = time.time()
    res = await store.enqueue_events(events)
    duration = time.time() - start
    # assert processed in a reasonable time locally
    assert res["unique"] == 750
    assert res["duplicate"] == 250
    assert duration < 10.0

    shutil.rmtree(tmp)
