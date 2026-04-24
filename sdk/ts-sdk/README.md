# TypeScript SDK

Shared TypeScript client library used by both the web app and the desktop app.

Re-exports all generated Zod schemas from `generated/ts/zod/` and wraps
them with a typed gRPC-Web / fetch client.

```ts
import { CreateUserCommand } from "@sdk/user";

await client.user.createUser({
  email: "a@a.com",
  password: "123",
});
```
