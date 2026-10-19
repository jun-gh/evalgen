import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_import_csv_and_run_benchmark(client: AsyncClient):
    csv_content = (
        "ID,Prompt Input,Expected Output,Context,Rubric,Difficulty,Tags\n"
        "tc-1,What is the return window?,14 days from delivery.,Standard return policy is 14 days.,100% accuracy,easy,returns\n"
        "tc-2,Do you ship internationally?,No only domestic.,Domestic shipping only.,Accuracy,medium,shipping\n"
    )

    files = {"file": ("acme_returns.csv", csv_content.encode("utf-8"), "text/csv")}
    import_res = await client.post("/api/v1/eval-sets/import-csv", files=files)
    assert import_res.status_code == 201, import_res.text
    dataset = import_res.json()
    assert dataset["title"] == "Imported: Acme Returns"
    assert len(dataset["test_cases"]) == 2
    eval_set_id = dataset["id"]

    # Run benchmark
    run_payload = {
        "system_prompt": "You are a customer support agent. Answer concisely based strictly on provided context.",
    }
    run_res = await client.post(f"/api/v1/eval-sets/{eval_set_id}/run", json=run_payload)
    assert run_res.status_code == 200, run_res.text
    run_data = run_res.json()
    assert run_data["eval_set_id"] == eval_set_id
    assert run_data["status"] == "completed"
    assert run_data["total_count"] == 2
    assert len(run_data["results"]) == 2
    assert "accuracy_rate" in run_data
    run_id = run_data["id"]

    # List runs for eval set
    list_runs_res = await client.get(f"/api/v1/eval-sets/{eval_set_id}/runs")
    assert list_runs_res.status_code == 200
    runs = list_runs_res.json()
    assert len(runs) >= 1
    assert runs[0]["id"] == run_id

    # Get single run detail
    get_run_res = await client.get(f"/api/v1/eval-sets/runs/{run_id}")
    assert get_run_res.status_code == 200
    single_run = get_run_res.json()
    assert single_run["id"] == run_id
    assert len(single_run["results"]) == 2
    assert single_run["results"][0]["prompt_input"] is not None
