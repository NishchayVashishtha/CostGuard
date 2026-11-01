"""
Unit & Contract Tests for CostGuard RAG Engine & Profiler
AI-Assisted Test Harness (CodiumAI / Pytest standard)
"""

import unittest
from decimal import Decimal
from costguard.rag_qa import CostGuardRAGBot, profile_rag_devops_workload

class RAGPipelineTests(unittest.TestCase):
    def setUp(self):
        self.bot = CostGuardRAGBot()

    def test_rag_bot_retrieves_relevant_context(self):
        query = "How does CostGuard gate regressions?"
        result = self.bot.ask(query, top_k=2)
        self.assertEqual(result["retrieved_chunks"], 2)
        self.assertGreater(result["retrieved_tokens"], 0)
        self.assertIn("README.md", result["sources"])

    def test_rag_profiler_detects_context_bloat_regression(self):
        profile = profile_rag_devops_workload()
        report = profile["report"]

        # Verify quantitative calculations
        self.assertEqual(report.cost_per_request_usd.baseline, Decimal("0.02100000"))
        self.assertEqual(report.cost_per_request_usd.candidate, Decimal("0.04920000"))
        self.assertGreater(report.cost_per_request_usd.delta_percent, Decimal("100.0"))

        # Verify CI/CD policy gating failure
        self.assertEqual(report.policy.status, "fail")
        self.assertTrue(any("exceeds 25%" in v for v in report.policy.violations))

if __name__ == "__main__":
    unittest.main()
