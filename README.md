# EvalGen: AI Evaluation Set Generator

[![Backend CI](https://github.com/OWNER/evalgen/actions/workflows/ci-backend.yml/badge.svg)](https://github.com/OWNER/evalgen/actions/workflows/ci-backend.yml)
[![Frontend CI](https://github.com/OWNER/evalgen/actions/workflows/ci-frontend.yml/badge.svg)](https://github.com/OWNER/evalgen/actions/workflows/ci-frontend.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-emerald.svg)](LICENSE)

**EvalGen** is an open-source, full-stack AI evaluation suite generator designed for mastering **AI Evals**, synthetic test generation, structured LLM outputs, and **zero-cost cloud-native deployments**.

---

## 1. System Architecture

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

## 2. Tech Stack & Zero-Cost Cloud Strategy

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

## 3. Error Handling & Resilience Best Practices

### 3.1 Maximum 3-Attempt Exponential Backoff
All transient external interactions (LLM generation, rate limits, network resets) strictly enforce a **maximum retry limit of 3**:
- **Backend**: Decorated with `tenacity` exponential backoff with jitter (`1s`, `2s`, `4s` + jitter). If all 3 attempts fail, a typed `RateLimitExceededException` or `LLMGenerationException` is raised.
- **Frontend**: Axios interceptors automatically retry idempotent requests up to 3 times before displaying actionable failure cards.

### 3.2 Displaying Errors to the UI for Best UX
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

## 4. Repository Structure

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
│   ├── ci-backend.yml              # Ruff + Pytest on PR/push
│   ├── ci-frontend.yml             # Vue-tsc + Vite build check on PR/push
│   ├── deploy-backend.yml          # Build Docker, push to GHCR, deploy to Render
│   └── deploy-frontend.yml         # Build & direct upload to Cloudflare Pages
├── render.yaml                     # Render Blueprint (Infrastructure as Code)
├── .gitignore
└── README.md
```

---

## 5. Local Development Quickstart

### Prerequisites
- Python 3.11+
- Node.js 20+ and npm

### 5.1 Backend Setup
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
API Documentation will be available at [http://localhost:8000/docs](http://localhost:8000/docs).

### 5.2 Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Start Vite development server
npm run dev
```
Open [http://localhost:5173](http://localhost:5173) in your browser.

---

## 6. Running Tests

```bash
cd backend
source .venv/bin/activate
pytest tests -v
```

Tests include verification that transient rate limit errors retry **exactly 3 times** before aborting.

---

## 7. Zero-Cost Cloud Deployment Runbook

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
