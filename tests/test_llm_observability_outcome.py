"""
Unit and Integration Tests for:
1. LLMs Working (Unified Engine, Multi-provider, Simulation fallback)
2. Observability (Distributed Traces, OpenTelemetry Spans, Metrics Collector)
3. Economics of Successful Outcomes (ECSO, Wasted Spend, Policy Gating)
"""

import unittest
from decimal import Decimal

from costguard.analysis import compare_workloads
from costguard.llm import LLMClient, LLMMessage, default_llm_client
from costguard.models import ComparisonPolicy, ComparisonRequest, Workload, WorkloadRun, ModelCall, PricingCatalog, ModelPrice
from costguard.observability import ObservabilityTracer, tracer
from costguard.rag_qa import CostGuardRAGBot


def make_pricing() -> PricingCatalog:
    return PricingCatalog(
        version="v1",
        entries=[
            ModelPrice(
                provider="test-provider",
                model="test-model",
                input_per_million_usd=Decimal("10"),
                output_per_million_usd=Decimal("20"),
            )
        ],
    )


def make_run(case_id: str, input_tokens: int = 1000, output_tokens: int = 500, quality: str | None = "0.85", status: str = "ok") -> WorkloadRun:
    return WorkloadRun(
        case_id=case_id,
        calls=[
            ModelCall(
                provider="test-provider",
                model="test-model",
                input_tokens=input_tokens,
                output_tokens=output_tokens,
            )
        ],
        latency_ms=Decimal("500"),
        quality_score=Decimal(quality) if quality is not None else None,
        status=status,
    )


class LLMWorkingTests(unittest.TestCase):
    def setUp(self):
        self.client = LLMClient()

    def test_llm_generates_grounded_response_and_telemetry(self):
        messages = [
            LLMMessage(role="system", content="You are CostGuard AI assistant."),
            LLMMessage(role="user", content="How does CostGuard gate economic regressions in CI/CD?"),
        ]
        resp = self.client.chat_completion(messages=messages, model="gpt-4o-mini")

        self.assertIsNotNone(resp.content)
        self.assertGreater(len(resp.content), 20)
        self.assertIn("CostGuard", resp.content)
        self.assertGreater(resp.prompt_tokens, 0)
        self.assertGreater(resp.completion_tokens, 0)
        self.assertGreater(resp.total_tokens, 0)
        self.assertGreater(resp.latency_ms, 0)
        self.assertGreater(resp.ttft_ms, 0)
        self.assertIsNotNone(resp.trace_id)
        self.assertIsNotNone(resp.span_id)

    def test_rag_bot_integrates_with_llm_and_returns_grounded_answer(self):
        bot = CostGuardRAGBot()
        res = bot.ask("What are valid step kinds in execution traces?", top_k=2)

        self.assertEqual(res["retrieved_chunks"], 2)
        self.assertIn("answer", res)
        self.assertGreater(len(res["answer"]), 30)
        self.assertIn("llm_telemetry", res)
        self.assertIsNotNone(res["trace_id"])


