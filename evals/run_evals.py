import csv
import json
import os
import sys
from pathlib import Path
from tabulate import tabulate

# 1. Automatically load configuration from backend/.env if not already set in environment
def load_backend_env():
    env_path = Path(__file__).resolve().parent.parent / "backend" / ".env"
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    k = k.strip()
                    v = v.strip().strip('"').strip("'")
                    if k not in os.environ and v:
                        os.environ[k] = v

load_backend_env()

GEMINI_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.8-flash")
HAS_GEMINI = bool(GEMINI_KEY and GEMINI_KEY not in ("", "your_gemini_api_key_here", "dummy", "test"))

if HAS_GEMINI:
    from google import genai
    from google.genai import types
    client = genai.Client(api_key=GEMINI_KEY)
    print(f"✨ Using live Google Gemini ({GEMINI_MODEL}) for evaluation.")
else:
    print("ℹ️  GEMINI_API_KEY not configured in backend/.env. Running simulated evaluation.")


# 2. The Application Under Test (Replace with your actual agent/LLM function)
def your_ai_application(prompt: str, context: str = "") -> str:
    """Simulates or calls your actual AI application/prompt under test."""
    if HAS_GEMINI:
        import time
        for attempt in range(3):
            try:
                resp = client.models.generate_content(
                    model=GEMINI_MODEL,
                    contents=f"Context: {context}\n\nUser Question: {prompt}\nAnswer concisely:",
                )
                if resp and resp.text:
                    return resp.text.strip()
                return f"[No text in response for: {prompt[:30]}...]"
            except Exception as exc:
                if attempt < 2 and any(term in str(exc).lower() for term in ["429", "quota", "rate limit", "timeout", "connection"]):
                    time.sleep(2 ** (attempt + 1))
                    continue
                print(f"\n⚠️  Gemini API error during generation ({type(exc).__name__}): {exc}")
                return f"Simulated fallback response due to API error ({type(exc).__name__})."
    else:
        # Mock responses for offline testing
        return f"Standard response adhering to policy: {prompt[:40]}..."


# 3. LLM-as-a-Judge Evaluation Engine
def evaluate_test_case(prompt: str, expected: str, actual: str, rubric: str) -> dict:
    """Grades the candidate output against the golden answer and rubric."""
    if HAS_GEMINI:
        import time
        judge_prompt = f"""
You are an impartial, strict AI Evaluation Judge.
Grade the Candidate Output against the Reference Golden Answer and Rubric.

User Prompt: {prompt}
Reference Golden Answer: {expected}
Candidate Output: {actual}
Grading Rubric:
{rubric}

Return ONLY valid JSON matching this schema:
{{
  "score": <float between 0.0 and 1.0>,
  "passed": <boolean: true if score >= 0.7 else false>,
  "critique": "<one-sentence justification of score>"
}}
"""
        for attempt in range(3):
            try:
                response = client.models.generate_content(
                    model=GEMINI_MODEL,
                    contents=judge_prompt,
                    config=types.GenerateContentConfig(response_mime_type="application/json"),
                )
                raw_text = (response.text or "").strip()
                if raw_text.startswith("```json"):
                    raw_text = raw_text[7:]
                if raw_text.startswith("```"):
                    raw_text = raw_text[3:]
                if raw_text.endswith("```"):
                    raw_text = raw_text[:-3]
                return json.loads(raw_text.strip())
            except Exception as exc:
                if attempt < 2 and any(term in str(exc).lower() for term in ["429", "quota", "rate limit", "timeout", "connection"]):
                    time.sleep(2 ** (attempt + 1))
                    continue
                print(f"\n⚠️  Gemini API error during grading ({type(exc).__name__}): {exc}")
                break

    # Heuristic grading fallback for offline testing or API failure
    norm_exp = expected.strip().lower()
    norm_act = actual.strip().lower()
    match = any(word in norm_act for word in norm_exp.split()[:4])
    score = 0.85 if match else 0.4
    return {
        "score": score,
        "passed": score >= 0.7,
        "critique": "Heuristic match: key terminology found in actual output." if match else "Missing key terms from expected output."
    }


# 4. Main Benchmark Execution Loop
def run_benchmark(csv_path: str):
    path = Path(csv_path)
    if not path.exists():
        print(f"❌ Error: File not found: {csv_path}")
        print("Please provide a valid path to your exported EvalGen CSV file.")
        sys.exit(1)

    print(f"\n🚀 Running Benchmark Suite: {path.name}")
    print("=" * 80)

    results_table = []
    total = 0
    passed = 0

    with open(path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for idx, row in enumerate(reader, 1):
            total += 1
            tc_id = row.get("ID", f"TC-{idx}")[:8]
            prompt = row.get("Prompt Input", "")
            expected = row.get("Expected Output", "")
            context = row.get("Context", "")
            rubric = row.get("Rubric", "Must be accurate and factual.")
            difficulty = row.get("Difficulty", "medium")

            print(f"[{idx}/{total}] Testing: {prompt[:50]}...")

            # 1. Run your AI App
            actual = your_ai_application(prompt, context)

            # 2. Grade with LLM-as-a-judge
            eval_result = evaluate_test_case(prompt, expected, actual, rubric)

            is_pass = eval_result["passed"]
            if is_pass:
                passed += 1

            status_icon = "✅ PASS" if is_pass else "❌ FAIL"
            results_table.append([
                tc_id,
                difficulty.upper(),
                status_icon,
                f"{eval_result['score']:.2f}",
                eval_result["critique"][:45] + ("..." if len(eval_result["critique"]) > 45 else "")
            ])

    print("\n" + "=" * 80)
    print("📊 EVALUATION SCORECARD")
    print("=" * 80)
    print(tabulate(
        results_table,
        headers=["ID", "Tier", "Status", "Score", "Judge Critique"],
        tablefmt="rounded_outline"
    ))

    pass_rate = (passed / total) * 100 if total else 0
    print(f"\n🎯 Overall Pass Rate: {passed}/{total} Passed ({pass_rate:.1f}%)\n")


if __name__ == "__main__":
    csv_file = sys.argv[1] if len(sys.argv) > 1 else "evals/dataset.csv"
    run_benchmark(csv_file)