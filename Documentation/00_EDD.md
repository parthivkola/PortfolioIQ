**PORTFOLIO INTELLIGENCE PLATFORM**

**Engineering Design Document**

*A Financial Analytics Engine, with a portfolio-management surface on top*

**Version:  **2.0

**Author:  **Kola

**Target Company Inspiration:  **Groww

**Tech Stack:  **FastAPI · PostgreSQL · Redis · SQLAlchemy · Docker · GitHub Actions

**Companion Docs:  **API Specification · Database Schema & ER Diagram · System Design Document · Architecture Decision Records · Domain Model & Analytics Algorithms


# **1. Problem Statement**


***Retail investors often invest across multiple asset classes — Stocks, Mutual Funds, ETFs, Crypto, and Bonds — but existing platforms primarily focus on transaction execution. There is an opportunity to provide a unified backend service that aggregates portfolio data, computes advanced analytics, and exposes fast, scalable APIs for dashboards and financial insights.***

***This project builds a Financial Analytics Engine — the Portfolio, Holdings, and Transaction CRUD surface exists to feed clean, immutable data into that engine; the engine's XIRR, CAGR, risk, allocation, and tax-loss computations are the actual product. See the companion Domain Model & Analytics Algorithms document for the full mathematical treatment.***

***This is deliberately not a trading platform. It is a production-grade analytics and portfolio-intelligence backend capable of securely managing investment records, calculating financial metrics correctly, and serving analytics through REST APIs.***


# **2. Goals**



## **Functional Goals**


- User Authentication

- Portfolio Management

- Transaction Management

- Holdings Management

- Portfolio Analytics

- Dashboard APIs

- Market Data Integration

- Portfolio History

- Public REST APIs

- Production Deployment


## **Non-Functional Goals**


- < 200 ms average API latency (excluding external calls)

- Horizontally scalable architecture

- Clean, layered codebase (routers → services → repositories)

- 90%+ unit test coverage on analytics modules

- Secure authentication (JWT + bcrypt)

- Auto-generated, clean API documentation (OpenAPI)

- Fully Dockerized deployment


# **3. Non-Goals**


- Trading execution

- Payment gateway integration

- Real brokerage integration

- AI investment advice

- Options/Futures trading

- Social investing


# **4. Target Users**


**Persona**

**Core Needs**

Beginner Investor

Current portfolio value, profit/loss, simple dashboard

Active Investor

XIRR, CAGR, allocation breakdown, risk analytics

Power User

Portfolio snapshots, tax analytics, historical performance


# **5. Functional Requirements**



### **Authentication**


- Register

- Login

- JWT authentication

- Password hashing (bcrypt)

- Refresh tokens


### **Portfolio**


- Create

- Update

- Delete

- View portfolios


### **Holdings**


- Support Stocks, ETFs, Mutual Funds, Crypto, Bonds


### **Transactions**


- Buy

- Sell

- Dividend

- Bonus

- Split


### **Dashboard**


- Current value

- Total invested

- Today's gain

- Overall gain

- Top gainers/losers

- Recent transactions

- Asset allocation

- Sector allocation


### **Analytics**


- XIRR

- CAGR

- Absolute returns

- Unrealized P&L

- Realized P&L

- Daily P&L

- Portfolio allocation

- Market-cap allocation

- Sector allocation

- Diversification score

- Largest holding

- Dividend income

- Tax-loss opportunities


# **6. Non-Functional Requirements**


**Category**

**Requirement**

Availability

99% uptime target

Performance

Dashboard responses under 200 ms (cached)

Security

JWT auth, bcrypt hashing, HTTPS everywhere

Scalability

Stateless APIs, Redis caching, horizontal scale-out

Logging

Structured JSON logs

Observability

/health and /metrics endpoints


# **7. High-Level Architecture**