class ObservabilityTests(unittest.TestCase):
    def setUp(self):
        self.tracer = ObservabilityTracer(max_traces=50)

    def test_trace_and_nested_span_hierarchy(self):
        with self.tracer.start_trace("parent_task_flow") as trace:
            with self.tracer.start_span("retrieval_step", kind="retrieval") as s_ret:
                s_ret.set_attribute("docs_count", 4)

            with self.tracer.start_span("llm_inference_step", kind="llm") as s_llm:
                s_llm.set_attribute("tokens", 250)
                s_llm.set_attribute("ttft_ms", 18.5)

        self.assertEqual(len(trace.spans), 2)
        self.assertEqual(trace.spans[0].name, "retrieval_step")
        self.assertEqual(trace.spans[0].kind, "retrieval")
        self.assertEqual(trace.spans[1].name, "llm_inference_step")
        self.assertEqual(trace.spans[1].kind, "llm")
        self.assertEqual(trace.status, "ok")
        self.assertGreater(trace.latency_ms, 0)

    def test_metrics_collector_aggregates_telemetry(self):
        with self.tracer.start_trace("test_run_1") as t1:
            with self.tracer.start_span("llm_span_1", kind="llm", attributes={"prompt_tokens": 100, "completion_tokens": 50, "ttft_ms": 20.0}):
                pass

        metrics = self.tracer.get_metrics()
        self.assertGreaterEqual(metrics["total_traces"], 1)
        self.assertGreaterEqual(metrics["total_tokens"], 150)
        self.assertGreater(metrics["avg_ttft_ms"], 0)
        self.assertIn("llm", metrics["spans_by_kind"])

    def test_export_opentelemetry_format(self):
        otel = self.tracer.export_otel()
        self.assertIn("resourceSpans", otel)
        self.assertGreaterEqual(len(otel["resourceSpans"]), 1)
        first_span = otel["resourceSpans"][0]["scopeSpans"][0]["spans"][0]
        self.assertIn("traceId", first_span)
        self.assertIn("spanId", first_span)


class OutcomeEconomicsTests(unittest.TestCase):
    def test_calculates_cost_per_task_and_ecso(self):
        pricing = make_pricing()
        baseline = Workload(
            name="base-workload",
            runs=[
                make_run("case-1", 1000, 500, quality="0.90", status="ok"),
                make_run("case-2", 1000, 500, quality="0.85", status="ok"),
            ],
        )
        # Candidate has 1 failed task (status="error") and 1 passed task
        candidate = Workload(
            name="cand-workload",
            runs=[
                make_run("case-1", 1200, 500, quality="0.92", status="ok"),
                make_run("case-2", 1200, 500, quality="0.20", status="error"),
            ],
        )

        req = ComparisonRequest(
            baseline=baseline,
            candidate=candidate,
            pricing=pricing,
        )
        report = compare_workloads(req)
        out = report.outcome_economics

        self.assertIsNotNone(out)
        self.assertEqual(out.baseline.total_tasks, 2)
        self.assertEqual(out.baseline.successful_tasks, 2)
        self.assertEqual(out.baseline.success_rate_percent, Decimal("100.00"))
        self.assertEqual(out.baseline.wasted_spend_usd, Decimal("0.00000000"))

        # Candidate had 1 failure out of 2 tasks -> 50% success rate
        self.assertEqual(out.candidate.total_tasks, 2)
        self.assertEqual(out.candidate.successful_tasks, 1)
        self.assertEqual(out.candidate.failed_tasks, 1)
        self.assertEqual(out.candidate.success_rate_percent, Decimal("50.00"))
        # ECSO = total cost / 1 success = 2x raw cost per task
        self.assertGreater(out.candidate.cost_per_successful_task_usd, out.candidate.cost_per_task_usd)
        self.assertGreater(out.candidate.wasted_spend_usd, Decimal("0"))
        self.assertEqual(out.candidate.wasted_spend_percent, Decimal("50.00"))
        self.assertIn("Candidate unit economics regressed", out.summary)

    def test_policy_gates_on_success_rate_and_wasted_spend(self):
        pricing = make_pricing()
        baseline = Workload(
            name="base",
            runs=[make_run("case-1", 1000, 500, status="ok")],
        )
        candidate = Workload(
            name="cand",
            runs=[make_run("case-1", 1000, 500, status="error")],
        )

        policy = ComparisonPolicy(
            min_candidate_task_success_rate_percent=Decimal("90.0"),
            max_candidate_wasted_spend_percent=Decimal("10.0"),
        )

        req = ComparisonRequest(
            baseline=baseline,
            candidate=candidate,
            pricing=pricing,
            policy=policy,
        )
        report = compare_workloads(req)

        self.assertEqual(report.policy.status, "fail")
        self.assertTrue(any("success rate" in v for v in report.policy.violations))
        self.assertTrue(any("wasted spend" in v for v in report.policy.violations))


if __name__ == "__main__":
    unittest.main()
