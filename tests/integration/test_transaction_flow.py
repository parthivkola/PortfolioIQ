"""Integration tests for the transaction flow."""

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.mark.skip(reason="Requires running Postgres and Redis")
class TestTransactionFlow:
    async def test_buy_creates_holding_state(self, client):
        """BUY transaction should update holding quantity and avg price."""
        # Register + create portfolio + create holding + record BUY
        resp = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "txn@example.com",
                "password": "securepass123",
                "full_name": "Txn User",
            },
        )
        token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Create portfolio
        resp = await client.post("/api/v1/portfolio", json={"name": "Test"}, headers=headers)
        portfolio_id = resp.json()["id"]

        # Create holding
        resp = await client.post(
            "/api/v1/holdings",
            json={
                "portfolio_id": portfolio_id,
                "asset_type": "STOCK",
                "symbol": "RELIANCE",
            },
            headers=headers,
        )
        assert resp.status_code == 201
        holding_id = resp.json()["id"]

        # Record BUY
        resp = await client.post(
            "/api/v1/transactions",
            json={
                "holding_id": holding_id,
                "transaction_type": "BUY",
                "quantity": "10",
                "price": "2450.50",
                "timestamp": "2026-07-03T09:15:00Z",
            },
            headers=headers,
        )
        assert resp.status_code == 201

        # Verify holding state
        resp = await client.get(f"/api/v1/holdings?portfolio_id={portfolio_id}", headers=headers)
        holdings = resp.json()
        assert len(holdings) == 1
        assert holdings[0]["quantity"] == "10.000000"
