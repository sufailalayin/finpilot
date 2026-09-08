# FinPilot Architecture

## Product surfaces

### Mobile
Flutter application for end users. Android is the first release target. The architecture remains portable to iOS.

### Backend
FastAPI owns authentication, financial records, entitlements, AI orchestration, notifications and admin APIs.

### Admin
Next.js console for aggregate product operations: users, trials, subscriptions, revenue, AI usage, support and system health.

## Data

PostgreSQL is the source of truth. Redis supports caching, rate limiting and asynchronous workloads.

Core domains planned:

- identity and authentication
- user profile and preferences
- financial accounts
- categories
- transactions
- budgets
- savings goals
- recurring bills
- subscription entitlements
- AI conversations and usage metadata
- audit events

## Subscription lifecycle

A newly eligible account receives a server-controlled 7-day Pro trial. Paid Android entitlements will be verified server-side against Google Play rather than trusted from the device.

## AI privacy boundary

The AI layer receives only the minimum user context needed to answer a request. Secrets stay server-side. Admin analytics should be aggregate by default and access to user-level financial data must be explicitly authorized and audited.

## Security principles

- tenant isolation on every user-owned record
- short-lived access tokens and refresh-token rotation
- server-side entitlement verification
- rate limiting
- encryption in transit and appropriate encryption at rest
- no secrets committed to Git
- immutable/auditable administrative actions
- least-privilege admin roles
