**PORTFOLIO INTELLIGENCE PLATFORM**

**Architecture Decision Records**

*Why the platform is built the way it is — decisions, alternatives, and trade-offs*

**Version:  **1.0

**Author:  **Kola

**Format:  **Lightweight ADR (Context / Decision / Alternatives / Consequences)


# **How to Read These Records**


***Each ADR captures one architecturally significant decision at the time it was made. Status is either Accepted or Proposed. Superseded decisions are kept for history rather than deleted, with a pointer to the record that replaces them.***


## **ADR-001 — Modular Monolith over Microservices**


**Status: **Accepted


### **Context**


***The team is four engineers building toward a portfolio project and eventual production use, with no existing operational experience running distributed systems in production. Domain boundaries (Auth, Portfolio, Analytics, Market Data) are fairly stable and don't yet need independent scaling or deployment cadences.***


### **Decision**


***Build a single deployable FastAPI service, internally partitioned into modules with clean interfaces (routers -> services -> repositories) so that any module can be extracted into its own service later without a rewrite.***


### **Alternatives Considered**


**Option**

**Why Not Chosen**

Microservices from day one

Adds network-boundary complexity (service discovery, distributed tracing, partial-failure handling) that isn't justified by current scale or team size; slows iteration speed.

Single unstructured monolith (no internal module boundaries)

Makes it harder to reason about ownership and would require a bigger rewrite if a service later needs to be split out.


### **Consequences**


- Faster local development and simpler CI/CD — one image, one deploy pipeline.

- No distributed transactions needed for the write path (transaction + holding update is a single DB transaction).

- Analytics Service is the most likely first candidate to extract if CPU-bound recompute load grows — the module boundary is already drawn.

- Trade-off: all modules currently scale together; a hot path in one module (e.g., Market Data fan-out) consumes capacity that Auth or Portfolio could otherwise use.


## **ADR-002 — PostgreSQL over MongoDB**


**Status: **Accepted


### **Context**


***Core domain data — transactions, holdings, portfolio snapshots — is inherently relational: a transaction belongs to exactly one holding, a holding to exactly one portfolio, and financial correctness depends on strong consistency and numeric precision.***


### **Decision**


***Use PostgreSQL as the system of record, with native ENUM types for asset/transaction types and NUMERIC columns for all monetary values.***


### **Alternatives Considered**


**Option**

**Why Not Chosen**

MongoDB

Document flexibility isn't needed here — the schema is stable and well-normalized. MongoDB's historical lack of arbitrary-precision decimal handling (pre-Decimal128) and weaker multi-document transaction guarantees are a poor fit for ledger-style financial data.

MySQL

Comparable fit to Postgres for this workload, but Postgres's native support for JSONB (for future flexible fields), window functions (useful for time-series analytics queries), and stronger standards compliance made it the preferred default.


### **Consequences**


- ACID guarantees make the transaction-insert + holding-update sequence safe under concurrent writes.

- NUMERIC avoids floating-point drift in XIRR/CAGR calculations, which is non-negotiable for financial correctness.

- Window functions simplify time-series analytics queries (e.g., rolling volatility) directly in SQL.

- Trade-off: horizontal write-scaling is harder than a natively sharded document store; mitigated for now by a read replica and the fact that write volume (transactions) is orders of magnitude lower than read volume (dashboard views).


## **ADR-003 — Redis as the Sole Caching Layer**


**Status: **Accepted


### **Context**


***The dashboard and analytics endpoints are read-heavy and latency-sensitive (< 200 ms target), but their underlying data changes infrequently relative to read volume (quotes every ~60s, snapshots daily, analytics on transaction events).***


### **Decision**


***Use Redis as a cache-aside layer in front of PostgreSQL for quotes, dashboard payloads, and analytics results, with short TTLs plus explicit invalidation on writes that affect cached keys.***


### **Alternatives Considered**


**Option**

**Why Not Chosen**

In-process (application-memory) caching

Doesn't work once the app is horizontally scaled across multiple containers — each instance would have an inconsistent view.

No caching, rely on read replica

Fails the < 200 ms latency budget once market-data fan-out and analytics joins are involved; also increases load on the external market data provider.


