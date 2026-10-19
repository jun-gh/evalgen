# EvalGen: AI Evaluation & Benchmarking Studio

**EvalGen** is an open-source, full-stack AI evaluation and benchmarking studio designed for mastering **AI Evals**, synthetic test generation, in-browser and CLI LLM-as-a-judge benchmarking, structured LLM outputs, and **zero-cost cloud-native deployments**.

---

## 1. The Iterative Evals-Driven Development (Prompt TDD) Cycle

AI engineering teams use EvalGen to move away from unscientific **"vibe checks"** (tweaking prompts and hoping nothing broke) to disciplined **Test-Driven Development (TDD) for LLMs**.

```
┌────────────────────────────────────────────────────────┐
│ 1. CREATE GOLDEN BENCHMARK                             │
│    Synthesize 10–20 domain test cases with             │
│    strict rubrics & edge cases, or upload existing CSV.│
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│ 2. DRAFT 1: RUN INITIAL BENCHMARK                      │
│    Input your candidate System Prompt in the browser UI│
│    and click "Run Benchmark".                          │
│    Example Result: 60% Passed (3 Passed / 2 Failed)    │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│ 3. DIAGNOSE THE 40% FAILURES                           │
│    Filter by "Failed" in the interactive dashboard:    │
│    • Compare Candidate Output vs Golden Expected Output│
│    • Read LLM Judge Critique:                          │
│      "Failed because model hallucinated an exception   │
│       to the return policy when pressured."            │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│ 4. TWEAK SYSTEM PROMPT & RE-RUN                        │
│    Add rule: "Never make exceptions to 14-day policy." │
│    Click "Run Benchmark" again.                        │
│    Example Result: 85% or 100% Passed!                 │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│ 5. CONTINUOUS REGRESSION & MODEL COMPARISON            │
│    • Compare model performance across foundation LLMs  │
│    • Run in GitHub Actions CI/CD before PR merges      │
└────────────────────────────────────────────────────────┘
```

### The 4-Step Production Workflow

1. **Golden Test Suite Creation**: Define a domain (*Customer Support, Finance, Coding, Healthcare, Tool Calling, Reasoning*) and let Gemini synthesize diverse happy-path, edge-case, and adversarial prompts with golden outputs and grading rubrics.
2. **Initial Baseline Run**: Navigate to the **Benchmark Studio** (`/benchmark`). Enter your application's current system prompt and run the test suite. Receive an objective accuracy baseline (e.g. 60% pass rate).
3. **Root-Cause Critique Inspection**: Expand failed cases to view side-by-side output comparisons and read why the LLM Judge penalized the response.
4. **Prompt Hardening & Verification**: Update your system instructions to patch the failure mode and re-benchmark. Watch your score increase with quantifiable proof.

---

## 2. System Architecture

```
                    +-------------------------------------------------+
                    |       Cloudflare Pages (Vue 3 + Vite SPA)       |
                    |  - 3-Attempt Retry Interceptor                  |
                    |  - Render Cold-Start Wakeup Banner              |
                    |  - Reactive Error Toast & Diagnostic Trace IDs  |
                    +------------------------+------------------------+
                                             |
                                 HTTPS REST  |  JSON Payload
                                             v
                    +-------------------------------------------------+
                    |       Render Web Service (FastAPI + Uvicorn)    |
                    |  - Scale-to-Zero Free Tier                      |
                    |  - Tenacity 3-Attempt Exponential Backoff       |
                    |  - Standardized ErrorEnvelope Handler           |
                    +------------+--------------------+---------------+
                                 |                    |
           +---------------------+                    +-----------------------+
           |                                                                  |
           v                                                                  v
+---------------------+                                            +---------------------+
|  Google Gemini API  |                                            | Storage & State     |
|  - Gemini 2.5 Flash |                                            | - Dev: SQLite Async |
|  - JSON Schema Mode |                                            | - Prod: Neon Server |
|  - Few-shot Synthes |                                            |   less PostgreSQL   |
+---------------------+                                            +---------------------+
           ^
           | Tool Calling & Grounding
+---------------------+
|  Model Context      |
|  Protocol (MCP)     |
|  - Schema Validator |
|  - Fuzzy Scorer     |
+---------------------+
```

