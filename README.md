# UTS_Sister - Pub/Sub Log Aggregator

This project is a small FastAPI-based Pub/Sub log aggregator with in-memory queue and SQLite persistence for unique events.

See `Dockerfile` and `docker-compose.yml` for running in Docker. For development with Docker inside a Kali VM (VirtualBox), prefer using Bridged networking or set up port forwarding.
Pub-Sub Log Aggregator

Run the FastAPI aggregator which consumes events via an in-memory asyncio.Queue and persists unique events into SQLite.

Features:
- Deduplication using UNIQUE(topic, event_id)
- /publish endpoint accepts single or batch events
- /events and /stats endpoints
