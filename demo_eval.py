"""
CostGuard Mid-Sem Live Demonstration Script
AI DevOps (CSE 4011) - Intelligent Developer Tools

Demonstrates:
1. Workload Profiling (Baseline vs Candidate)
2. Quantitative Economic & Latency Comparison
3. Automated CI/CD Policy Gate (Pass/Fail)
4. Economics of Successful Outcomes (Cost per Task & ECSO)
5. Live LLM Economic Investigator diagnosis & Observability Tracing
"""

import json
from decimal import Decimal
from costguard.economics import compare_workloads
from costguard.llm import LLMMessage, default_llm_client
from costguard.models import ComparisonRequest
from costguard.observability import tracer

def main():
    print("=" * 72)
    print("  CostGuard: Pre-Deployment Economic Regression Testing for AI DevOps")
    print("  Subject: AI DevOps (CSE 4011) - Mid-Sem Project Evaluation")
    print("=" * 72)
    print()

    # 1. Load experiment workload fixture
    fixture_path = "examples/comparison.json"
    print(f"[*] Loading workload specification from '{fixture_path}'...")
    with open(fixture_path, "r") as f:
        data = json.load(f)

    baseline = data["baseline"]
    candidate = data["candidate"]
    pricing = data["pricing"]["entries"][0]
    policy = data["policy"]

    print("\n[+] EXPERIMENTAL SETUP:")
    print(f"    - Baseline Branch:    {baseline['name']} (1000 input tokens, 500 output tokens)")
    print(f"    - Candidate (PR):     {candidate['name']} (1500 input tokens, 500 output tokens)")
    print(f"    - Model / Provider:   {pricing['provider']} / {pricing['model']}")
    print(f"    - Pricing Catalog:    ${pricing['input_per_million_usd']}/M input tokens, ${pricing['output_per_million_usd']}/M output tokens")
    print(f"    - DevOps Policy:      Max Cost Regression <= {policy['max_cost_increase_percent']}%")
    print(f"    - Monthly Projection: {data['monthly_requests']:,} requests/month")

    # 2. Run Economic Engine inside Observability Trace
    print("\n[*] Executing CostGuard Economic Engine & Observability Tracer...")
    with tracer.start_trace("midsem_evaluation_workload") as trace:
        with tracer.start_span("economic_engine_compare", kind="workflow") as comp_span:
            request = ComparisonRequest.model_validate(data)
            report = compare_workloads(request)
            comp_span.set_attribute("baseline_cost", str(report.cost_per_request_usd.baseline))
            comp_span.set_attribute("candidate_cost", str(report.cost_per_request_usd.candidate))
            comp_span.set_attribute("policy_status", report.policy.status)

    cost_base = report.cost_per_request_usd.baseline
    cost_cand = report.cost_per_request_usd.candidate
    cost_delta = report.cost_per_request_usd.delta_percent

    lat_base = report.mean_latency_ms.baseline
    lat_cand = report.mean_latency_ms.candidate
    lat_delta = report.mean_latency_ms.delta_percent

    q_base = report.quality_score.baseline
    q_cand = report.quality_score.candidate
    q_delta = report.quality_score.delta_percent

    proj_delta = report.monthly_projection.cost_usd.delta
    out = report.outcome_economics

    # 3. Quantitative Results Table
    print("\n" + "=" * 72)
    print("  QUANTITATIVE EVALUATION RESULTS (Baseline vs Candidate)")
    print("=" * 72)
    print(f"  Metric                             Baseline        Candidate       Delta (%)")
    print(f"  ---------------------------------------------------------------------------")
    print(f"  Cost per Request ($)               ${cost_base:<14.4f} ${cost_cand:<14.4f} +{cost_delta:.1f}%")
    print(f"  Mean Latency (ms)                  {lat_base:<15.1f} {lat_cand:<15.1f} +{lat_delta:.1f}%")
    print(f"  Quality Score (0-1)                {q_base:<15.2f} {q_cand:<15.2f} +{q_delta:.1f}%")
    if out:
        print(f"  Cost / Successful Task (ECSO) ($)  ${out.baseline.cost_per_successful_task_usd:<14.4f} ${out.candidate.cost_per_successful_task_usd:<14.4f} +{out.cost_per_successful_task.delta_percent or 0:.1f}%")
        print(f"  Task Success Rate (%)              {out.baseline.success_rate_percent}%         {out.candidate.success_rate_percent}%         +{out.success_rate.delta_percent or 0:.1f}%")
        print(f"  Wasted Spend ($)                   ${out.baseline.wasted_spend_usd:<14.4f} ${out.candidate.wasted_spend_usd:<14.4f} 0.0%")
    print(f"  Monthly Spend Delta ($)            --              --              +${proj_delta:.2f}/mo")
    print("=" * 72)

    # 4. CI/CD Policy Gate Decision
    print("\n[+] CI/CD REGRESSION GATE DECISION:")
    if report.policy.status == "fail":
        print(f"    >>> STATUS: [ FAILED ] (Exit Code 1 -> Blocks CI/CD Merge)")
        for v in report.policy.violations:
            print(f"    >>> VIOLATION: {v}")
    else:
        print(f"    >>> STATUS: [ PASSED ] (Exit Code 0 -> Safe to Merge)")

    # 5. Live LLM Investigator Root Cause Analysis
    print("\n[+] AUTONOMOUS AI INVESTIGATOR ROOT CAUSE DIAGNOSIS (Live LLM Inference):")
    investigator_prompt = [
        LLMMessage(role="system", content="You are CostGuard's autonomous economic investigator. Diagnose cost regressions."),
        LLMMessage(role="user", content=f"Baseline cost is ${cost_base}/req, candidate cost is ${cost_cand}/req (+{cost_delta}%). Quality delta is +{q_delta}%. Diagnose root cause and provide proposal.")
    ]
    llm_resp = default_llm_client.chat_completion(investigator_prompt)
    print(llm_resp.content)
    print(f"\n    [Telemetry: {llm_resp.model} | {llm_resp.latency_ms}ms latency | TTFT: {llm_resp.ttft_ms}ms | Trace ID: {llm_resp.trace_id}]")

    print("\n[OK] CostGuard Evaluation Complete. Ready for CI/CD PR annotation & Viva defense.")
    print("=" * 72)

if __name__ == "__main__":
    main()
