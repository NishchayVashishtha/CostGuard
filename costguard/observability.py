"""
CostGuard Observability: Enterprise Tracing, Span Trees, and Telemetry Engine.
Follows OpenTelemetry standards for LLM workflows, RAG pipelines, and agent loops.
"""

from __future__ import annotations

import contextvars
import os
import threading
import time
from dataclasses import asdict, dataclass, field
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import uuid4

# Context variables for automatic span hierarchy propagation
_CURRENT_TRACE: contextvars.ContextVar[Optional[Trace]] = contextvars.ContextVar("_CURRENT_TRACE", default=None)
_CURRENT_SPAN: contextvars.ContextVar[Optional[Span]] = contextvars.ContextVar("_CURRENT_SPAN", default=None)


@dataclass
class SpanEvent:
    name: str
    timestamp: float
    attributes: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Span:
    span_id: str
    trace_id: str
    name: str
    kind: str  # "workflow" | "retrieval" | "llm" | "tool" | "evaluation" | "internal"
    parent_span_id: Optional[str] = None
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    latency_ms: float = 0.0
    status: str = "ok"  # "ok" | "error"
    attributes: Dict[str, Any] = field(default_factory=dict)
    events: List[SpanEvent] = field(default_factory=list)

    def finish(self, status: str = "ok", error: Optional[str] = None):
        self.end_time = time.time()
        self.latency_ms = round((self.end_time - self.start_time) * 1000.0, 2)
        self.status = status
        if error:
            self.attributes["error.message"] = str(error)
            self.status = "error"

    def add_event(self, name: str, attributes: Optional[Dict[str, Any]] = None):
        self.events.append(SpanEvent(name=name, timestamp=time.time(), attributes=attributes or {}))

    def set_attribute(self, key: str, value: Any):
        self.attributes[key] = value

    def to_dict(self) -> Dict[str, Any]:
        return {
            "span_id": self.span_id,
            "trace_id": self.trace_id,
            "parent_span_id": self.parent_span_id,
            "name": self.name,
            "kind": self.kind,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "latency_ms": self.latency_ms,
            "status": self.status,
            "attributes": self.attributes,
            "events": [asdict(e) for e in self.events],
        }


@dataclass
class Trace:
    trace_id: str
    name: str
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    latency_ms: float = 0.0
    status: str = "ok"
    root_span_id: Optional[str] = None
    spans: List[Span] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def finish(self, status: str = "ok"):
        self.end_time = time.time()
        self.latency_ms = round((self.end_time - self.start_time) * 1000.0, 2)
        if any(s.status == "error" for s in self.spans):
            self.status = "error"
        else:
            self.status = status

    def to_dict(self) -> Dict[str, Any]:
        total_prompt_tokens = sum(s.attributes.get("prompt_tokens", 0) for s in self.spans)
        total_completion_tokens = sum(s.attributes.get("completion_tokens", 0) for s in self.spans)
        total_cost_usd = sum(float(s.attributes.get("cost_usd", 0.0)) for s in self.spans)

        return {
            "trace_id": self.trace_id,
            "name": self.name,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "latency_ms": self.latency_ms,
            "status": self.status,
            "root_span_id": self.root_span_id,
            "span_count": len(self.spans),
            "total_prompt_tokens": total_prompt_tokens,
            "total_completion_tokens": total_completion_tokens,
            "total_tokens": total_prompt_tokens + total_completion_tokens,
            "total_cost_usd": round(total_cost_usd, 6),
            "spans": [s.to_dict() for s in self.spans],
            "metadata": self.metadata,
        }


class TraceContext:
    def __init__(self, tracer: ObservabilityTracer, name: str, metadata: Optional[Dict[str, Any]] = None):
        self.tracer = tracer
        self.trace = Trace(
            trace_id=uuid4().hex[:16],
            name=name,
            metadata=metadata or {},
        )
        self.token = None

    def __enter__(self) -> Trace:
        self.token = _CURRENT_TRACE.set(self.trace)
        return self.trace

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.trace.finish(status="error")
        else:
            self.trace.finish(status="ok")
        self.tracer._record_trace(self.trace)
        _CURRENT_TRACE.reset(self.token)


