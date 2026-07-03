**PORTFOLIO INTELLIGENCE PLATFORM**

**System Design Document**

*Component interactions, sequence flows, and deployment topology*

**Version:  **1.0

**Author:  **Kola

**Companion Docs:  **EDD · API Specification · Database Schema & ER Diagram


# **1. Component Interactions**


***PIP is implemented as a modular monolith. Each service is an independent module with a clear responsibility boundary, communicating in-process through the FastAPI application, and out-of-process only with PostgreSQL, Redis, and the external market data provider.***

**Component**

**Depends On**

**Communication**

Auth Service

PostgreSQL, Redis

Sync (in-process call from Gateway)

Portfolio Service

PostgreSQL

Sync

Analytics Service

PostgreSQL, Portfolio Service

Sync (read) + Async (recompute trigger)

Market Data Service

Redis, External Provider

Sync with cache-through

Dashboard Service

Redis, Portfolio, Analytics, Market Data

Sync aggregation with cache-aside

***Analytics recomputation after a transaction is dispatched asynchronously (FastAPI BackgroundTasks in the MVP; can be promoted to a Celery/Redis queue if recompute volume grows) so the write path stays fast and the client is not blocked on XIRR recalculation.***


# **2. Sequence Diagrams**



## **2.1 Login Flow**


***A user authenticates and receives a short-lived access token plus a longer-lived refresh token. The session is mirrored into Redis to support fast revocation checks.***

*Figure 1 — Authentication sequence*


## **2.2 Record Transaction & Recompute Analytics**


***Writing a transaction is kept on the fast path (ledger insert + holding update). XIRR/CAGR recomputation and cache invalidation happen asynchronously so POST /transactions stays under the 200 ms latency budget.***

*Figure 2 — Transaction write and async analytics recompute*


## **2.3 Dashboard Read (Cache-Aside)**


***The dashboard is the highest-traffic read endpoint, so it is served cache-first with a 30-second TTL. On a cache miss, the Dashboard Service fan-outs to Portfolio, Analytics, and Market Data, assembles one response, and re-populates the cache.***

*Figure 3 — Dashboard cache-aside read path*


## **2.4 Cache Miss vs. Cache Invalidation**


***These are two distinct events worth showing separately: a miss is a read finding nothing cached and repopulating it; an invalidation is a write proactively deleting a now-stale key. Conflating them is a common source of stale-dashboard bugs.***

*Figure 4 — Cache miss (steps 1-7) followed by a write-triggered invalidation (steps 8-9)*


## **2.5 Scheduled Background Jobs**


***Two recurring jobs keep cached and derived data fresh without being triggered by any single user request: a 60-second market price refresh, and a daily portfolio snapshot generation run. The MVP runs these via APScheduler inside the application process; if job volume grows, they can move to a dedicated worker without changing the Market Data or Portfolio service interfaces.***

*Figure 5 — Scheduled market refresh and daily snapshot generation*


# **3. Deployment Diagram**


***The application is packaged as a single Docker image and horizontally scaled behind a load balancer. GitHub Actions builds, tests, and pushes the image to a container registry; the platform (Render/Railway) then performs a rolling deploy with health-check gating.***

*Figure 4 — Deployment topology*


## **Scaling Notes**


- Application containers are stateless — session state lives in Redis, so any container can serve any request, enabling simple horizontal auto-scaling.

- PostgreSQL runs as a primary with a read replica; analytics-heavy read queries can be routed to the replica as load grows.

- Redis is the single point of shared mutable cache state; a managed Redis cluster (with persistence disabled for pure cache use) keeps this layer simple.

- The Market Data Provider is called through a cache-through wrapper so a provider outage degrades to stale-but-available quotes rather than failing requests outright.


# **4. Cross-Cutting Concerns**


**Concern**

**Implementation**

AuthN/AuthZ

JWT bearer token validated by a FastAPI dependency on every protected route; resource ownership checked at the repository layer.

Validation

Pydantic models enforce request schema and type/range constraints before reaching service logic.

Rate Limiting

Redis-backed sliding-window limiter at the Gateway layer (per-user and per-IP).

Caching

Cache-aside pattern for dashboard/analytics/quotes; explicit invalidation on writes that affect cached keys.

Logging

Structured JSON logs with request_id correlation across service boundaries.

Error Handling

Centralized exception handlers map domain exceptions to the standard error envelope.


# **5. Observability**


***Three pillars are treated as first-class, not bolted on: structured logs for debugging specific requests, metrics for aggregate system health, and distributed tracing for following a request across service boundaries within the monolith.***


## **5.1 Request Correlation**


***Every inbound request is assigned a request_id (UUID) at the Gateway layer via middleware, propagated through every log line and background task spawned from that request, and returned to the client in an X-Request-ID response header so a user-reported issue can be traced end-to-end.***

{"timestamp":"2026-07-03T09:15:00Z","level":"INFO","request_id":"7f3a...","user_id":"usr_9f2a","event":"transaction.created","holding_id":"hld_11","latency_ms":42}


