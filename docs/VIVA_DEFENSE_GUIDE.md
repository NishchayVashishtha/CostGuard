# CostGuard: Mid-Sem Viva & Evaluation Defense Guide
**Subject:** CSE 4011 — Intelligent Development Tools & AI DevOps  
**Evaluation:** A2 — Mid-Term Project Phase Evaluation  
**Instructor:** Dr. Kiran Khatter & Prof. Singh  

---

## 🚀 1. The 60-Second Elevator Pitch (Opening Statement)

> *"Good morning respected faculty. Our project is **CostGuard**, an AI DevOps system designed for **pre-deployment economic profiling, regression testing, and autonomous root-cause investigation of LLM applications**.*
>
> *In traditional DevOps, CI/CD pipelines check code compilation, unit tests, and security vulnerabilities. But in AI-native applications, when a developer modifies a prompt, increases RAG retrieved chunks, or switches a model in a Pull Request, traditional tests still pass—while production costs surge by 30% to 50% and latency spikes!*
>
> *CostGuard solves this by integrating directly into GitHub Actions CI/CD to gate pull requests against economic regression policies before code ships. Furthermore, it embeds an **autonomous LLM Economic Investigator** that uses tool-calling to identify the exact token hotspot and propose an optimized prompt experiment. We have a working prototype, 30 passing automated tests, and live CLI demonstration ready."*

---

## 🎯 2. Defense Mapped to the 7 Evaluation Criteria

### Criterion 1: Research Question & Experimental Alignment
- **Question:** What is your research question, and how does your experiment answer it?
- **Answer:**
  - **Research Question:** *"Can automated pre-deployment profiling and CI/CD gating detect prompt-level and model-level economic regressions before deployment, and can an autonomous LLM investigator reliably diagnose root causes and propose cost-reducing optimizations while preserving task accuracy?"*
  - **Alignment:** We set up a paired benchmark where a baseline workload (`main` branch) is compared against a pull request candidate (`feature/new-prompt`). The experiment directly measures whether our policy gate catches silent regressions and whether the LLM agent can identify the root cause without hallucinating.

### Criterion 2: Quantitative Evaluation
- **Question:** What quantitative metrics and baselines did you use?
- **Answer:**
  - **Baselines:** Reference baseline workload (1,000 input tokens, 500 output tokens at $10/M input, $20/M output).
  - **Metrics Tracked:**
    1. **Cost per Request:** $0.0200 vs $0.0250 (**+25.0% regression**)
    2. **Mean & P95 Latency:** 1000.0 ms vs 1200.0 ms (**+20.0% latency increase**)
    3. **Quality Score:** Evaluated via exact match / rubric (0.80 vs 0.84, **+5.0%**)
    4. **Monthly Spend Projection:** At 100k requests/month, spend increases from $2,000 to $2,500 (**+$500/month or +$6,000/year**)
    5. **Policy Threshold:** Gated at $\le 20\%$ cost increase.

### Criterion 3: Results & Interpretation
- **Question:** What patterns did you observe, and what conclusion do you draw?
- **Answer:**
  - **Observation:** The candidate prompt introduced boilerplate system instructions. While quality marginally ticked up from 0.80 to 0.84 (+5%), token consumption surged by 50% on input, driving a 25% total cost regression.
  - **Conclusion:** A small quality gain does not justify a 25% cost surge in high-throughput production. The CI/CD gate successfully threw an exit code `1` (FAIL), preventing deployment.
  - **Agent Action:** The LLM investigator attributed the hotspot specifically to system prompt inflation and proposed pruning unnecessary tokens to restore cost within policy limits while maintaining quality $\ge 0.82$.

### Criterion 4: Technical Implementation
- **Question:** How is this implemented technically?
- **Answer:**
  - **Core Economic Engine (`costguard/economics.py`):** High-precision arithmetic using Python `Decimal` to avoid floating-point drift.
  - **CI/CD CLI Gate (`costguard/__main__.py`):** Headless gate CLI returning exit code 0 (Pass) or 1 (Fail) for GitHub Actions.
  - **LLM Agent with Guardrails (`costguard/investigation.py`):** ReAct agent with explicit tool schemas (`inspect_comparison`, `inspect_case`, `propose_prompt_experiment`). Enforces strict spend limits ($0.10) and prevents hallucinations by verifying all evidence citations.
  - **Developer Tools Integration (`costguard/mcp_server.py`):** Model Context Protocol (MCP) server allowing tools like Cursor and Claude to inspect economic profiles.
  - **Infrastructure:** Docker Compose, PostgreSQL 17, Bifrost AI Gateway, FastAPI backend.

