# User Service

CQRS command/query handlers for the `user.v1` contract.

Consumes `contracts/user/v1/user.proto` and the generated `generated/python/user_models.py`.

## Responsibilities

- Handle `CreateUserCommand` → emit `UserCreated` event
- Handle `GetUserQuery` → return projection state
- Write events to the shared Event Store
