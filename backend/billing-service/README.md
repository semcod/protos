# Billing Service

CQRS command/query handlers for the `billing.v1` contract.

Consumes `contracts/billing/v1/billing.proto` and the generated `generated/python/billing_models.py`.

## Responsibilities

- Handle `CreateInvoiceCommand` → emit `InvoiceCreated` event
- Handle `PayInvoiceCommand` → emit `InvoicePaid` event
- Handle `GetInvoiceQuery` → return projection state
- Write events to the shared Event Store
