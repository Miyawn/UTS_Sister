import os
import random
import time
import httpx

AGG = os.getenv("AGGREGATOR_URL", "http://aggregator:8080")

def gen_event(topic: str, eid: str):
    return {
        "topic": topic,
        "event_id": eid,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "source": "publisher",
        "payload": {"value": random.randint(0, 1000000)},
    }

def main():
    client = httpx.Client(timeout=10.0)
    total = int(os.getenv("TOTAL", "1000"))
    dup_rate = float(os.getenv("DUP_RATE", "0.2"))
    for i in range(total):
        if random.random() < dup_rate and i > 0:
            eid = str(random.randint(max(0, i-100), i))
        else:
            eid = str(i)
        ev = gen_event("topic-1", eid)
        try:
            r = client.post(f"{AGG}/publish", json=ev)
            print(i, r.status_code)
        except Exception as e:
            print("err", e)
    print("done")

if __name__ == '__main__':
    main()
import json
import random
import time
import uuid
from http.client import HTTPConnection
from urllib import request

import httpx

def generate_event(topic: str, eid: str):
    return {
        "topic": topic,
        "event_id": eid,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "source": "publisher",
        "payload": {"value": random.randint(0, 1000000)},
    }

def main():
    client = httpx.Client(timeout=30.0)
    total = 5000
    dup_rate = 0.2
    sent = 0
    for i in range(total):
        if random.random() < dup_rate and i > 0:
            # pick a recent id
            eid = str(random.randint(max(0, i-100), i))
        else:
            eid = str(i)
        ev = generate_event("topic-1", eid)
        try:
            resp = client.post("http://aggregator:8080/publish", json=ev)
            print(i, resp.status_code)
        except Exception as e:
            print("error", e)
        sent += 1
    print("done", sent)

if __name__ == "__main__":
    main()
