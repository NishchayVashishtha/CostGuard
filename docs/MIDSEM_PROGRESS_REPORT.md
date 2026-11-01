# Mid-Semester Project Progress Report
**Course:** CSE 4011 — Intelligent Developer Tools & AI DevOps  
**Evaluation:** A2 — Mid-Term Project Phase Evaluation (30% Weightage)  
**Project Title:** CostGuard: Pre-Deployment Economic Profiling & CI/CD Regression Gating for LLM Workloads  
**Evaluator:** Dr. Kiran Khatter & Prof. Singh  

---

## 1. Research Question & Problem Definition

### Problem Statement
In traditional DevOps, CI/CD pipelines prevent functional breakage via unit, integration, and contract tests. However, in modern AI-augmented software engineering, **non-functional regressions—specifically token consumption, API operational costs, and latency spikes—frequently occur silently**. Developers modify prompt templates, inject large context/RAG chunks, or switch LLM endpoints in a Pull Request (PR). The code still compiles and traditional unit tests pass, but production cloud bills surge and latency doubles.

### Core Research Question
> *"Can an automated pre-deployment profiling and CI/CD gating pipeline detect prompt-level and model-level economic regressions prior to merging, and can an autonomous LLM investigator reliably diagnose root causes and propose cost-reducing optimizations while preserving output quality?"*

### Objectives & Experimental Alignment
1. **Automated Gating:** Intercept LLM regressions in GitHub Actions CI/CD workflows using configurable economic policies (e.g., max 10–20% cost regression).
2. **Deterministic Economic Profiling:** Compare matched baseline and candidate test suites against explicit, versioned provider pricing catalogs.
3. **Agentic Root-Cause Diagnosis:** Implement a bounded ReAct-style LLM Economic Investigator that inspects execution traces, attributes token hotspots, and proposes optimized system prompts.
4. **Developer Tool Integration:** Expose economic metrics to developer assistants (e.g., Cursor, Gemini CLI) via the Model Context Protocol (MCP).

---

## 2. Methodology & Experimental Setup

```
[Developer PR / Prompt Change]
              │
              ▼
    [GitHub Actions CI/CD]
              │
    ┌─────────┴─────────┐
    ▼                   ▼
[Baseline Suite]    [Candidate Suite]
(Reference Model)   (Proposed PR Workload)
    │                   │
    └─────────┬─────────┘
              ▼
   [CostGuard Economic Engine] ◄── [Pricing Catalog & Policy]
              │
   ┌──────────┴──────────┐
   ▼                     ▼
[Pass: Code Merged]   [Fail: PR Blocked (Exit Code 1)]
                         │
                         ▼
           [LLM Economic Investigator]
           (inspect_comparison, inspect_case)
                         │
                         ▼
        [Root Cause: Hotspot Attribution]
        [Proposal: Optimized System Prompt]
```

### Experimental Setup & Dataset
- **Workload Test Suite:** Standardized paired test cases evaluating common software engineering prompts (e.g., support QA, code explanation, code completion).
- **Baseline Configuration:** Concise system prompt (`"Answer briefly."`), 1,000 input tokens, 500 output tokens.
- **Candidate Configuration:** Over-engineered system prompt (`"Answer accurately. Read the request carefully..."`), 1,500 input tokens, 500 output tokens.
- **Pricing Catalog:** Standardized pricing version (`$10.00 / M input tokens`, `$20.00 / M output tokens`).
- **DevOps Policy Threshold:** Maximum permissible cost increase $\le 20\%$.

---

## 3. Quantitative Evaluation & Results Interpretation

### Empirical Comparison (Baseline vs Candidate)

