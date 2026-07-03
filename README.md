# Portfolio Intelligence Platform (PIP)

A modern, light-themed Single Page Application (SPA) dashboard for tracking portfolio analytics and metrics including CAGR, XIRR, and asset allocation, backed by a FastAPI backend, PostgreSQL, and Redis caching.

---

## Architecture Overview

- **Backend**: FastAPI (Python 3.12/3.14) with async SQLAlchemy + asyncpg
- **Database**: PostgreSQL (port 5433 locally) for transaction ledger and portfolio states
- **Caching & Rate Limiting**: Redis (port 6379 locally)
- **Migrations**: Alembic
- **Market Data**: Yahoo Finance scraper/simulation with caching (APScheduler background workers sync prices every minute)
- **Frontend**: Single Page Application (SPA) built with vanilla JS and CSS, using a responsive light mode design with toast feedback, interactive allocation charts, and live symbol popup quotes.

---

## Local Development Setup

### 1. Prerequisites
Make sure you have `uv` installed (Python package installer and manager):
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Local Environment Setup
Sync dependencies:
```bash
uv sync
```

### 3. Run Postgres & Redis
Use Docker Compose to launch database and cache containers:
```bash
docker compose up -d
```

### 4. Run Migrations
Run the Alembic migration scripts to build the database schema:
```bash
uv run alembic upgrade head
```

### 5. Run the Application
Start the FastAPI development server:
```bash
uv run uvicorn app.main:app --reload
```
Open `http://localhost:8000` in your browser.

---

## Running with Docker (Local Testing)

To run the entire application inside a Docker container while referencing your local Postgres/Redis databases:

1. **Build the image**:
   ```bash
   docker build -t portfolio-iq .
   ```

2. **Run the container**:
   ```bash
   docker run --rm \
     --add-host host.docker.internal:host-gateway \
     -e DATABASE_URL="postgresql+asyncpg://pip_user:pip_password@host.docker.internal:5433/portfolio_intelligence" \
     -e REDIS_URL="redis://host.docker.internal:6379/0" \
     -p 8001:8000 \
     portfolio-iq
   ```
   Open `http://localhost:8001` in your browser.

---

## Production Deployment (Render)

This project is optimized for deployment on [Render](https://render.com) using Infrastructure-as-Code via the provided `render.yaml` file.

### One-Click Blueprint Deploy
1. Push this repository to your GitHub account.
2. Go to **Render Dashboard** -> **Blueprints** -> **New Blueprint Instance**.
3. Select your repository.
4. Render will read the `render.yaml` file and automatically spin up:
   - **PostgreSQL Database** (Free tier)
   - **Redis Cache Store** (Free tier)
   - **Web Service** (Docker container, runs database migrations automatically at startup, respects `$PORT`)
5. Click **Apply**. Render will handle setting up and connecting all services safely.

---

## Key Financial Calculations & Constraints

### CAGR (Compound Annual Growth Rate)
$$\text{CAGR} = \left(\frac{\text{Ending Value}}{\text{Beginning Value}}\right)^{\frac{1}{\text{Years}}} - 1$$
- **Constraint**: Requires $\text{days elapsed} \ge 1$. On the day of purchase (day 0), the time fraction is zero, making the exponent $\frac{1}{0}$ mathematically undefined. CAGR will render as `--` until at least 1 calendar day passes.

### XIRR (Extended Internal Rate of Return)
Solves for interest rate $r$ where:
$$\sum_{i=1}^{N} \frac{CF_i}{(1 + r)^{t_i}} = 0$$
- **Constraint**: Requires $\text{days elapsed} \ge 1$ from the first transaction. If all buy/sell transactions and the current portfolio valuation fall on the exact same calendar day, all time fractions $t_i$ equal zero. This removes the variable $r$ entirely from the equation ($\sum CF_i = 0$), making it impossible to solve. XIRR will display as `--` until at least 1 calendar day has elapsed.
