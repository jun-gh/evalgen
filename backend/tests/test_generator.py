import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_synthetic_generator_endpoint(client: AsyncClient):
    payload = {
        "title": "Python Async Concurrency Test Suite",
        "prompt_scenario": "Test an AI coding assistant on correctly using asyncio.gather with return_exceptions=True",
        "domain": "Coding",
        "eval_type": "reasoning",
        "num_samples": 3,
        "include_adversarial": True,
        "auto_save": True,
    }

    response = await client.post("/api/v1/generator/generate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "dataset" in data
    assert len(data["dataset"]["test_cases"]) == 3
    assert data["eval_set_id"] is not None

    # Verify that the auto-saved eval set is queryable from the database
    get_res = await client.get(f"/api/v1/eval-sets/{data['eval_set_id']}")
    assert get_res.status_code == 200
    assert len(get_res.json()["test_cases"]) == 3
