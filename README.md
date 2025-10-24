# UTS_Sister - Pub/Sub Log Aggregator

This project is a small FastAPI-based Pub/Sub log aggregator with in-memory queue and SQLite persistence for unique events.

See `Dockerfile` and `docker-compose.yml` for running in Docker. For development with Docker inside a Kali VM (VirtualBox), prefer using Bridged networking or set up port forwarding.
Pub-Sub Log Aggregator

Run the FastAPI aggregator which consumes events via an in-memory asyncio.Queue and persists unique events into SQLite.

Features:
- Deduplication using UNIQUE(topic, event_id)
- /publish endpoint accepts single or batch events
- /events and /stats endpoints

How to build & run (Kali VM - bash)

1) Prepare data dir (persistence):

```bash
mkdir -p data
chown $USER:$USER data
```

2) Build image:

```bash
docker build -t uts-aggregator .
```

3) Run container (mount data and set DB path):

```bash
docker run --rm -p 8080:8080 \
	-v "$(pwd)/data":/app/data \
	-e DEDUP_DB=/app/data/dedup_store.db \
	uts-aggregator
```

4) Quick test endpoints:

POST /publish -> send single or array of events
GET /events?topic=topic-1
GET /stats

Using docker-compose (recommended for aggregator+publisher demo):

```bash
docker compose up --build
```

Notes & assumptions:
- SQLite DB path controlled by env `DEDUP_DB` (default `log_store.db` if not set).
- Keep project and `data/` on VM filesystem (not a Windows shared mount) to avoid SQLite locking/perf issues.
- For VS Code editing, use Remote-SSH to the Kali VM for best workflow.

