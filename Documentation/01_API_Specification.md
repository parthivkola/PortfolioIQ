**PORTFOLIO INTELLIGENCE PLATFORM**

**API Specification**

*OpenAPI-first REST contract — request & response examples*

**Version:  **2.0

**Author:  **Kola

**Base URL:  **https://api.pip.dev/api/v1

**Auth Scheme:  **Bearer JWT (Authorization: Bearer <token>)


# **Conventions**


- All request/response bodies are JSON (Content-Type: application/json).

- Timestamps are ISO-8601 UTC (e.g., 2026-07-03T10:15:00Z).

- Monetary values are decimal strings to avoid float rounding errors.

- All endpoints except /api/v1/auth/register, /api/v1/auth/login, /api/v1/auth/refresh require a Bearer JWT.

- All list endpoints support pagination, sorting, and filtering (see Section below).

- Errors follow a consistent envelope with application-specific codes (see Error Codes section).


# **API Versioning**


***Every route is prefixed with /api/v1. This is a deliberate URI-path versioning choice — see ADR-006 in the companion Architecture Decision Records document for the rationale. Breaking changes to an existing resource ship as /api/v2 running alongside v1 until clients migrate; additive, backward-compatible changes (new optional response fields) do not require a version bump.***


# **Pagination, Sorting & Filtering**


***Every list endpoint (GET /portfolio, /holdings, /transactions, etc.) uniformly supports the following query parameters:***

**Param**

**Type**

**Default**

**Description**

page

integer

1

1-indexed page number

limit

integer

20 (max 100)

Items per page

sort

string

created_at

Field to sort by (endpoint-specific allow-list)

order

string

desc

asc or desc

filter[field]

string

—

Endpoint-specific filters, e.g. filter[asset_type]=STOCK

***Example: GET /api/v1/transactions?page=2&limit=10&sort=timestamp&order=desc&filter[transaction_type]=BUY***

**Every list response includes a meta block:**

{
  "meta": {
    "page": 2,
    "limit": 10,
    "total": 47,
    "total_pages": 5
  }
}


# **Standard Error Format**


***Errors use a consistent envelope with an application-specific code — not just an HTTP status — so clients can branch on exact failure reasons without parsing message strings.***

{
  "error": {
    "code": "TXN_002",
    "message": "Sell quantity exceeds current holding quantity",
    "field": "quantity"
  }
}


## **Application Error Codes**


***A representative subset — the full list lives alongside the code as an enum so it can never drift from the implementation.***

**Code**

**HTTP Status**

**Meaning**

AUTH_001

401

Invalid email or password

AUTH_002

401

Access token expired

AUTH_003

401

Refresh token reused/invalidated (possible theft — session revoked)

AUTH_004

429

Too many login attempts — temporarily locked

PORTFOLIO_001

404

Portfolio not found

PORTFOLIO_002

403

Portfolio does not belong to the authenticated user

PORTFOLIO_003

409

Portfolio name already exists for this user

PORTFOLIO_004

400

Portfolio cannot be deleted while it has open holdings

HOLDING_001

404

Holding not found

HOLDING_002

409

Holding already exists for this symbol in this portfolio

TXN_001

400

Sell would reduce quantity below zero

TXN_002

400

Sell quantity exceeds current holding quantity

TXN_003

409

Duplicate transaction (Idempotency-Key already used)

ANALYTICS_001

422

XIRR undefined for the given cash-flow series (Note: The API returns `null` for XIRR/CAGR in /performance instead of raising this exception to keep the dashboard functional)


MARKET_001

503

Market data provider unavailable — served stale cache if available

VALIDATION_ERROR

400

Generic request-schema validation failure


## **HTTP Status Codes Used**


**Code**

**Meaning**

200

OK — successful GET/PUT

201

Created — successful POST

204

No Content — successful DELETE

400

Bad Request — validation error

401

Unauthorized — missing/invalid/expired token

403

Forbidden — resource not owned by user

404

Not Found

409

Conflict — e.g., duplicate email

429

