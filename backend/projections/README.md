# Projections

Read-model projections that subscribe to the Event Store and build
query-optimised views from domain events.

## Examples

- `UserListProjection` — builds a flat list of active users from `UserCreated` / `UserDeactivated` events
- `InvoiceSummaryProjection` — builds per-user invoice totals from `InvoiceCreated` / `InvoicePaid` events
- `InventoryProjection` — builds current stock levels from `ItemAdded` / `StockUpdated` events
