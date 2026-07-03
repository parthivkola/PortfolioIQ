**PORTFOLIO INTELLIGENCE PLATFORM**

**Database Schema & ER Diagram**

*Relational schema, constraints, indexing strategy, and entity relationships*

**Version:  **1.0

**Author:  **Kola

**Database Engine:  **PostgreSQL 16

**Migration Tool:  **Alembic


# **1. Entity-Relationship Diagram**


***Solid lines denote enforced foreign-key relationships. The dashed line from MarketSnapshot to Holdings is a logical join on symbol, not an enforced FK, since market data is asset-level rather than holding-level.***


# **2. Table Definitions**



## **Users**


***Stores account credentials and profile data.***

**Column**

**Type**

**Constraints**

**Description**

id

UUID

PK, default gen_random_uuid()

Primary key

email

VARCHAR(255)

UNIQUE, NOT NULL

Login identifier

password_hash

VARCHAR(255)

NOT NULL

BCrypt hash

full_name

VARCHAR(120)

NOT NULL

Display name

created_at

TIMESTAMPTZ

NOT NULL, default now()

Account creation time

**Indexes:**

- UNIQUE INDEX ux_users_email ON users(email)


## **Portfolio**


***A named collection of holdings owned by one user.***

**Column**

**Type**

**Constraints**

**Description**

id

UUID

PK, default gen_random_uuid()

Primary key

user_id

UUID

FK -> users.id, NOT NULL

Owning user

name

VARCHAR(120)

NOT NULL

Portfolio display name

created_at

TIMESTAMPTZ

NOT NULL, default now()

Creation time

**Indexes:**

- INDEX ix_portfolio_user_id ON portfolio(user_id)


## **Holdings**


***A specific asset position within a portfolio.***

**Column**

**Type**

**Constraints**

**Description**

id

UUID

PK, default gen_random_uuid()

Primary key

portfolio_id

UUID

FK -> portfolio.id, NOT NULL

Owning portfolio

asset_type

ENUM

NOT NULL

STOCK | ETF | MUTUAL_FUND | CRYPTO | BOND

symbol

VARCHAR(40)

NOT NULL

Instrument identifier

quantity

NUMERIC(20,6)

NOT NULL, >= 0

Units held

average_buy_price

NUMERIC(20,4)

NOT NULL, >= 0

Weighted average cost

**Indexes:**

- INDEX ix_holdings_portfolio_id ON holdings(portfolio_id)

- UNIQUE INDEX ux_holdings_portfolio_symbol ON holdings(portfolio_id, symbol)


## **Transactions**


***An immutable ledger entry that mutates a holding's quantity/cost basis.***

**Column**

**Type**

**Constraints**

**Description**

id

UUID

PK, default gen_random_uuid()

Primary key

holding_id

UUID

FK -> holdings.id, NOT NULL

Affected holding

transaction_type

ENUM

NOT NULL

BUY | SELL | DIVIDEND | BONUS | SPLIT

quantity

NUMERIC(20,6)

NOT NULL

Units transacted

price

NUMERIC(20,4)

NOT NULL, >= 0

Price per unit at execution

timestamp

TIMESTAMPTZ

NOT NULL

Execution time

**Indexes:**

- INDEX ix_transactions_holding_id ON transactions(holding_id)

- INDEX ix_transactions_timestamp ON transactions(timestamp DESC)


## **MarketSnapshot**


***Point-in-time price observations, sourced from the market data provider and cache-warmed into Postgres for history queries.***

**Column**

**Type**

**Constraints**

**Description**

id

UUID

PK, default gen_random_uuid()

Primary key

symbol

VARCHAR(40)

NOT NULL

Instrument identifier

market_price

NUMERIC(20,4)

NOT NULL

Observed price

timestamp

TIMESTAMPTZ

NOT NULL

Observation time

**Indexes:**

- UNIQUE INDEX ux_marketsnapshot_symbol_ts ON marketsnapshot(symbol, timestamp)


## **PortfolioSnapshot**


***Daily (or on-demand) rollup of portfolio value used for history charts and XIRR cash-flow reconstruction.***

**Column**

**Type**

**Constraints**

**Description**

id

UUID

PK, default gen_random_uuid()

Primary key

portfolio_id

UUID

FK -> portfolio.id, NOT NULL

Owning portfolio

portfolio_value

NUMERIC(20,4)

NOT NULL

Market value at snapshot time

invested_value

NUMERIC(20,4)

NOT NULL

Net capital invested

pnl

NUMERIC(20,4)

NOT NULL

portfolio_value - invested_value

created_at

TIMESTAMPTZ

NOT NULL, default now()

Snapshot time

**Indexes:**

- INDEX ix_portfoliosnapshot_portfolio_id ON portfoliosnapshot(portfolio_id, created_at DESC)


# **3. Relationships**


**Parent**

**Child**

**Cardinality**

**On Delete**

users

portfolio

1 : N

CASCADE

portfolio

holdings

1 : N

CASCADE

holdings

transactions

1 : N

CASCADE

portfolio

portfoliosnapshot

1 : N

CASCADE

marketsnapshot

holdings

N : 1 (logical, via symbol)

N/A — not FK-enforced


# **4. Design Notes**


- All monetary and quantity columns use NUMERIC rather than FLOAT to avoid rounding drift in financial calculations (critical for XIRR/CAGR accuracy).

- Transactions are append-only; corrections are made by inserting a compensating transaction rather than mutating history, preserving audit integrity.

- Holdings.quantity and average_buy_price are derived/cached fields recomputed from the Transactions ledger by the Portfolio Service — the ledger is the source of truth.

- PortfolioSnapshot rows double as the irregular cash-flow series consumed by the XIRR Newton-Raphson solver.

- asset_type and transaction_type are implemented as native PostgreSQL ENUM types for storage efficiency and query-time validation.

- All tables use UUID primary keys (gen_random_uuid()) to avoid sequential-ID enumeration and simplify future horizontal partitioning.


# **5. Migration Strategy**


***Alembic manages versioned migrations. Each schema change ships as a paired upgrade()/downgrade() revision, applied automatically in the CI/CD pipeline's deploy step prior to rolling out new application containers.***

alembic revision --autogenerate -m "add portfoliosnapshot table"
alembic upgrade head