---

## 3. Tech Stack & Zero-Cost Cloud Strategy

| Component | Technology | Zero-Cost Deployment Rationale |
| :--- | :--- | :--- |
| **Backend API** | Python 3.11+, FastAPI, Pydantic v2 | High concurrency, native async, strict validation. |
| **Local Storage** | SQLite (`aiosqlite`) | Zero-setup, instant local development file storage. |
| **Production DB** | Neon Serverless Postgres (`asyncpg`) | True scale-to-zero serverless PostgreSQL with instant branching. |
| **AI Layer** | Google Gemini API (`google-genai`) | Low latency, generous free-tier quotas, structured JSON outputs. |
| **Tool Protocol** | Model Context Protocol (`mcp`) | Standardized tool context retrieval and validation. |
| **Frontend SPA** | Vue 3 (Composition API), Vite, Tailwind CSS, Pinia | Lightning-fast HMR, lightweight bundle. |
| **Backend Host** | Render Free Tier Web Service (`render.yaml`) | Zero-cost container hosting configured for **scale-to-zero**. |
| **Frontend Host** | Cloudflare Pages | Unlimited bandwidth, global edge CDN, zero-cost static hosting. |
| **Registry** | GitHub Container Registry (`ghcr.io`) | Free container image hosting tightly coupled to GitHub Actions. |
| **CI/CD** | GitHub Actions | Automated PR linting, pytest, typecheck, and zero-downtime deploy triggers. |

---

## 4. Session-Based Dataset Isolation & Runtime Quotas (Zero Login)

EvalGen provides frictionless **anonymous session scoping** without requiring user registration or login:
- **Zero-Login Workspace**: Every visitor receives a persistent session token (`X-Session-ID` attached automatically via Axios request interceptors and stored in browser `localStorage`).
- **Complete Privacy**: Visitors only view, test, and benchmark datasets generated or imported during their own active session. Other sessions' datasets remain strictly isolated (`HTTP 404`).
- **Automatic Schema Migration**: The backend startup lifecycle (`init_db`) automatically checks database schemas and provisions the `session_id` column on SQLite and PostgreSQL without manual SQL scripts or downtime.

