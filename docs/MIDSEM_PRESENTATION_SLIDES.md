# CostGuard: Mid-Semester Evaluation Presentation
**Course:** CSE 4011 — Intelligent Developer Tools & AI DevOps  
**Evaluation:** A2 — Mid-Term Project Phase Evaluation  
**Faculty Evaluators:** Dr. Kiran Khatter & Prof. Singh  

---

## 🖥️ Slide 1: Title Slide

### Slide Content:
- **Title:** CostGuard: Pre-Deployment Economic Profiling & CI/CD Regression Gating for AI Workloads
- **Subtitle:** An AI DevOps Architecture for Shifting-Left LLM Cost, Latency, and Context Evaluation
- **Course:** CSE 4011 — Intelligent Developer Tools & AI DevOps
- **Team Members:** [Student Name(s) & Roll Numbers]
- **Date:** Mid-Semester Evaluation (October 2026)
- **Project Repository:** `github.com/lazinWolf/CostGuard`

> 🗣️ **Speaker Notes (Aapko kya bolna hai):**  
> *"Good morning respected faculty. Today we are presenting our AI DevOps project, **CostGuard**. CostGuard is a pre-deployment economic profiling and regression testing layer that integrates directly into CI/CD pipelines to prevent unexpected cost, latency, and token bloat before code is shipped to production."*

---

## 🖥️ Slide 2: The Problem: Silent Regressions in AI DevOps

### Slide Content:
- **Traditional DevOps vs AI DevOps:**
  - Traditional CI/CD catches compilation errors, syntax breaks, and functional bugs via unit tests.
  - In AI-augmented systems, a developer modifying a system prompt or expanding RAG context still passes unit tests!
- **The Core Threat: Silent Economic Regressions:**
  - Token consumption surges by 30% to 50%.
  - Response latency doubles.
  - Unbounded tool loops spiral.
- **The Monitoring Dilemma:**
  - APM tools (Datadog, AWS Cost Explorer) only report costs **post-production** (after the money is already burnt).
  - **Need for Shift-Left:** Catch LLM economic and latency regressions in pull requests **pre-deployment**.

> 🗣️ **Speaker Notes:**  
> *"In traditional software engineering, if code breaks, tests fail. But with LLMs, if a developer expands a prompt or modifies a model in a PR, tests still pass with 100% green checks. However, production cloud bills surge by thousands of dollars, and user latency spikes. Existing observability tools only show you the bill at the end of the month. CostGuard solves this by bringing 'Shift-Left' principles to LLM economics—gating pull requests before they merge."*

---

## 🖥️ Slide 3: Research Question & Core Objectives

### Slide Content:
- **Primary Research Question:**
  > *"Can an automated pre-deployment CI/CD gating pipeline detect prompt-level and model-level economic regressions before deployment, and can an autonomous LLM investigator reliably diagnose root causes and propose cost-reducing optimizations while preserving output quality?"*
- **Measurable Objectives:**
  1. **Shift-Left Gating:** Block PRs violating economic policies (e.g., cost increase $>20\%$, latency $>1000\text{ ms}$).
  2. **Deterministic Economics:** Attribute cost changes down to individual prompt tokens, tool steps, and retrieval calls using explicit pricing catalogs.
  3. **Agentic Root-Cause Diagnosis:** Implement a bounded ReAct-style LLM Investigator to identify token hotspots and propose prompt optimizations.
  4. **Developer Workflow Integration:** Expose economic metrics to AI IDEs (Cursor, Gemini CLI) via the Model Context Protocol (MCP).

> 🗣️ **Speaker Notes:**  
> *"Our research addresses whether we can mathematically detect silent prompt regressions in automated CI/CD pipelines, and whether an AI agent can autonomously diagnose the root cause and refactor the prompt without human intervention or hallucinations. Our objectives focus on automated gating, exact attribution, agentic diagnosis, and IDE integration."*

---

## 🖥️ Slide 4: System Architecture & AI DevOps Workflow

