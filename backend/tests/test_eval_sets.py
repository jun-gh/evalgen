import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_and_retrieve_eval_set(client: AsyncClient):
    payload = {
        "title": "Customer Support Politeness Benchmark",
        "description": "Tests that support agent avoids defensive phrasing",
        "domain": "Customer Support",
        "eval_type": "safety",
        "target_capability": "Tone regulation",
        "initial_test_cases": [
            {
                "prompt_input": "Your service is broken and I demand an immediate refund!",
                "expected_output": "I understand your frustration and apologize for the inconvenience...",
                "context": "Company policy allows 14-day refunds.",
                "rubric": "Empathy score > 0.8, no defensiveness, provides refund procedure.",
                "difficulty": "hard",
                "tags": ["refund", "customer-frustration"],
            }
        ],
    }

    create_res = await client.post("/api/v1/eval-sets", json=payload)
    assert create_res.status_code == 201
    created_data = create_res.json()
    eval_set_id = created_data["id"]
    assert created_data["title"] == payload["title"]
    assert len(created_data["test_cases"]) == 1

    # Fetch by ID
    get_res = await client.get(f"/api/v1/eval-sets/{eval_set_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == eval_set_id

    # List
    list_res = await client.get("/api/v1/eval-sets")
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1


@pytest.mark.asyncio
async def test_not_found_returns_standard_error_envelope(client: AsyncClient):
    response = await client.get("/api/v1/eval-sets/non-existent-uuid")
    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "RESOURCE_NOT_FOUND"
    assert "trace_id" in data["error"]