### **Consequences**


- Shared cache state across all application containers, which is required for the stateless/auto-scaling deployment model.

- Explicit invalidation (on transaction writes) is required in addition to TTLs — see the Domain Model & Analytics document for the full invalidation matrix.

- Trade-off: introduces a second infrastructure dependency; a Redis outage must degrade gracefully rather than fail requests (see System Design Document, Failure Scenarios).


## **ADR-004 — Asynchronous Analytics Recomputation**


**Status: **Accepted


### **Context**


***XIRR (iterative Newton-Raphson solve) and related analytics are more CPU-intensive than a simple ledger insert, and blocking the transaction-write path on them would risk breaking the latency budget under load.***


### **Decision**


***POST /transactions returns as soon as the ledger insert and holding update are committed; analytics recomputation is dispatched as a background task and cache invalidation happens once recomputation completes.***


### **Alternatives Considered**


**Option**

**Why Not Chosen**

Synchronous recompute in the request path

Simple, but couples write latency to analytics compute cost and doesn't scale as portfolio size or transaction frequency grows.

Recompute on read (lazy)

Would make dashboard reads unpredictably slow immediately after a transaction, which is worse for the highest-traffic endpoint.


### **Consequences**


- Write path stays fast and predictable regardless of portfolio complexity.

- There is a brief window (typically sub-second to a few seconds) where the dashboard may reflect stale analytics after a transaction — acceptable for this domain, and callers can poll or the client can optimistically update quantity/value while XIRR catches up.

- Starts on FastAPI BackgroundTasks for the MVP; the module boundary is drawn so this can move to a Celery + Redis (or SQS-backed) queue without changing the Analytics Service's public interface if job volume or retry needs grow.


## **ADR-005 — JWT Access + Refresh Tokens over Server-Side Sessions**


**Status: **Accepted


### **Context**


***The API needs to support both a web dashboard and eventually mobile clients, and containers are stateless so any session state must either be shared (Redis) or embedded in the token itself.***


### **Decision**


***Issue short-lived JWT access tokens (15 min) and longer-lived rotating refresh tokens (7 days), with an active-session record mirrored in Redis to support explicit revocation.***


### **Alternatives Considered**


**Option**

**Why Not Chosen**

Pure server-side sessions (cookie + session store)

Works, but adds a mandatory Redis round-trip on every request for session lookup, and is a worse fit for non-browser mobile clients.

Long-lived JWT with no refresh/revocation mechanism

Simpler, but a leaked long-lived token can't be revoked before natural expiry — unacceptable for a finance product.


### **Consequences**


- Most requests validate the JWT signature locally (no DB/Redis hit), keeping the auth check fast.

- Refresh-token rotation (a new refresh token is issued on every use, and reuse of an old one invalidates the whole chain) limits the blast radius of a stolen refresh token — detailed in the Security Threat Model.

- Requires careful client-side handling of token refresh and logout-everywhere flows.


## **ADR-006 — URI Path API Versioning (/api/v1/...)**


**Status: **Accepted


### **Context**


***The analytics contract (response shapes for XIRR, allocation, risk) is the part of this API most likely to evolve as new metrics are added, and breaking existing clients silently is unacceptable once a dashboard depends on the contract.***


### **Decision**


***Prefix all routes with /api/v1. Breaking changes ship as /api/v2 routes running alongside v1 until clients migrate; additive changes (new optional fields) do not require a version bump.***


### **Alternatives Considered**


**Option**

**Why Not Chosen**

Header-based versioning (Accept: application/vnd.pip.v1+json)

More RESTfully 'pure' but harder to test, cache, and debug from a browser or simple HTTP client — path versioning is more discoverable for this project's scope.

No versioning

Fine short-term, but forces either breaking existing clients on every analytics change or indefinitely maintaining backward-compatible response shapes inline, which gets messy fast.


### **Consequences**


- Clear, greppable migration path in code (v1/routers/, v2/routers/).

- Slight duplication when a v2 route reuses most of a v1 handler — mitigated by sharing service-layer code and only duplicating the router/schema layer.