***The system follows a modular monolith pattern: a single deployable FastAPI application internally organized into distinct service modules (Auth, Portfolio, Analytics, Market Data, Dashboard), all sharing a common repository layer over PostgreSQL, with Redis as a shared cache.***

Client
  |
  v
FastAPI Gateway
  |
  +----------------+----------------+
  |                |                |
  v                v                v
Auth Service   Portfolio Service  Analytics Service
  |                |                |
  +----------------+----------------+
                   |
          Repository Layer
                   |
              PostgreSQL <----> Redis Cache
                   ^
                   |
          Market Data Provider


# **8. Low-Level Components**


**Component**

**Responsibilities**

Auth Service

Authentication, authorization, JWT issuance/validation, password hashing.

Portfolio Service

CRUD for portfolios, portfolio value computation, holdings orchestration.

Analytics Service

P&L, XIRR, CAGR, allocation, risk, and tax-related calculations.

Market Data Service

Quote retrieval, historical prices, caching, provider abstraction.

Dashboard Service

Aggregates Portfolio + Analytics + Transactions + Market Data into one optimized response.


# **9. Database Design (Summary)**


***Full schema, relationships, and ER diagram are provided in the companion Database Schema & ER Diagram document. Core entities:***

- Users

- Portfolio

- Holdings

- Transactions

- MarketSnapshot

- PortfolioSnapshot


# **10. API Design (Summary)**


***The full request/response contract is defined in the companion API Specification document. Endpoint groups:***

**Group**

**Endpoints**

Auth

POST /auth/register · POST /auth/login · POST /auth/refresh

Portfolio

GET/POST /portfolio · PUT/DELETE /portfolio/{id}

Holdings

GET/POST /holdings · PUT/DELETE /holdings/{id}

Transactions

GET/POST /transactions

Dashboard

GET /dashboard

Analytics

GET /analytics/performance, /allocation, /risk, /tax

Market

GET /market/search, /quote/{symbol}, /history/{symbol}


# **11. Caching Strategy**


**Cached Data**

**TTL**

Stock quotes

60 sec

Mutual fund NAV

60 sec

Portfolio dashboard

30 sec

User session

session lifetime

Frequently requested analytics

5 min


# **12. Security**


- JWT-based authentication

- BCrypt password hashing

- Rate limiting

- Input validation (Pydantic)

- SQL injection protection (parameterized ORM queries)

- CORS policy

- HTTPS enforced

- Environment-variable based config

- Secrets management


# **13. Deployment**


GitHub -> GitHub Actions -> Docker Build -> Deploy -> Render/Railway -> Health Check -> Production


# **14. Logging**


- Authentication events

- Errors

- API requests

- Cache hits/misses

- Market provider calls


# **15. Testing Strategy**


- Unit tests

- Integration tests

- API tests

- Authentication tests

- Analytics validation tests

- Load testing


# **16. Future Enhancements**


- Goal-based investing

- Benchmark comparison (e.g., Nifty 50)

- Watchlists

- Portfolio rebalancing suggestions

- CSV import/export

- Multi-currency support

- WebSocket live updates

- Notification service

- ML-based portfolio insights


# **17. Engineering Decisions & Trade-offs**


**Decision**

**Rationale**

Modular Monolith

Faster to develop and deploy than microservices while remaining easy to split later.

PostgreSQL

Reliable ACID-compliant relational database, ideal for transactional financial data.

Redis

Improves dashboard performance and reduces repeated market-data requests.

FastAPI

High-performance async Python framework with automatic OpenAPI documentation.

Repository Pattern

Separates business logic from persistence, improving testability and maintainability.

REST over GraphQL

Simpler for current scope; GraphQL can be revisited if frontend needs become more dynamic.


# **18. Domain Model Summary**


***Full entity definitions, state-transition rules, and analytics formulas live in the companion Domain Model & Analytics Algorithms document. The invariants that most shape the API and DB design:***

- Transactions are append-only — corrections are compensating entries, never edits or deletes.

- Holdings are derived from Transactions, not directly writable by normal API flow.

