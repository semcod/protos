# WebSocket Gateway

WebSocket server that pushes domain events from the Event Store to all
connected clients in real-time.

```
Event Store → WS broadcast → all clients

// Client-side example
ws.on("UserCreated", (event) => {
  store.users.add(event);
});
```
