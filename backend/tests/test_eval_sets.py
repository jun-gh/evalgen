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


@pytest.mark.asyncio
async def test_export_csv_with_session_and_query_param(client: AsyncClient):
    session_id = "test-session-csv-123"
    headers = {"X-Session-ID": session_id}
    payload = {
        "title": "Export Test Suite",
        "description": "Suite for CSV export verification",
        "domain": "Coding",
        "eval_type": "rag_qa",
        "target_capability": "Code synthesis",
        "initial_test_cases": [
            {
                "prompt_input": "Write a python fibonacci function",
                "expected_output": "def fib(n): return n if n <= 1 else fib(n-1) + fib(n-2)",
                "context": "",
                "rubric": "Correctness",
                "difficulty": "easy",
                "tags": ["python", "math"],
            }
        ],
    }

    create_res = await client.post("/api/v1/eval-sets", json=payload, headers=headers)
    assert create_res.status_code == 201
    eval_set_id = create_res.json()["id"]

    # 1. Export with X-Session-ID header
    csv_header_res = await client.get(f"/api/v1/eval-sets/{eval_set_id}/export/csv", headers=headers)
    assert csv_header_res.status_code == 200
    assert "text/csv" in csv_header_res.headers["content-type"]
    assert "Prompt Input" in csv_header_res.text
    assert "Write a python fibonacci function" in csv_header_res.text

    # 2. Export with ?session_id= query param (simulating browser download)
    csv_query_res = await client.get(f"/api/v1/eval-sets/{eval_set_id}/export/csv?session_id={session_id}")
    assert csv_query_res.status_code == 200
    assert "Write a python fibonacci function" in csv_query_res.text

    # 3. Export by direct UUID lookup (fallback)
    csv_anon_res = await client.get(f"/api/v1/eval-sets/{eval_set_id}/export/csv")
    assert csv_anon_res.status_code == 200
    assert "Write a python fibonacci function" in csv_anon_res.text


@pytest.mark.asyncio
async def test_delete_eval_set_with_test_cases(client: AsyncClient):
    session_id = "test-session-delete-123"
    headers = {"X-Session-ID": session_id}
    payload = {
        "title": "Dataset To Delete",
        "description": "Suite for deletion verification",
        "domain": "General QA",
        "eval_type": "rag_qa",
        "initial_test_cases": [
            {
                "prompt_input": "Delete me",
                "expected_output": "Ok",
                "difficulty": "easy",
                "tags": ["temp"],
            }
        ],
    }

    create_res = await client.post("/api/v1/eval-sets", json=payload, headers=headers)
    assert create_res.status_code == 201
    eval_set_id = create_res.json()["id"]

    # Delete
    del_res = await client.delete(f"/api/v1/eval-sets/{eval_set_id}", headers=headers)
    assert del_res.status_code == 204

    # Verify gone
    get_res = await client.get(f"/api/v1/eval-sets/{eval_set_id}", headers=headers)
    assert get_res.status_code == 404


@pytest.mark.asyncio
async def test_delete_eval_set_with_benchmark_runs(client: AsyncClient):
    from unittest.mock import patch

    session_id = "test-session-delete-runs-123"
    headers = {"X-Session-ID": session_id}
    payload = {
        "title": "Dataset With Runs To Delete",
        "domain": "General QA",
        "eval_type": "rag_qa",
        "initial_test_cases": [
            {
                "prompt_input": "Test input",
                "expected_output": "Test output",
                "difficulty": "easy",
            }
        ],
    }

    create_res = await client.post("/api/v1/eval-sets", json=payload, headers=headers)
    assert create_res.status_code == 201
    eval_set_id = create_res.json()["id"]

    # Run benchmark to generate EvalRun and EvaluationResult records
    async def mock_resp(*args, **kwargs):
        return '{"score": 1.0, "passed": true, "feedback": "good"}'

    with patch("app.services.evaluator.gemini_service.generate_response", side_effect=mock_resp):
        run_res = await client.post(
            f"/api/v1/eval-sets/{eval_set_id}/run",
            json={"system_prompt": "test"},
            headers=headers,
        )
        assert run_res.status_code == 200

    # Now attempt to delete the eval set
    del_res = await client.delete(f"/api/v1/eval-sets/{eval_set_id}", headers=headers)
    assert del_res.status_code == 204