### Criterion 5: Limitations & Failure Analysis
- **Question:** What does NOT work? What are the limitations and potential sources of error?
- **Answer:**
  - **In-flight Token Abort:** We check spend limits between case executions, but cannot terminate an active in-flight streaming socket midway through generation.
  - **Synthetic vs Real Traffic Drift:** If synthetic case suites do not mirror real user prompts, the pre-deployment prediction may diverge from production spend.
  - **Missing Provider Usage:** If an upstream LLM provider fails to report token usage in its response, CostGuard marks the result as `inconclusive` rather than giving a false pass.
  - **Quality vs Cost Tradeoff:** Automated quality evaluators (exact match / LLM-as-a-judge) may have slight subjective bias when evaluating open-ended text.

### Criterion 6: Methodology & Reproducibility
- **Question:** Is your setup reproducible?
- **Answer:**
  - **Yes, 100% reproducible:**
    1. Run `python demo_eval.py` to reproduce the entire quantitative comparison and gating decision in 2 seconds.
    2. Run `python -m unittest discover -v` to verify all 30 unit and integration tests passing deterministically.
    3. All fixtures, pricing catalogs, and schemas are versioned JSON files in the repo.

### Criterion 7: Individual Understanding (Tough Viva Questions)

#### Q1: "How does this connect to DevOps? Isn't this just cost tracking?"
> **Answer:** *"In DevOps, the core principle is shift-left: finding problems before they reach production. Tools like Datadog or AWS Cost Explorer are post-deployment monitoring—they tell you you lost money after the bill arrives! CostGuard is pre-deployment regression testing in CI/CD. Just like SonarQube gates code smells and Pytest gates functional bugs, CostGuard gates economic and latency regressions in pull requests before code is merged."*

#### Q2: "How does this relate to RAG (Retrieval-Augmented Generation)?"
> **Answer:** *"In RAG workflows, developers frequently tweak top-k chunk retrieval (e.g., retrieving 8 chunks instead of 3). This dramatically expands input token context. CostGuard's execution schema explicitly supports step kinds `retrieval`, `model`, and `tool`. When developers increase retrieval context in a PR, CostGuard measures the token surge, attributes the cost difference directly to retrieval steps, and gates the PR if it exceeds budget."*

#### Q3: "How do you prevent the LLM Investigator from hallucinating false cost data?"
> **Answer:** *"Our LLM investigator does NOT calculate costs or invent numbers. The numerical calculations are computed deterministically by our Python economic engine. The LLM only receives tool outputs (`inspect_comparison`, `inspect_case`). Furthermore, in `costguard/investigation.py`, our conclusion schema validates citations: if the LLM cites a case ID that it did not inspect via tools, the engine rejects the conclusion as unvalidated."*

#### Q4: "How does this integrate with developer tools like Cursor or Sweep.dev?"
> **Answer:** *"CostGuard includes an MCP (Model Context Protocol) server. In modern AI IDEs like Cursor or Gemini CLI, coding agents can query CostGuard via MCP before refactoring code: 'What is the cost impact of changing this prompt?' The developer tool receives immediate economic feedback right inside the IDE."*

---

## 💻 3. Live Demonstration Cheat Sheet

When the professor says: *"Show me the demo / prototype"*

### Step 1: Run the Live Evaluation Demo
In the project terminal, run:
```bash
python demo_eval.py
```
**Point to the screen and say:**
1. *"Here is our experimental setup: Baseline main branch vs Candidate pull request."*
2. *"Our quantitative engine compares token counts and pricing: candidate cost rose by 25%, and latency rose by 20%."*
3. *"The DevOps policy threshold was 20%, so the CI/CD gate immediately triggered FAILED (Exit Code 1), blocking the PR."*
4. *"Our AI Investigator diagnosed the root cause: +500 prompt token bloat in the system prompt."*

### Step 2: Run the Automated Test Suite
```bash
python -m unittest discover -v
```
**Point to the screen and say:**
*"All 30 unit and integration tests passed cleanly in under 0.1 seconds, verifying economic formulas, spend thresholds, and anti-hallucination guardrails."*