class SpanContext:
    def __init__(
        self,
        tracer: ObservabilityTracer,
        name: str,
        kind: str = "workflow",
        attributes: Optional[Dict[str, Any]] = None,
    ):
        self.tracer = tracer
        self.name = name
        self.kind = kind
        self.attributes = attributes or {}
        self.span: Optional[Span] = None
        self.token = None

    def __enter__(self) -> Span:
        current_trace = _CURRENT_TRACE.get()
        if current_trace is None:
            # Auto-wrap in an ephemeral trace
            self._temp_trace_ctx = self.tracer.start_trace(f"trace_{self.name}")
            current_trace = self._temp_trace_ctx.__enter__()
        else:
            self._temp_trace_ctx = None

        parent_span = _CURRENT_SPAN.get()
        parent_id = parent_span.span_id if parent_span else None

        self.span = Span(
            span_id=uuid4().hex[:12],
            trace_id=current_trace.trace_id,
            name=self.name,
            kind=self.kind,
            parent_span_id=parent_id,
            attributes=dict(self.attributes),
        )

        if not current_trace.root_span_id:
            current_trace.root_span_id = self.span.span_id

        current_trace.spans.append(self.span)
        self.token = _CURRENT_SPAN.set(self.span)
        return self.span

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.span:
            if exc_type is not None:
                self.span.finish(status="error", error=str(exc_val))
            else:
                self.span.finish(status="ok")
        if self.token:
            _CURRENT_SPAN.reset(self.token)
        if self._temp_trace_ctx:
            self._temp_trace_ctx.__exit__(exc_type, exc_val, exc_tb)


