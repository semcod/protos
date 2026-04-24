# HTTP API Gateway

REST gateway that translates HTTP requests into gRPC commands/queries
directed at the backend CQRS services.

```
Client → POST /users → CreateUserCommand (gRPC) → user-service
Client → GET  /users/:id → GetUserQuery (gRPC) → user-service
```