## **5.2 Metrics (Prometheus)**


**Metric**

**Type**

**Purpose**

http_request_duration_seconds

Histogram (by route, method, status)

Latency budget tracking (< 200 ms target) and SLO alerting

cache_hit_ratio

Gauge (by key prefix)

Validates the caching strategy is actually reducing DB load

xirr_solver_iterations

Histogram

Detects analytics correctness/performance regressions (e.g., non-convergence spikes)

background_job_duration_seconds

Histogram (by job name)

Tracks scheduler job health (market refresh, snapshot generation)

market_provider_errors_total

Counter

Early warning for upstream market data provider degradation

***Proposed: Metrics are planned to be exposed on /metrics and scraped by Prometheus; Grafana dashboards will visualize p50/p95/p99 latency per route, cache hit ratio trends, and job success rates, with alerting rules on latency SLO breaches and elevated error rates (not yet active in the current implementation).***



## **5.3 Health Checks**


***/health/live confirms the process is running; /health/ready confirms it can reach PostgreSQL and Redis, and is what the load balancer and deploy pipeline gate on before routing traffic to a new container.***


# **6. Security Threat Model**


***Threats are organized by the asset they target. This is a living document — new endpoints or integrations should be checked against it before shipping.***


## **6.1 Authentication & Session**


**Threat**

**Mitigation**

Stolen access token replay

Short 15-minute expiry limits the exposure window; tokens are only ever transmitted over HTTPS.

Stolen refresh token replay

Refresh-token rotation: each use issues a new refresh token and invalidates the old one. Reuse of an already-rotated token invalidates the entire session chain and forces re-login (signals likely theft).

Brute-force login attempts

Rate limiting per email and per IP on /auth/login (e.g., 5 attempts / 15 min), with exponential backoff and eventual temporary lockout.

Password database compromise

Passwords are bcrypt-hashed with a per-password salt (cost factor 12); plaintext is never logged or stored.

Session fixation / logout not effective

Logout deletes the Redis-mirrored session record immediately, independent of the JWT's own expiry, enabling true server-side revocation.


## **6.2 Transport & API Surface**


**Threat**

**Mitigation**

Man-in-the-middle

HTTPS enforced end-to-end; HSTS header set; TLS termination at the load balancer with modern cipher suites only.

CORS misconfiguration

Explicit allow-list of known frontend origins; no wildcard (*) origin, especially since Authorization headers are in play.

CSRF

Not applicable to the current bearer-token-in-header design (CSRF targets cookie-based auth). If cookie-based auth is ever introduced for browser convenience, SameSite=Strict cookies plus a double-submit CSRF token become mandatory before shipping.

SQL injection

SQLAlchemy ORM with parameterized queries exclusively; no raw string-interpolated SQL anywhere in the codebase.

Mass-assignment / over-posting

Pydantic request schemas are explicit allow-lists of fields; unknown fields are rejected, not silently accepted.

IDOR (accessing another user's portfolio by guessing an ID)

Every repository-layer query filters by the authenticated user_id in addition to the resource ID; UUIDs (non-sequential) additionally reduce guessability.


## **6.3 Secrets & Configuration**


- Database credentials, JWT signing keys, and the market-data provider API key are injected via environment variables from a secrets manager — never committed to source control.

- JWT signing uses an asymmetric algorithm (RS256) in production so the public key can be distributed to any service that needs to verify tokens without holding the ability to mint them.

- Different secrets per environment (dev/staging/prod); production secrets are not accessible to developer machines.


# **7. Failure Modes & Resilience**


**Failure**

**Detection**

**Mitigation**

**Recovery**

Market Data Provider down

market_provider_errors_total spikes; provider health check fails

Serve last cached quote (stale-while-revalidate); flag response with source: "stale-cache"

Scheduler retries with exponential backoff; alert fires if stale beyond 10 min

Redis unavailable

Connection errors on cache GET/SET

Fall back to direct DB reads with degraded (but correct) latency rather than failing the request

Redis reconnect with circuit breaker; cache repopulates naturally once restored

PostgreSQL primary failover

Connection refused / replica lag alert

Managed failover to standby; read-only queries can temporarily route to replica

Application retries idempotent reads; writes queue briefly and retry with backoff

Analytics background job failure

Job exception logged with request_id; background_job_duration_seconds shows failure

Failed jobs retried with backoff (max 3 attempts); dashboard falls back to last-known PortfolioSnapshot

Dead-letter after max retries with alert for manual investigation

Duplicate transaction submission (client retry)

N/A — prevented, not just detected

Idempotency-Key header on POST /transactions; duplicate keys within 24h return the original response instead of double-booking

N/A

Scheduler misses a run (deploy restart mid-cycle)

Missed-run alert if no execution within 2x expected interval

Jobs are idempotent (safe to re-run) so a missed run self-heals on the next tick

Manual trigger endpoint (admin-only) to force an immediate run if needed