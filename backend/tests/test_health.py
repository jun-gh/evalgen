import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check_returns_healthy(client: AsyncClient):
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["app"] == "EvalGen"
    assert "gemini_model" in data
    assert "database_status" in data
    assert "timestamp" in data
    assert "X-Trace-ID" in response.headers


@pytest.mark.asyncio
async def test_config_endpoint_returns_model(client: AsyncClient):
    response = await client.get("/api/v1/config")
    assert response.status_code == 200
    data = response.json()
    assert "gemini_model" in data
    assert data["app_name"] == "EvalGen"
