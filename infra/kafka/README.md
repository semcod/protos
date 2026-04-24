# Kafka Infrastructure

Kafka broker configuration for production event streaming.

In development the Event Store uses SQLite.  In production, events are
published to Kafka topics and consumed by projection workers.

```
Topic naming convention:
  {aggregate}.{event_type}   e.g.  user.UserCreated
                                    billing.InvoiceCreated
```