| Metric | Baseline | Candidate (PR) | Delta ($\Delta$) | Impact / Interpretation |
| :--- | :---: | :---: | :---: | :--- |
| **Cost per Request ($)** | **$0.0200** | **$0.0250** | **+25.0%** | Exceeds policy threshold ($\le 20\%$) |
| **Mean Latency (ms)** | 1000.0 ms | 1200.0 ms | **+20.0%** | Slower response due to prompt length |
| **Quality Score (0.0 - 1.0)** | 0.80 | 0.84 | **+5.0%** | Marginal quality gain does not justify cost |
| **Monthly Spend (100k req)** | $2,000.00 | $2,500.00 | **+$500.00** | Direct cloud spend increase of $6,000/year |
| **CI/CD Gating Status** | — | — | **FAILED (Code 1)** | PR merge blocked automatically |

### Interpretation & Pattern Identification
- **Economic Inefficiency:** The candidate PR introduced an unmonitored prompt bloat (+500 input tokens per call). While accuracy improved marginally by $5\%$, cost surged by $25\%$, resulting in a severe cost-to-benefit asymmetry.
- **CI/CD Enforcement:** The CostGuard regression gate executed with exit code `1`, preventing silent deployment into production.
- **Agent Diagnosis:** The autonomous LLM Investigator queried the comparison evidence via tool-calling, detected that the system prompt was the primary contributor to token bloat, and synthesized an optimized prompt proposal restoring baseline cost while retaining quality $\ge 0.82$.

---

## 4. Technical Implementation & Architecture

1. **Economic Engine (`costguard/economics.py`):**
   - High-precision decimal arithmetic calculating case-level and model-level cost deltas.
   - Evaluator tracking (`exact:v1`, semantic match).
2. **RAG-based Code & Policy Q&A Engine (`costguard/rag_qa.py`):**
   - LangChain-compatible semantic index over repository docs and economic policies.
   - Profiles context retrieval overhead ($k=2$ vs $k=8$) to catch token bloat regressions in RAG pipelines.
3. **CI/CD CLI Gate & GitHub Actions (`.github/workflows/costguard_ai_devops.yml`):**
   - Automated PR gate that runs on every pull request, catches cost/latency regressions, and posts an AI review summary (Sweep.dev style).
   - Headless execution: `python -m costguard gate --baseline <base.json> --candidate <cand.json> --pricing <price.json> --policy <policy.json>`
   - Exit codes: `0` (Pass), `1` (Fail), `2` (Inconclusive/Error).
4. **Agentic Investigator (`costguard/investigation.py`):**
   - Bounded tool-use loop: `inspect_comparison`, `inspect_case`, `propose_prompt_experiment`, `finish_investigation`.
   - Strict spending limits (`stop_after_usd = $0.10`), max call caps (5 turns), and citation verification against hallucinated evidence.
5. **Developer Tooling & MCP Server (`costguard/mcp_server.py`):**
   - Model Context Protocol server exposing read-only queries to Cursor, Claude Desktop, and Gemini CLI.
5. **AI Gateway & Infrastructure:**
   - Bifrost AI Gateway (`maximhq/bifrost:v2.2.3`), PostgreSQL 17 persistence, and Docker Compose modularity.

---

## 5. Limitations & Failure Analysis

1. **In-Flight Spend Guarding:**
   - *Limitation:* Spend caps are enforced between sequential case runs, not as mid-stream TCP cancellation during active token generation.
2. **Missing Usage Telemetry:**
   - *Failure Mode:* If a downstream provider gateway omits token counts, CostGuard returns `inconclusive` rather than a false `pass`, preserving pipeline integrity.
3. **Synthetic Test Coverage vs Real-World Distribution:**
   - *Limitation:* Pre-deployment evaluation relies on curated case suites. Production traffic may experience distribution drift requiring periodic baseline re-calibration.
4. **RAG Context Variability:**
   - *Assumption:* Chunk retrieval counts ($k$) must be held constant during prompt comparisons to isolate model and prompt effects from vector search variance.

---

## 6. Reproducibility & Verification

- **Test Suite Verification:** 30 unit and integration tests passing (`python -m unittest discover -v`).
- **Live CLI Demo:** Executable in under 2 seconds (`python demo_eval.py`).
- **Deterministic Fixtures:** Test data specified in `examples/comparison.json` with reproducible inputs and outputs.