Too Many Requests — rate limited

500

Internal Server Error


# **1. Authentication**



### **POST  /api/v1/auth/register**


***Create a new user account.***

**Auth required: **No

**Request Body:**

{
  "email": "kola@example.com",
  "password": "StrongPass!23",
  "full_name": "Kola"
}

**Response (201 Created):**

{
  "id": "usr_9f2a",
  "email": "kola@example.com",
  "full_name": "Kola",
  "created_at": "2026-07-03T10:15:00Z"
}


### **POST  /api/v1/auth/login**


***Authenticate and receive an access/refresh token pair.***

**Auth required: **No

**Request Body:**

{
  "email": "kola@example.com",
  "password": "StrongPass!23"
}

**Response (200 OK):**

{
  "access_token": "eyJhbGciOi...",
  "refresh_token": "eyJhbGciOi...",
  "token_type": "bearer",
  "expires_in": 900
}


### **POST  /api/v1/auth/refresh**


***Exchange a valid refresh token for a new access token.***

**Auth required: **No

**Request Body:**

{
  "refresh_token": "eyJhbGciOi..."
}

**Response (200 OK):**

{
  "access_token": "eyJhbGciOi...",
  "token_type": "bearer",
  "expires_in": 900
}


# **2. Portfolio**



### **GET  /api/v1/portfolio**


***List all portfolios owned by the authenticated user.***

**Auth required: **Yes (Bearer JWT)

**Response (200 OK):**

{
  "data": [
    {
      "id": "pf_1a2b",
      "name": "Primary Portfolio",
      "created_at": "2026-01-10T08:00:00Z"
    }
  ],
  "meta": {
    "page": 1,
    "limit": 20,
    "total": 1
  }
}


### **POST  /api/v1/portfolio**


***Create a new portfolio.***

**Auth required: **Yes (Bearer JWT)

**Request Body:**

{
  "name": "Retirement Fund"
}

**Response (201 Created):**

{
  "id": "pf_3c4d",
  "name": "Retirement Fund",
  "created_at": "2026-07-03T10:20:00Z"
}


### **PUT  /api/v1/portfolio/{id}**


***Rename or update a portfolio.***

**Auth required: **Yes (Bearer JWT)

**Parameters:**

**Name**

**In**

**Type**

**Description**

id

path

string

Portfolio ID

**Request Body:**

{
  "name": "Retirement Fund (US)"
}

**Response (200 OK):**

{
  "id": "pf_3c4d",
  "name": "Retirement Fund (US)",
  "updated_at": "2026-07-03T11:00:00Z"
}


### **DELETE  /api/v1/portfolio/{id}**


***Delete a portfolio and cascade-delete its holdings/transactions.***

**Auth required: **Yes (Bearer JWT)

**Parameters:**

**Name**

**In**

**Type**

**Description**

id

path

string

Portfolio ID

**Response (204 No Content):**

{}


# **3. Holdings**



### **GET  /api/v1/holdings**


***List holdings, optionally filtered by portfolio and asset type.***

**Auth required: **Yes (Bearer JWT)

**Parameters:**

**Name**

**In**

**Type**

**Description**

portfolio_id

query

string

Filter by portfolio

asset_type

query

string

STOCK | ETF | MUTUAL_FUND | CRYPTO | BOND

**Response (200 OK):**

{
  "data": [
    {
      "id": "hld_11",
      "portfolio_id": "pf_1a2b",
      "asset_type": "STOCK",
      "symbol": "RELIANCE",
      "quantity": "10",
      "average_buy_price": "2450.50"
    }
  ],
  "meta": {
    "page": 1,
    "limit": 20,
    "total": 1
  }
}


### **POST  /api/v1/holdings**


***Add a new holding to a portfolio.***

**Auth required: **Yes (Bearer JWT)

**Request Body:**

{
  "portfolio_id": "pf_1a2b",
  "asset_type": "MUTUAL_FUND",
  "symbol": "AXIS_BLUECHIP",
  "quantity": "150.234",
  "average_buy_price": "48.10"
}