- Portfolio value is always computed (quantity x latest price), never stored as an editable field.

- A SELL cannot take quantity below zero; oversell attempts are rejected, not clamped.


# **19. Background Processing**


***Two scheduled jobs and one event-triggered async task keep derived data current without blocking the request path:***

**Job**

**Trigger**

**Purpose**

Market price refresh

Every 60s (scheduler)

Pull latest quotes for all held symbols; repopulate Redis and append MarketSnapshot rows

Portfolio snapshot generation

Daily @ 00:05 IST (scheduler)

Compute and persist each portfolio's value/invested/P&L as the day's PortfolioSnapshot

Analytics recompute

On transaction write (async, event-triggered)

Recompute XIRR/CAGR/allocation and invalidate affected cache keys

***Full sequence diagrams for all three are in the companion System Design Document, Section 2.***


# **20. Project Structure**


app/
  api/            # versioned routers (v1/, v2/) — request/response schemas only
  core/            # config, security primitives, dependency wiring
  auth/            # Auth Service: JWT issuance, password hashing
  portfolio/       # Portfolio Engine: CRUD + derivation from transactions
  analytics/       # Analytics Engine: XIRR, CAGR, risk, allocation, tax
  market/          # Market Data Service: provider abstraction, quote cache
  repositories/    # DB access layer (one repository per aggregate root)
  services/        # cross-cutting orchestration (e.g., Dashboard aggregation)
  models/          # SQLAlchemy ORM models
  schemas/         # Pydantic request/response schemas
  cache/           # Redis client + cache-aside helpers, invalidation matrix
  middleware/       # request_id injection, rate limiting, error envelope
  tasks/           # scheduled jobs + async background task handlers
  utils/           # shared helpers (date math, decimal handling)
tests/
  unit/            # analytics module tests (90%+ coverage target)
  integration/     # API + DB integration tests
alembic/           # DB migrations


# **21. Requirements Traceability Matrix**


***Maps each functional requirement to the service module, API endpoint(s), and database table(s) that implement it — the connective tissue between this EDD, the API Specification, and the Database Schema document.***

**Requirement**

**Service**

**API Endpoint(s)**

**Table(s)**

User registration & login

Auth Service

POST /auth/register, /auth/login, /auth/refresh

users

Portfolio CRUD

Portfolio Engine

GET/POST /portfolio, PUT/DELETE /portfolio/{id}

portfolio

Holdings management

Portfolio Engine

GET/POST /holdings, PUT/DELETE /holdings/{id}

holdings

Transaction recording

Portfolio Engine

GET/POST /transactions

transactions, holdings

Dashboard aggregation

Dashboard Service

GET /dashboard

holdings, transactions, portfoliosnapshot, marketsnapshot

XIRR / CAGR / P&L

Analytics Engine

GET /analytics/performance

transactions, portfoliosnapshot

Allocation & diversification

Analytics Engine

GET /analytics/allocation

holdings, marketsnapshot

Risk metrics

Analytics Engine

GET /analytics/risk

portfoliosnapshot, marketsnapshot

Tax-loss harvesting

Analytics Engine

GET /analytics/tax

holdings, marketsnapshot

Quote & history lookup

Market Data Service

GET /market/search, /quote/{symbol}, /history/{symbol}

marketsnapshot

Scheduled market refresh

Market Data Service

N/A (background job)

marketsnapshot

Scheduled snapshot generation

Portfolio Engine

N/A (background job)

portfoliosnapshot


# **Success Criteria**


***The project is successful if it:***

- Supports secure user authentication.

- Manages portfolios and transactions across multiple asset classes.

- Calculates accurate financial metrics (P&L, XIRR, CAGR, allocations).

- Serves a dashboard with low latency using caching.

- Is fully containerized, documented, tested, and deployable with CI/CD.

- Demonstrates production-quality backend architecture suitable for discussion in an SDE interview.