### Slide Content:
```
[Developer PR / Prompt Change]
              │
              ▼
    [GitHub Actions CI/CD] ─── (Sweep.dev style PR Bot)
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
- **FastAPI Core:** High-performance headless REST API & web dashboard.
- **Economic Engine:** High-precision Decimal math calculating per-request delta and monthly projections.
- **AI Gateway & Providers:** Integrated with Bifrost AI Gateway, OpenAI-compatible APIs, and local Ollama models.
- **Model Context Protocol (MCP):** Connects to Cursor and Gemini CLI.

> 🗣️ **Speaker Notes:**  
> *"Here is our end-to-end architecture. When a developer submits a PR, GitHub Actions triggers CostGuard. It executes paired case suites on both baseline and candidate configurations. Our economic engine applies explicit pricing and policy rules. If cost exceeds policy thresholds, the pipeline fails with exit code 1, blocking the PR. Concurrently, our LLM Economic Investigator diagnoses the trace, isolates the hotspot, and posts an actionable recommendation directly as a PR comment."*

---

## 🖥️ Slide 5: Methodology & Experimental Setup

### Slide Content:
- **Workload Test Suite:** Curated software engineering tasks (support QA, code completion, code explanation).
- **Experimental Control:**
  - **Baseline (`main` branch):** Concise system prompt (`"Answer briefly."`), 1,000 input tokens, 500 output tokens.
  - **Candidate (`feature/new-prompt`):** Over-engineered system prompt (`"Answer accurately. Read carefully..."`), 1,500 input tokens, 500 output tokens.
- **Pricing Catalog:** Versioned pricing entries ($10/M input tokens, $20/M output tokens).
- **Traffic Assumptions:** 100,000 requests/month production scale.
- **DevOps Policy Threshold:** Maximum permissible cost increase $\le 20\%$.

> 🗣️ **Speaker Notes:**  
> *"To rigorously test our system, we created a controlled experimental benchmark. Our baseline represents production code with a concise prompt. Our candidate branch simulates a developer adding defensive instructions to the system prompt. Both run across identical test cases with standardized pricing and a strict 20% regression policy."*

---

## 🖥️ Slide 6: Quantitative Evaluation Results

### Slide Content:
| Metric | Baseline (`main`) | Candidate (PR) | Delta ($\Delta$) | Impact & Interpretation |
| :--- | :---: | :---: | :---: | :--- |
| **Cost per Request ($)** | **$0.0200** | **$0.0250** | **+25.0%** | Exceeds DevOps Policy ($\le 20\%$) |
| **Mean Latency (ms)** | 1000.0 ms | 1200.0 ms | **+20.0%** | Slower user response time |
| **Task Quality Score** | 0.80 | 0.84 | **+5.0%** | Marginal quality gain |
| **Monthly Spend (100k req)** | $2,000.00 | $2,500.00 | **+$500.00** | Direct cloud burn of +$6,000/year |
| **CI/CD Gate Decision** | — | — | **FAILED (Code 1)** | **PR Merge Blocked** |

> 🗣️ **Speaker Notes:**  
> *"These are our quantitative results. Look at the trade-off: The candidate prompt achieved a minor 5% quality improvement, but at the cost of a 25% cost surge and 20% latency penalty. For a workload of 100,000 monthly requests, this represents a $6,000 annual leak. Our CI/CD gate immediately detected the violation and blocked the merge."*

---

## 🖥️ Slide 7: Autonomous LLM Investigator & Root-Cause Analysis

### Slide Content:
- **Bounded ReAct Agent Loop:**
  - Tools: `inspect_comparison`, `inspect_case`, `propose_prompt_experiment`, `finish_investigation`.
  - Guardrails: Strict spend ceiling ($0.10 limit), maximum 5 execution turns.
- **Anti-Hallucination Citation Verification:**
  - The model cannot invent numbers; all figures come from deterministic engine receipts.
  - If the agent references a case it did not inspect via tools, the conclusion is rejected.
- **Autonomous Diagnosis:**
  - Hotspot identified: +500 input tokens due to verbose system prompt boilerplate.
  - Proposal synthesized: Prunes redundant instructions while retaining semantic directives.
  - Outcome: Restores cost to $0.0200 while maintaining quality $\ge 0.82$.

> 🗣️ **Speaker Notes:**  
> *"Instead of just failing the pipeline, CostGuard includes an autonomous AI Economic Investigator. It runs in a strictly bounded tool-calling loop with a 10-cent spending limit. It inspected the comparison, identified that the system prompt was bloated with redundant guidelines, and synthesized an optimized prompt proposal that brought costs back within policy limits while maintaining output quality."*

---

## 🖥️ Slide 8: RAG Intelligence & Context Profiling (LangChain Integration)

### Slide Content:
- **The RAG Dilemma in Software Engineering:**
  - Developers routinely increase retrieved chunk count ($k=2 \rightarrow k=8$) to boost retrieval recall.
  - This multiplies context tokens by 300% to 400%, exploding LLM API bills.
- **CostGuard RAG Profiler (`costguard/rag_qa.py`):**
  - **Baseline RAG ($k=2$ chunks):** 600 input tokens, $0.021/req, 450 ms latency.
  - **Candidate RAG ($k=8$ chunks):** 2,400 input tokens, $0.049/req (**+134% cost**), 1,150 ms (**+156% latency**).
  - Retrieval Quality: 0.85 $\rightarrow$ 0.88 (+3.5% marginal gain).
- **DevOps Gate Decision:** [FAIL] — Policy blocks RAG context inflation in CI/CD.
- **Codebase RAG Bot:** Implements semantic indexing over codebase documentation for developer Q&A.

> 🗣️ **Speaker Notes:**  
> *"A key component of our course syllabus is RAG architectures. In RAG pipelines, developers often innocently bump top-k chunks from 2 to 8. We profiled this exact scenario: retrieving 8 chunks gave only a 3.5% quality bump, but caused an alarming 134% cost explosion and more than doubled latency! CostGuard's RAG profiler caught this regression and blocked the PR, proving our ability to gate RAG architectures."*

---

## 🖥️ Slide 9: AI-Enhanced CI/CD & GitHub Actions Automation (Sweep.dev style)

### Slide Content:
- **Headless CI/CD Integration (`costguard_ai_devops.yml`):**
  - Triggers automatically on `pull_request` (opened, synchronize).
  - Executes unit tests and headless CostGuard regression gate.
- **Sweep.dev Style Automated PR Review Bot (`simulate_pr_bot.py`):**
  - Synthesizes an automated PR comment detailing the cost breakdown, latency changes, and policy status.
  - Annotates PR with root-cause diagnosis.
- **Hard Enforcement:**
  - Pull Request merge button is disabled on failure (exit code 1).
  - Shifts developer awareness directly to token economics inside GitHub.

> 🗣️ **Speaker Notes:**  
> *"To fulfill the CI/CD and Sweep.dev automation rubric, we built an automated GitHub Actions workflow. When a pull request is submitted, our bot runs the economic checks, generates a rich markdown review comment on the PR, and locks the merge button if policies are violated. We also have a live simulator that we can demonstrate right now."*

---

## 🖥️ Slide 10: AI-Assisted Testing & Verification (CodiumAI Standards)

### Slide Content:
- **Comprehensive Test Suite:**
  - 32 automated unit, contract, and integration tests (`tests/test_analysis.py`, `tests/test_execution.py`, `tests/test_investigation.py`, `tests/test_rag_pipeline.py`).
  - **Execution Time:** All 32 tests pass in **0.020 seconds** (100% pass rate).
- **Boundary & Contract Verification:**
  - Rejection of invalid token counts (negative or boolean tokens).
  - Spend threshold interruption tests.
  - Anti-hallucination citation checks.
  - Inconclusive handling for dropped telemetry.

> 🗣️ **Speaker Notes:**  
> *"For testing and code quality, we followed modern AI test-generation principles. Our suite contains 32 comprehensive tests verifying economic formulas, edge cases like dropped provider tokens, and agent spend caps. The entire test suite executes in just 20 milliseconds with zero failures."*

---

## 🖥️ Slide 11: Limitations & Failure Analysis

### Slide Content:
- **1. In-Flight Stream Guarding:**
  - Spend limits are checked between case runs, not as mid-stream socket aborts during active token streaming.
- **2. Telemetry Drop & Provider Errors:**
  - If a cloud LLM gateway fails to return token counts, CostGuard marks the run as **`inconclusive`** rather than granting a false pass.
- **3. Synthetic Test vs Production Drift:**
  - Pre-deployment test cases are synthetic. Real-world traffic distribution may drift, requiring continuous baseline recalibration.
- **4. Quality Evaluation Subjectivity:**
  - Automated evaluators (exact match / LLM judge) can have slight variance on creative, open-ended tasks.

> 🗣️ **Speaker Notes:**  
> *"A critical aspect of our evaluation is understanding what does NOT work. First, our spend limits check between cases, not midway through an active TCP streaming call. Second, if an LLM provider omits token usage, we never give a false pass—we mark it inconclusive. Third, synthetic test suites cannot fully replicate production user drift, so baselines must be re-anchored periodically."*

---

## 🖥️ Slide 12: Project Timeline: Progress vs Plan

### Slide Content:
| Milestone | Planned Timeline | Current Status | Delivered Artifacts |
| :--- | :---: | :---: | :--- |
| **Phase 1: Foundations** | Aug 24 – Sep 21 | **100% Completed** | Problem Charter, Schemas, Pricing Formulas |
| **Phase 2: Mid-Term (A2)** | Sep 22 – Oct 08 | **100% Completed** | Economic Engine, CI/CD Gate, LLM Investigator, RAG Profiler, Web Dashboard, 32 Tests |
| **Phase 3: End-Term (A3)** | Oct 09 – Nov 15 | **On Track** | Multi-tenant auth, Live cloud provider benchmarks, Production trace ingestion |

> 🗣️ **Speaker Notes:**  
> *"Here is our timeline. We are currently 100% on track. All deliverables planned for the Mid-Term milestone—the economic engine, CI/CD gating, LLM investigator, RAG profiler, and working prototypes—are fully complete and operational."*

---

## 🖥️ Slide 13: Summary & Conclusion

### Slide Content:
- **Core Value Proposition:** CostGuard establishes a new pre-deployment safety layer for AI engineering.
- **Key Achievements:**
  1. Automated detection of silent prompt and RAG token regressions in CI/CD.
  2. Sub-second economic gating preventing costly PR merges.
  3. Autonomous root-cause attribution without hallucinated data.
  4. Full alignment with AI DevOps developer tools (MCP, GitHub Actions, LangChain).
- **Live Prototypes Ready for Demo:**
  - `python demo_eval.py` (Main Economic Gate)
  - `python demo_rag.py` (RAG Context Profiling)
  - `python simulate_pr_bot.py` (GitHub PR Bot)
  - Web UI at `http://localhost:8000/docs`

> 🗣️ **Speaker Notes:**  
> *"To conclude, CostGuard bridges the gap between software development and LLM economics. It empowers engineering teams to ship AI features rapidly without fear of silent cloud bill explosions. We are now excited to demonstrate our working software live. Thank you, and we welcome your questions!"*
