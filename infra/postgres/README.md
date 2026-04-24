# PostgreSQL Infrastructure

PostgreSQL configuration for production persistence.

In development the Event Store uses SQLite.  In production, events are
persisted in PostgreSQL.

```sql
-- Core tables provisioned by the Event Store service:
--   events     (append-only event log)
--   snapshots  (aggregate state cache)
```

The generated SQL DDL files (`generated/sql/*.sql`) provision the
read-model (projection) tables.
