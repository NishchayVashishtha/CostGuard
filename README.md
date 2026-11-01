# CostGuard

**CostGuard** is an **economic intelligence, profiling, distributed observability, and pre-deployment regression-testing layer for AI applications and agentic workloads**.

CostGuard helps engineering teams understand the financial, behavioral, and quality consequences of an AI/LLM change *before it reaches production*: what became more expensive, why, whether latency or task success rates regressed, and whether proposed modifications satisfy explicit economic policies.

---

## Key Pillars

### 1. Unified LLM Execution Engine
- **Multi-Provider Support**: Direct integration with OpenAI (`gpt-4o`, `gpt-4o-mini`), Google Gemini (`gemini-1.5-flash`), Anthropic (`claude-3-5-sonnet`), Groq (`llama-3.3-70b`), local Ollama (`llama3`), and OpenAI-compatible gateways (e.g., Bifrost).
- **Intelligent Contextual Fallback (`IntelligentOfflineSimulator`)**: Built-in offline simulator that enables complete local development, demonstration, and automated test execution without external paid API keys.
- **RAG Codebase & Policy Q&A**: Semantic document indexing and grounded LLM synthesis via `CostGuardRAGBot`.

### 2. Distributed Observability & Telemetry
- **OpenTelemetry Standard Tracing**: Full parent-child span hierarchy tracking complete task lifecycles: `workflow` $\rightarrow$ `retrieval` $\rightarrow$ `llm` $\rightarrow$ `evaluation`.
- **Granular Latency & Token Metrics**:
  - **Streaming TTFT (Time To First Token)** tracking.
  - **P50 / P90 / P95 Latency** profiling.
  - **Token Throughput (tokens/second)** and Prompt vs. Completion token distribution.
  - **Error and Regression Rates** across workflow executions.
- **Observability Dashboard (`/observability`)**:
  - Interactive telemetry KPI cards.
  - Hierarchical visual waterfall / Gantt latency flame bars for each trace.
  - Live interactive LLM sandbox.
  - One-click OpenTelemetry standard JSON export.

### 3. Economics of Successful Outcomes (Unit Economics)
Traditional AI monitoring measures raw cost per token or cost per API call, which fails to capture real workflow value. CostGuard pioneers **Outcome Economics**:
- **Cost per Task ($/Task)**: Total workload spend divided by total attempted requests.
- **Effective Cost per Successful Outcome (ECSO - $/Success)**:
  $$\text{ECSO} = \frac{\text{Total Workload Cost}}{\text{Successful Tasks}} = \frac{\text{Cost per Attempt}}{\text{Task Success Rate}}$$
  *Catches hidden economic regressions where a cheaper model fails more frequently, doubling the effective cost per completed outcome.*
- **Wasted Spend ($ & %)**: Quantifies capital lost to failed tasks, validation rejections, and unnecessary retries.
- **Economic Efficiency Score**: Successful business outcomes delivered per $100 budget.
- **CI/CD Regression Gates**: Automated policies enforcing caps on `max_candidate_cost_per_successful_task_usd`, `min_candidate_task_success_rate_percent`, and `max_candidate_wasted_spend_percent`.

---

## Quickstart

### 1. Installation
Clone the repository and install dependencies:

```bash
git clone https://github.com/NishchayVashishtha/CostGuard.git
cd CostGuard
pip install -r requirements.txt
```

### 2. Start the Local Web Server
Launch the FastAPI application with live hot-reloading:

```bash
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

Open in your browser:
- **Observability Dashboard**: [http://localhost:8000/observability](http://localhost:8000/observability)
- **Overview & Reports**: [http://localhost:8000/](http://localhost:8000/)
- **Interactive OpenAPI Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## Live Demonstrations

CostGuard includes three ready-to-run demonstration scripts:

### A. Live RAG + LLM + Observability Demonstration
Demonstrates grounded semantic retrieval, live LLM generation, distributed tracing with TTFT, and context inflation profiling ($k=2$ vs $k=8$ chunks):

```bash
python demo_rag.py
```

### B. Mid-Semester Project Evaluation & Gating
Demonstrates baseline vs candidate workload comparison, quantitative unit economics, policy enforcement, and autonomous AI investigator root-cause diagnosis:

```bash
python demo_eval.py
```

### C. CI/CD Automated PR Review Bot Simulator
Emulates an automated GitHub Actions PR reviewer (Sweep.dev / CodiumAI style) that evaluates Pull Request economic impact and blocks merge on policy violations:

```bash
python simulate_pr_bot.py
```

---

## Running the Automated Test Suite

Run the complete test suite (39 unit and integration tests covering analysis, execution, RAG pipeline, LLMs, distributed tracing, and outcome economics):

```bash
python -m unittest discover -v
```

---

## REST API Overview

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | Service health check |
| `POST` | `/api/v1/llm/chat` | Execute chat completion with automated observability tracing |
| `GET` | `/api/v1/observability/traces` | List recent distributed traces and span hierarchies |
| `GET` | `/api/v1/observability/traces/{id}`| Retrieve detailed span waterfall for a specific trace |
| `GET` | `/api/v1/observability/metrics` | Retrieve aggregated latency, TTFT, token throughput & error rates |
| `GET` | `/api/v1/observability/otel` | Export traces in OpenTelemetry standard JSON format |
| `POST` | `/compare` | Stateless economic regression comparison for two workloads |
| `GET` | `/api/v1/comparisons` | List saved workload comparisons |
| `POST` | `/api/v1/scenarios` | Evaluate hypothetical repricing scenarios |

---

## Docker Compose (Optional Full Stack)

For containerized environments with PostgreSQL and the Bifrost gateway:

```bash
# Copy local configuration
cp .env.example .env

# Start demo profile
COSTGUARD_DEMO=1 docker compose --profile demo up -d --build
```

---

## License

This project is licensed under the Apache 2.0 License.
