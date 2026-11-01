# Project Charter & Timeline (Revised — Mid-Term)
**Course:** CSE 4011 — Intelligent Developer Tools & AI DevOps  
**Evaluation:** A2 — Mid-Term Project Phase Evaluation  
**Project Name:** CostGuard — Intelligent Economic Regression Testing & Profiling for AI DevOps  

---

## 1. Updated Project Charter / Synopsis

### Project Title
**CostGuard:** Model-Led Economic Profiling, Pre-Deployment Regression Testing, and Autonomous Investigation for AI Workloads.

### Project Description
As engineering teams adopt Large Language Models (LLMs) and agentic workflows, software development teams face an unprecedented challenge: **silent economic regressions**. Unlike traditional codebases where regressions manifest as compilation or runtime errors, prompt modifications, model upgrades, or context window expansions frequently trigger catastrophic cost and latency increases without failing conventional tests.

CostGuard provides an end-to-end AI DevOps layer that:
1. Profiles LLM workloads on paired case suites before code ships.
2. Gates PR merges in CI/CD pipelines against explicit cost, latency, and quality thresholds.
3. Deploys an autonomous LLM Economic Investigator to diagnose token bloat and synthesize prompt refactor proposals.
4. Integrates seamlessly into developer productivity tools (Cursor, Claude, Gemini CLI) via the Model Context Protocol (MCP).

---

## 2. Project Timeline & Milestone Tracking (Progress vs. Plan)

| Phase | Milestone / Activity | Planned Dates | Actual Status | Deliverables & Outcomes |
| :--- | :--- | :---: | :---: | :--- |
| **Phase 1** *(A1)* | **Foundations & Architecture**<br>• Problem definition & synopsis<br>• Core economic model & schemas<br>• Unit test harness setup | Aug 24 – Sep 21 | **Completed (100%)** | • Project Charter<br>• Pydantic & SQLAlchemy data schemas<br>• Baseline mathematical formulas for token pricing |
| **Phase 2** *(A2 - Mid-Term)* | **Core Engine & CI/CD Integration**<br>• Economic comparison engine<br>• Pre-deployment CI/CD gate CLI<br>• Autonomous LLM Investigator loop<br>• MCP server implementation<br>• GitHub Actions workflow | Sep 22 – Oct 08 | **Completed (100%)** | • Working Prototype & CLI (`demo_eval.py`)<br>• 30 automated test cases passing<br>• Bounded tool-calling agent with spend guardrails<br>• GitHub Actions CI pipeline (`ci.yaml`) |
| **Phase 3** *(A3 - End-Term)* | **Production Polish & Real Providers**<br>• Live cloud LLM gateway testing<br>• LlamaIndex / LangChain RAG pipeline integration<br>• Interactive web dashboard enhancements<br>• Multi-user authentication & secrets | Oct 09 – Nov 15 | **Planned / In-Progress** | • End-to-end benchmark on open-source code models<br>• RAG context retrieval optimizer<br>• Final project report & conference-style presentation |

---

## 3. Rubric Alignment Matrix (Mid-Term Evaluation A2)

| Syllabus Rubric Requirement | Weightage | How CostGuard Addresses It | Implementation File / Evidence |
| :--- | :---: | :--- | :--- |
| **RAG & LLM Code Intelligence** | 10% | Profiles prompt token context, retrieval chunk overhead, and model tool loops. Autonomous agent diagnoses token inflation. | [`costguard/investigation.py`](file:///costguard/investigation.py)<br>[`costguard/economics.py`](file:///costguard/economics.py) |
| **GitHub Actions CI/CD Automation** | 10% | CLI gate (`python -m costguard gate`) integrated into GitHub Actions CI workflow to block PR regressions automatically. | [`.github/workflows/ci.yaml`](file:///.github/workflows/ci.yaml)<br>[`costguard/__main__.py`](file:///costguard/__main__.py) |
| **Test Generation & Code Quality** | 5% | 30 deterministic unit & E2E tests, contract validation, and strict Pydantic model assertions. | [`tests/test_analysis.py`](file:///tests/test_analysis.py)<br>[`tests/test_execution.py`](file:///tests/test_execution.py) |
| **Integration Quality & Docs** | 5% | MCP Server for Cursor/Gemini CLI, FastAPI backend, Docker Compose setup, and comprehensive documentation. | [`costguard/mcp_server.py`](file:///costguard/mcp_server.py)<br>[`docs/MIDSEM_PROGRESS_REPORT.md`](file:///docs/MIDSEM_PROGRESS_REPORT.md) |

---

## 4. Team Responsibility Matrix

| Team Member / Role | Primary Responsibilities | Core Deliverables Completed |
| :--- | :--- | :--- |
| **Lead Developer & AI Architect** | Core engine design, economic formulas, and CI/CD CLI gating | • `costguard/economics.py`<br>• `costguard/__main__.py` (gate CLI)<br>• CI/CD pipeline integration |
| **AI DevOps & Agent Engineer** | Autonomous LLM Investigator agent, ReAct tool design, and guardrails | • `costguard/investigation.py`<br>• Tool definitions (`inspect_comparison`, `inspect_case`)<br>• Spend cap enforcement |
| **Infrastructure & Test Engineer** | Docker orchestration, database schema, test harnesses, and documentation | • `compose.yaml`, `Dockerfile`<br>• Unit test suite (30 test cases)<br>• Progress report & demo script |