**Response (201 Created):**

{
  "id": "hld_45",
  "portfolio_id": "pf_1a2b",
  "asset_type": "MUTUAL_FUND",
  "symbol": "AXIS_BLUECHIP",
  "quantity": "150.234",
  "average_buy_price": "48.10"
}


### **PUT  /api/v1/holdings/{id}**


***Update a holding's quantity or average buy price (recomputed automatically from transactions in normal flow; manual override for corrections).***

**Auth required: **Yes (Bearer JWT)

**Parameters:**

**Name**

**In**

**Type**

**Description**

id

path

string

Holding ID

**Request Body:**

{
  "quantity": "160.734",
  "average_buy_price": "47.85"
}

**Response (200 OK):**

{
  "id": "hld_45",
  "quantity": "160.734",
  "average_buy_price": "47.85",
  "updated_at": "2026-07-03T11:05:00Z"
}


### **DELETE  /api/v1/holdings/{id}**


***Remove a holding (only allowed when quantity is zero).***

**Auth required: **Yes (Bearer JWT)

**Parameters:**

**Name**

**In**

**Type**

**Description**

id

path

string

Holding ID

**Response (204 No Content):**

{}


# **4. Transactions**



### **GET  /api/v1/transactions**


***List transactions for a holding or portfolio, most recent first.***

**Auth required: **Yes (Bearer JWT)

**Parameters:**

**Name**

**In**

**Type**

**Description**

holding_id

query

string

Filter by holding

portfolio_id

query

string

Filter by portfolio

**Response (200 OK):**

{
  "data": [
    {
      "id": "txn_901",
      "holding_id": "hld_11",
      "transaction_type": "BUY",
      "quantity": "10",
      "price": "2450.50",
      "timestamp": "2026-02-14T09:31:00Z"
    }
  ],
  "meta": {
    "page": 1,
    "limit": 20,
    "total": 1
  }
}


### **POST  /api/v1/transactions**


***Record a transaction (BUY, SELL, DIVIDEND, BONUS, SPLIT). Triggers async recomputation of holding averages and portfolio snapshot.***

**Auth required: **Yes (Bearer JWT)

**Request Body:**

{
  "holding_id": "hld_11",
  "transaction_type": "BUY",
  "quantity": "5",
  "price": "2480.00",
  "timestamp": "2026-07-03T09:15:00Z"
}

**Response (201 Created):**

{
  "id": "txn_902",
  "holding_id": "hld_11",
  "transaction_type": "BUY",
  "quantity": "5",
  "price": "2480.00",
  "timestamp": "2026-07-03T09:15:00Z"
}


# **5. Dashboard**



### **GET  /api/v1/dashboard**


***Aggregated snapshot for the home screen. Backed by a 30s Redis cache keyed on user_id.***

**Auth required: **Yes (Bearer JWT)

**Parameters:**

**Name**

**In**

**Type**

**Description**

portfolio_id

query

string

Optional — omit for all portfolios combined

**Response (200 OK):**

{
  "current_value": "512340.75",
  "total_invested": "470000.00",
  "todays_gain": {
    "amount": "2310.40",
    "percent": "0.45"
  },
  "overall_gain": {
    "amount": "42340.75",
    "percent": "9.01"
  },
  "top_gainers": [
    {
      "symbol": "RELIANCE",
      "percent": "3.2"
    }
  ],
  "top_losers": [
    {
      "symbol": "AXIS_BLUECHIP",
      "percent": "-1.1"
    }
  ],
  "recent_transactions": [
    {
      "id": "txn_902",
      "transaction_type": "BUY",
      "symbol": "RELIANCE",
      "timestamp": "2026-07-03T09:15:00Z"
    }
  ],
  "asset_allocation": [
    {
      "asset_type": "STOCK",
      "percent": "64.2"
    },
    {
      "asset_type": "MUTUAL_FUND",
      "percent": "35.8"
    }
  ],
  "sector_allocation": [
    {
      "sector": "Energy",
      "percent": "28.5"
    }
  ]
}


