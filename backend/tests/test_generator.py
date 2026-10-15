import pytest
from unittest.mock import patch
from httpx import AsyncClient
from app.schemas.generation import SyntheticGenerationResult, GeneratedTestCase


@pytest.mark.asyncio
async def test_synthetic_generator_endpoint(client: AsyncClient):
    mock_dataset = SyntheticGenerationResult(
        title="Python Async Concurrency Test Suite",
        description="Test an AI coding assistant on asyncio concurrency",
        domain="Coding",
        eval_type="reasoning",
        target_capability="Python async reasoning",
        test_cases=[
            GeneratedTestCase(
                prompt_input=f"Async test prompt {i + 1}",
                expected_output=f"Expected golden answer {i + 1}",
                context=None,
                rubric="Factual correctness and exception handling",
                difficulty="medium",
                tags=["coding", "async", "concurrency"],
            )
            for i in range(3)
        ],
    )

    with patch("app.api.v1.endpoints.generator.gemini_service.generate_eval_set", return_value=(mock_dataset, 0)):
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
