import pytest
from httpx import AsyncClient
from app.config import settings


@pytest.mark.asyncio
async def test_config_endpoint_returns_session_quotas(client: AsyncClient):
    res = await client.get("/api/v1/config")
    assert res.status_code == 200
    data = res.json()
    assert data["max_datasets_per_session"] == settings.MAX_DATASETS_PER_SESSION
    assert data["session_expiry_days"] == settings.SESSION_EXPIRY_DAYS
    assert data["max_sample_count"] == settings.MAX_SAMPLE_COUNT
    assert data["default_sample_count"] == settings.DEFAULT_SAMPLE_COUNT


@pytest.mark.asyncio
async def test_session_isolation(client: AsyncClient):
    session_a = "user-session-aaa-111"
    session_b = "user-session-bbb-222"

    payload = {
        "title": "Session A Exclusive Dataset",
        "domain": "Customer Support",
        "eval_type": "rag_qa",
        "initial_test_cases": [
            {
                "prompt_input": "Hello",
                "expected_output": "Hi there",
                "rubric": "Friendly greeting",
            }
        ],
    }

    # Session A creates a dataset
    res_a = await client.post(
        "/api/v1/eval-sets",
        json=payload,
        headers={"X-Session-ID": session_a},
    )
    assert res_a.status_code == 201
    dataset_a_id = res_a.json()["id"]

    # Session A can see it
    list_a = await client.get(
        "/api/v1/eval-sets",
        headers={"X-Session-ID": session_a},
    )
    assert list_a.status_code == 200
    ids_a = [d["id"] for d in list_a.json()]
    assert dataset_a_id in ids_a

    # Session B CANNOT see it in list
    list_b = await client.get(
        "/api/v1/eval-sets",
        headers={"X-Session-ID": session_b},
    )
    assert list_b.status_code == 200
    ids_b = [d["id"] for d in list_b.json()]
    assert dataset_a_id not in ids_b

    # Session B CANNOT access Session A's dataset directly (404)
    get_b = await client.get(
        f"/api/v1/eval-sets/{dataset_a_id}",
        headers={"X-Session-ID": session_b},
    )
    assert get_b.status_code == 404

    # Session B CANNOT delete Session A's dataset (404)
    del_b = await client.delete(
        f"/api/v1/eval-sets/{dataset_a_id}",
        headers={"X-Session-ID": session_b},
    )
    assert del_b.status_code == 404


@pytest.mark.asyncio
async def test_session_dataset_quota_enforcement(client: AsyncClient):
    session_id = "quota-test-session-999"

    # Create up to MAX_DATASETS_PER_SESSION
    created_ids = []
    for i in range(settings.MAX_DATASETS_PER_SESSION):
        payload = {
            "title": f"Quota Test Dataset {i + 1}",
            "domain": "Finance",
            "eval_type": "reasoning",
            "initial_test_cases": [
                {
                    "prompt_input": f"Q{i}",
                    "expected_output": f"A{i}",
                    "rubric": "Correct",
                }
            ],
        }
        res = await client.post(
            "/api/v1/eval-sets",
            json=payload,
            headers={"X-Session-ID": session_id},
        )
        assert res.status_code == 201
        created_ids.append(res.json()["id"])

    # Attempt to create (MAX + 1)-th dataset should fail with 400 QUOTA_EXCEEDED
    extra_payload = {
        "title": "Overflow Dataset",
        "domain": "Finance",
        "eval_type": "reasoning",
        "initial_test_cases": [],
    }
    overflow_res = await client.post(
        "/api/v1/eval-sets",
        json=extra_payload,
        headers={"X-Session-ID": session_id},
    )
    assert overflow_res.status_code == 400
    err_data = overflow_res.json()
    assert err_data["error"]["code"] == "QUOTA_EXCEEDED"
    assert "Session limit reached" in err_data["error"]["message"]

    # Delete one dataset
    del_res = await client.delete(
        f"/api/v1/eval-sets/{created_ids[0]}",
        headers={"X-Session-ID": session_id},
    )
    assert del_res.status_code == 204

    # Now creating a dataset succeeds again
    retry_res = await client.post(
        "/api/v1/eval-sets",
        json=extra_payload,
        headers={"X-Session-ID": session_id},
    )
    assert retry_res.status_code == 201


@pytest.mark.asyncio
async def test_sample_count_validation(client: AsyncClient):
    payload = {
        "title": "Too Many Samples",
        "prompt_scenario": "Testing sample count boundary",
        "num_samples": settings.MAX_SAMPLE_COUNT + 10,
        "auto_save": False,
    }
    res = await client.post("/api/v1/generator/generate", json=payload)
    assert res.status_code == 422
