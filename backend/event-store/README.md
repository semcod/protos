# Event Store

SQLite-backed append-only event log with snapshot support.

See `scripts/event_store.py` for the implementation used across all backend services.

## Schema

```sql
-- events table: all domain events across all aggregates
-- snapshots table: optional aggregate state cache
```

In production, replace SQLite with PostgreSQL + EventStoreDB or Kafka.