# **6. Analytics**



### **GET  /api/v1/analytics/performance**


***Returns XIRR, CAGR, absolute returns, and realized/unrealized/daily P&L for a portfolio.***

**Auth required: **Yes (Bearer JWT)

**Parameters:**

**Name**

**In**

**Type**

**Description**

portfolio_id

query

string

Required

**Response (200 OK):**

{
  "xirr": "14.82",
  "cagr": "12.05",
  "absolute_return_percent": "9.01",
  "unrealized_pnl": "38210.10",
  "realized_pnl": "4130.65",
  "daily_pnl": "2310.40"
}


### **GET  /api/v1/analytics/allocation**


***Returns portfolio allocation by asset class, market cap, and sector, plus a diversification score.***

**Auth required: **Yes (Bearer JWT)

**Parameters:**

**Name**

**In**

**Type**

**Description**

portfolio_id

query

string

Required

**Response (200 OK):**

{
  "by_asset_type": [
    {
      "asset_type": "STOCK",
      "percent": "64.2"
    }
  ],
  "by_market_cap": [
    {
      "bucket": "LARGE_CAP",
      "percent": "70.0"
    }
  ],
  "by_sector": [
    {
      "sector": "Energy",
      "percent": "28.5"
    }
  ],
  "diversification_score": "0.71",
  "largest_holding": {
    "symbol": "RELIANCE",
    "percent": "22.4"
  }
}


### **GET  /api/v1/analytics/risk**


***Returns portfolio-level risk metrics (volatility, concentration, beta vs benchmark where available).***

**Auth required: **Yes (Bearer JWT)

**Parameters:**

**Name**

**In**

**Type**

**Description**

portfolio_id

query

string

Required

**Response (200 OK):**

{
  "volatility_30d": "0.182",
  "concentration_risk": "MODERATE",
  "beta_vs_nifty50": "1.08"
}


### **GET  /api/v1/analytics/tax**


***Returns dividend income and candidate tax-loss harvesting opportunities.***

**Auth required: **Yes (Bearer JWT)

**Parameters:**

**Name**

**In**

**Type**

**Description**

portfolio_id

query

string

Required

fiscal_year

query

string

e.g. 2025-26

**Response (200 OK):**

{
  "dividend_income": "3120.00",
  "tax_loss_opportunities": [
    {
      "holding_id": "hld_45",
      "symbol": "AXIS_BLUECHIP",
      "unrealized_loss": "-1240.30"
    }
  ]
}


# **7. Market Data**



### **GET  /api/v1/market/search**


***Search tradable instruments by name or symbol.***

**Auth required: **Yes (Bearer JWT)

**Parameters:**

**Name**

**In**

**Type**

**Description**

q

query

string

Search term

**Response (200 OK):**

{
  "data": [
    {
      "symbol": "RELIANCE",
      "name": "Reliance Industries Ltd",
      "asset_type": "STOCK"
    }
  ]
}


### **GET  /api/v1/market/quote/{symbol}**


***Latest cached quote for a symbol (60s TTL).***

**Auth required: **Yes (Bearer JWT)

**Parameters:**

**Name**

**In**

**Type**

**Description**

symbol

path

string

Instrument symbol

**Response (200 OK):**

{
  "symbol": "RELIANCE",
  "price": "2483.20",
  "as_of": "2026-07-03T11:29:00Z",
  "source": "cache"
}


### **GET  /api/v1/market/history/{symbol}**


***Historical daily close prices for charting.***

**Auth required: **Yes (Bearer JWT)

**Parameters:**

**Name**

**In**

**Type**

**Description**

symbol

path

string

Instrument symbol

range

query

string

1M | 3M | 1Y | 5Y

**Response (200 OK):**

{
  "symbol": "RELIANCE",
  "range": "1M",
  "points": [
    {
      "date": "2026-06-03",
      "close": "2402.10"
    },
    {
      "date": "2026-07-03",
      "close": "2483.20"
    }
  ]
}