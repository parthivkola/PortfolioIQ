"""Integration tests for portfolio CRUD operations."""

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
class TestPortfolioCRUD:
    async def test_create_and_list(self, client):
        # Register and get token
        resp = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "portfolio@example.com",
                "password": "securepass123",
                "full_name": "Portfolio User",
            },
        )
        token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Create portfolio
        resp = await client.post(
            "/api/v1/portfolio",
            json={"name": "My Investments"},
            headers=headers,
        )
        assert resp.status_code == 201
        portfolio_id = resp.json()["id"]

        # List portfolios
        resp = await client.get("/api/v1/portfolio", headers=headers)
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

        # Update
        resp = await client.put(
            f"/api/v1/portfolio/{portfolio_id}",
            json={"name": "Renamed Portfolio"},
            headers=headers,
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "Renamed Portfolio"