### Runtime Environment Limits & Quotas
All session quotas and sample bounds are governed dynamically via environment variables in `backend/.env` (or Render's Environment dashboard) and broadcast via `GET /api/v1/config`:

| Environment Variable | Default | Purpose & Dynamic UI Behavior |
| :--- | :--- | :--- |
| `MAX_DATASETS_PER_SESSION` | `5` | Maximum active datasets allowed per session. Reaching this limit displays a warning badge and halts auto-saving until an older set is removed. |
| `SESSION_EXPIRY_DAYS` | `7` | Lifespan of session datasets (1 week). Queries automatically enforce a rolling cutoff (`created_at >= now - expiry_days`). |
| `MAX_SAMPLE_COUNT` | `10` | Upper ceiling for the test generation slider. Validated both client-side and server-side via Pydantic validators. |
| `DEFAULT_SAMPLE_COUNT` | `3` | Initial default test case count populated on the generator form. |

> [!TIP]
> **Zero Git Commits / Zero Frontend Redeploys**: Updating any of these environment variables on your backend host (Render) immediately updates frontend sliders, bounds, and backend enforcement upon container reboot—**no frontend rebuild or git commit is required**.

---

## 5. Error Handling & Resilience Best Practices

### 5.1 Maximum 3-Attempt Exponential Backoff
All transient external interactions (LLM generation, rate limits, network resets) strictly enforce a **maximum retry limit of 3**:
- **Backend**: Decorated with `tenacity` exponential backoff with jitter (`1s`, `2s`, `4s` + jitter). If all 3 attempts fail, a typed `RateLimitExceededException` or `LLMGenerationException` is raised.
- **Frontend**: Axios interceptors automatically retry idempotent requests up to 3 times before displaying actionable failure cards.

### 5.2 Displaying Errors to the UI for Best UX
- **Standardized Error Envelope**: All API errors return a consistent JSON schema:
  ```json
  {
    "success": false,
    "error": {
      "code": "RATE_LIMIT_EXCEEDED",
      "message": "Gemini API rate limit reached. 3 automated retries exhausted.",
      "trace_id": "req-8fa1b439cd",
      "retryable": true,
      "retry_count": 3,
      "timestamp": "2026-10-15T14:00:00Z"
    }
  }
  ```
- **Render Cold-Start Wakeup Banner**: Because Render free tier sleeps on inactivity, the frontend displays an animated, friendly banner: *"Render's zero-cost tier scales to zero when idle. Your first request is waking the server up (~30-45s)..."*
- **Reactive Toast Stack**: User receives non-blocking toasts displaying the exact error message, correlation `trace_id`, and a one-click **"Retry Request"** button.

---

## 6. Repository Structure

```
evalgen/
├── backend/
│   ├── app/
│   │   ├── api/v1/endpoints/       # Health, EvalSets, Generator, MCP tools
│   │   ├── core/                   # Database (SQLite/Neon), Exceptions, 3-Retry logic
│   │   ├── models/                 # SQLAlchemy 2.0 ORM models
│   │   ├── schemas/                # Pydantic v2 validation models & ErrorEnvelope
│   │   ├── services/               # Gemini API client, MCP manager, Evaluator
│   │   ├── config.py               # Settings and environment overrides
│   │   └── main.py                 # FastAPI lifespan, CORS, and request tracing
│   ├── tests/                      # Pytest suite (health, max-3 retries, eval sets)
│   ├── Dockerfile                  # Multi-stage production container
│   ├── pyproject.toml              # Dependencies & tool configurations
│   ├── requirements.txt            # Locked requirements
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/common/      # Navbar, ErrorToast, ServerWakeupBanner
│   │   ├── components/evals/       # TestCaseTable, Rubrics, Assertions
│   │   ├── services/               # Axios API client with 3-retry interceptor
│   │   ├── stores/                 # Pinia stores (evalStore, uiStore)
│   │   ├── views/                  # DashboardView, GeneratorView, EvalDetailView
│   │   ├── App.vue
│   │   └── main.ts
│   ├── index.html
│   ├── package.json
│   ├── vite.config.ts
│   └── tailwind.config.js
├── .github/workflows/
│   ├── ci.yml                      # Unified Backend (Ruff+Pytest) & Frontend (Vite) CI
│   └── deploy-backend.yml          # Build Docker, push to GHCR, deploy to Render
├── render.yaml                     # Render Blueprint (Infrastructure as Code)
├── .gitignore
└── README.md
```

---

## 7. Local Development Quickstart

### Prerequisites
- Python 3.11+
- Node.js 20+ and npm

### 7.1 Backend Setup
```bash
cd backend

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and insert your GEMINI_API_KEY (optional for mock mode)

# Run migrations / start server
uvicorn app.main:app --reload --port 8000
```
API Documentation will be available local at [http://localhost:8000/docs](http://localhost:8000/docs).
API is now live at **https://evalgen-backend.onrender.com/api/v1**  
Interactive docs: **https://evalgen-backend.onrender.com/docs**

### 7.2 Frontend Setup
```bash
cd frontend

# Install all dependencies
npm install

# Start Vite development server
npm run dev
```
Open [http://localhost:5173](http://localhost:5173) in your browser.
Frontend is now live at **https://evalgen.jmco.workers.dev**

---

## 8. Running Tests

```bash
cd backend
source .venv/bin/activate
pytest tests -v
```

Tests include verification of synthetic test generation, benchmark execution, CSV import, and the **maximum 3 retries** resilience.

---

## 9. Running Benchmarks (In-Browser Studio & CLI)

EvalGen supports two ways to benchmark your prompts and LLM applications against golden test suites:

### Option A: In-Browser Benchmark Studio (Interactive Web UI)
1. Navigate to **Run Benchmark** (`/benchmark`) in the top navigation bar.
2. Select an existing evaluation dataset or upload an exported `.csv` file.
3. Enter your candidate **System Instruction / Target Prompt** under test (or select a preset like *Strict Policy Grounding*).
4. Click **Run Benchmark**.
5. View real-time results:
   - **Pass Rate %** and **Average Rubric Score**.
   - Side-by-side view comparing **Candidate Actual Output** vs **Reference Golden Output**.
   - Detailed **LLM-as-a-Judge Feedback** highlighting why each case passed or failed.

### Option B: CLI Benchmark Runner (CI/CD Automated Script)
EvalGen includes a standalone benchmark evaluation harness in `evals/run_evals.py`. It reads your `GEMINI_API_KEY` and `GEMINI_MODEL` from `backend/.env`, executes test prompts, and outputs a formatted terminal scorecard:

```bash
# Evaluate an exported CSV file downloaded from the dashboard
backend/.venv/bin/python evals/run_evals.py ~/Downloads/customer-support-evals.csv

# Or evaluate the default baseline dataset
backend/.venv/bin/python evals/run_evals.py evals/dataset.csv
```

#### Sample CLI Output:
```text
✨ Using live Google Gemini (gemini-3.7-flash) for evaluation.

🚀 Running Benchmark Suite: customer-support-evals.csv
================================================================================
[1/3] Testing: How do I request a refund for an order placed 10...
[2/3] Testing: My package arrived damaged and missing items...
[3/3] Testing: Can I change my delivery address after shipping...

================================================================================
📊 EVALUATION SCORECARD
================================================================================
╭──────────┬────────┬──────────┬────────┬───────────────────────────────────────────────╮
│ ID       │ Tier   │ Status   │ Score  │ Judge Critique                                │
├──────────┼────────┼──────────┼────────┼───────────────────────────────────────────────┤
│ 8f1a2b3c │ EASY   │ ✅ PASS  │ 0.95   │ Clear, polite, and follows 14-day policy.     │
│ a4d5e6f7 │ HARD   │ ✅ PASS  │ 0.88   │ Acknowledges damage and provides claim link.  │
│ 1c2d3e4f │ MEDIUM │ ❌ FAIL  │ 0.55   │ Missed required apology and timeframe bounds. │
╰──────────┴────────┴──────────┴────────┴───────────────────────────────────────────────╯

🎯 Overall Pass Rate: 2/3 Passed (66.7%)
```

---

## 10. Zero-Cost Cloud Deployment Runbook

### Step 1: Provision Neon Serverless Postgres
1. Go to [Neon.tech](https://neon.tech) and create a free project.
2. Copy the pooled connection string (e.g. `postgresql://user:pass@ep-xyz.us-east-2.aws.neon.tech/neondb?sslmode=require`).

### Step 2: Deploy Backend to Render via Blueprint
1. Go to [Render Dashboard](https://dashboard.render.com).
2. Click **New** -> **Blueprint** and connect your GitHub repository.
3. Render reads `render.yaml` automatically configuring:
   - Free Web Service plan (scale-to-zero)
   - Health check path: `/api/v1/health`
4. In Render environment settings, set:
   - `DATABASE_URL`: Your Neon Postgres connection string
   - `GEMINI_API_KEY`: Your Google Gemini API key
5. Copy your Render **Deploy Hook URL**.

### Step 3: Deploy Frontend to Cloudflare Pages
1. Go to [Cloudflare Dashboard](https://dash.cloudflare.com) -> **Workers & Pages**.
2. Create a project named `evalgen`.
3. In GitHub Repository Secrets, add:
   - `CLOUDFLARE_API_TOKEN`
   - `CLOUDFLARE_ACCOUNT_ID`
   - `RENDER_DEPLOY_HOOK_URL`
4. Pushing to `main` will automatically trigger GHCR container build, Render deploy, and Cloudflare Pages direct upload!

## License

MIT