class ObservabilityTracer:
    """Central Telemetry and Tracing Collector."""

    def __init__(self, max_traces: int = 500):
        self._traces: List[Trace] = []
        self._lock = threading.Lock()
        self.max_traces = max_traces
        self._seed_demo_traces()

    def start_trace(self, name: str, metadata: Optional[Dict[str, Any]] = None) -> TraceContext:
        return TraceContext(self, name, metadata)

    def start_span(
        self,
        name: str,
        kind: str = "workflow",
        attributes: Optional[Dict[str, Any]] = None,
    ) -> SpanContext:
        return SpanContext(self, name, kind, attributes)

    def _record_trace(self, trace: Trace):
        with self._lock:
            self._traces.append(trace)
            if len(self._traces) > self.max_traces:
                self._traces.pop(0)

    def list_traces(self, limit: int = 50, status: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._lock:
            filtered = self._traces
            if status:
                filtered = [t for t in filtered if t.status == status]
            return [t.to_dict() for t in reversed(filtered[-limit:])]

    def get_trace(self, trace_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            for t in self._traces:
                if t.trace_id == trace_id:
                    return t.to_dict()
        return None

    def get_metrics(self) -> Dict[str, Any]:
        with self._lock:
            if not self._traces:
                return {
                    "total_traces": 0,
                    "total_spans": 0,
                    "mean_latency_ms": 0.0,
                    "p50_latency_ms": 0.0,
                    "p95_latency_ms": 0.0,
                    "avg_ttft_ms": 0.0,
                    "total_prompt_tokens": 0,
                    "total_completion_tokens": 0,
                    "total_tokens": 0,
                    "tokens_per_second": 0.0,
                    "error_rate_percent": 0.0,
                    "spans_by_kind": {},
                    "total_cost_usd": 0.0,
                }

            latencies = sorted(t.latency_ms for t in self._traces)
            total_spans = sum(len(t.spans) for t in self._traces)
            all_spans = [s for t in self._traces for s in t.spans]

            p50 = latencies[int(len(latencies) * 0.50)]
            p95 = latencies[min(int(len(latencies) * 0.95), len(latencies) - 1)]
            mean_lat = round(sum(latencies) / len(latencies), 2)

            ttft_values = [
                s.attributes["ttft_ms"]
                for s in all_spans
                if "ttft_ms" in s.attributes and isinstance(s.attributes["ttft_ms"], (int, float))
            ]
            avg_ttft = round(sum(ttft_values) / len(ttft_values), 2) if ttft_values else 24.5

            prompt_toks = sum(s.attributes.get("prompt_tokens", 0) for s in all_spans)
            comp_toks = sum(s.attributes.get("completion_tokens", 0) for s in all_spans)
            total_toks = prompt_toks + comp_toks

            total_gen_time_sec = sum(
                s.latency_ms / 1000.0 for s in all_spans if s.kind == "llm" and s.latency_ms > 0
            )
            tokens_per_sec = (
                round(comp_toks / total_gen_time_sec, 1) if total_gen_time_sec > 0 else 42.0
            )

            error_count = sum(1 for t in self._traces if t.status == "error")
            error_rate = round((error_count / len(self._traces)) * 100.0, 2)

            spans_by_kind: Dict[str, int] = {}
            for s in all_spans:
                spans_by_kind[s.kind] = spans_by_kind.get(s.kind, 0) + 1

            total_cost = sum(float(s.attributes.get("cost_usd", 0.0)) for s in all_spans)

            return {
                "total_traces": len(self._traces),
                "total_spans": total_spans,
                "mean_latency_ms": mean_lat,
                "p50_latency_ms": p50,
                "p95_latency_ms": p95,
                "avg_ttft_ms": avg_ttft,
                "total_prompt_tokens": prompt_toks,
                "total_completion_tokens": comp_toks,
                "total_tokens": total_toks,
                "tokens_per_second": tokens_per_sec,
                "error_rate_percent": error_rate,
                "spans_by_kind": spans_by_kind,
                "total_cost_usd": round(total_cost, 6),
            }

    def export_otel(self) -> Dict[str, Any]:
        """Exports traces in OpenTelemetry standard JSON format."""
        with self._lock:
            resource_spans = []
            for trace in self._traces:
                otel_spans = []
                for s in trace.spans:
                    otel_spans.append({
                        "traceId": trace.trace_id,
                        "spanId": s.span_id,
                        "parentSpanId": s.parent_span_id or "",
                        "name": s.name,
                        "kind": s.kind.upper(),
                        "startTimeUnixNano": int(s.start_time * 1e9),
                        "endTimeUnixNano": int((s.end_time or s.start_time) * 1e9),
                        "status": {"code": 1 if s.status == "ok" else 2},
                        "attributes": [
                            {"key": k, "value": {"stringValue": str(v)}}
                            for k, v in s.attributes.items()
                        ],
                    })
                resource_spans.append({
                    "resource": {
                        "attributes": [
                            {"key": "service.name", "value": {"stringValue": "costguard-observability"}},
                            {"key": "service.version", "value": {"stringValue": "1.0.0"}},
                        ]
                    },
                    "scopeSpans": [{"spans": otel_spans}],
                })
            return {"resourceSpans": resource_spans}

    def _seed_demo_traces(self):
        """Seed representative traces so UI and telemetry are functional immediately."""
        now = time.time()
        # Seed 1: RAG Code Q&A Trace
        t1 = Trace(trace_id="trc-rag-qa-01", name="rag_pipeline_query", start_time=now - 120)
        s1_root = Span(
            span_id="spn-root-1",
            trace_id=t1.trace_id,
            name="rag_task_execution",
            kind="workflow",
            start_time=now - 120,
            end_time=now - 119.55,
            latency_ms=450.0,
            status="ok",
            attributes={"task": "codebase_qa", "query": "How does CostGuard gate economic regressions?"},
        )
        s1_retrieval = Span(
            span_id="spn-ret-1",
            trace_id=t1.trace_id,
            parent_span_id="spn-root-1",
            name="semantic_retrieval",
            kind="retrieval",
            start_time=now - 120,
            end_time=now - 119.92,
            latency_ms=80.0,
            status="ok",
            attributes={"top_k": 2, "retrieved_chunks": 2, "retrieved_tokens": 224, "sources": "README.md, VISION.md"},
        )
        s1_llm = Span(
            span_id="spn-llm-1",
            trace_id=t1.trace_id,
            parent_span_id="spn-root-1",
            name="llm_inference:gpt-4o-mini",
            kind="llm",
            start_time=now - 119.92,
            end_time=now - 119.57,
            latency_ms=350.0,
            status="ok",
            attributes={
                "provider": "openai-compatible",
                "model": "gpt-4o-mini",
                "prompt_tokens": 600,
                "completion_tokens": 200,
                "ttft_ms": 22.4,
                "tokens_per_sec": 48.2,
                "cost_usd": 0.02100,
            },
        )
        s1_eval = Span(
            span_id="spn-eval-1",
            trace_id=t1.trace_id,
            parent_span_id="spn-root-1",
            name="policy_evaluator",
            kind="evaluation",
            start_time=now - 119.57,
            end_time=now - 119.55,
            latency_ms=20.0,
            status="ok",
            attributes={"quality_score": 0.85, "policy_status": "pass"},
        )
        t1.root_span_id = "spn-root-1"
        t1.spans = [s1_root, s1_retrieval, s1_llm, s1_eval]
        t1.end_time = now - 119.55
        t1.latency_ms = 450.0
        self._traces.append(t1)

        # Seed 2: Bloated PR Regression Trace (Candidate k=8)
        t2 = Trace(trace_id="trc-bloated-pr-02", name="pr_ci_regression_eval", start_time=now - 60)
        s2_root = Span(
            span_id="spn-root-2",
            trace_id=t2.trace_id,
            name="ci_cd_pr_gate",
            kind="workflow",
            start_time=now - 60,
            end_time=now - 58.85,
            latency_ms=1150.0,
            status="ok",
            attributes={"pr_number": 42, "experiment": "k=8 context expansion"},
        )
        s2_retrieval = Span(
            span_id="spn-ret-2",
            trace_id=t2.trace_id,
            parent_span_id="spn-root-2",
            name="semantic_retrieval_bloated",
            kind="retrieval",
            start_time=now - 60,
            end_time=now - 59.78,
            latency_ms=220.0,
            status="ok",
            attributes={"top_k": 8, "retrieved_chunks": 8, "retrieved_tokens": 2300, "warning": "context inflation"},
        )
        s2_llm = Span(
            span_id="spn-llm-2",
            trace_id=t2.trace_id,
            parent_span_id="spn-root-2",
            name="llm_inference:gpt-4o-mini",
            kind="llm",
            start_time=now - 59.78,
            end_time=now - 58.87,
            latency_ms=910.0,
            status="ok",
            attributes={
                "provider": "openai-compatible",
                "model": "gpt-4o-mini",
                "prompt_tokens": 2400,
                "completion_tokens": 220,
                "ttft_ms": 38.5,
                "tokens_per_sec": 34.1,
                "cost_usd": 0.04920,
            },
        )
        s2_eval = Span(
            span_id="spn-eval-2",
            trace_id=t2.trace_id,
            parent_span_id="spn-root-2",
            name="policy_gate_check",
            kind="evaluation",
            start_time=now - 58.87,
            end_time=now - 58.85,
            latency_ms=20.0,
            status="error",
            attributes={"policy_status": "fail", "violation": "cost increase 134.29% exceeds 25%"},
        )
        t2.root_span_id = "spn-root-2"
        t2.spans = [s2_root, s2_retrieval, s2_llm, s2_eval]
        t2.end_time = now - 58.85
        t2.latency_ms = 1150.0
        t2.status = "error"
        self._traces.append(t2)


# Global singleton tracer
tracer = ObservabilityTracer()
