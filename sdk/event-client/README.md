# Event Client SDK

Shared client for subscribing to real-time domain events via the WebSocket or SSE gateway.

```ts
import { EventClient } from "@sdk/event-client";

const client = new EventClient("wss://gateway/ws");
client.on("UserCreated", (event) => {
  console.log("new user:", event.email);
});
```
