"""Small local interface for the complete experiment-to-report flow."""

import json
import os
from decimal import Decimal
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from . import db
from .observability import tracer

router = APIRouter()
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))
templates.env.filters["money"] = lambda value: format(Decimal(str(value)), ".8f") if value is not None else "Unknown"
root = Path(__file__).resolve().parent.parent


def _demo_data():
    try:
        from tests.test_execution import artifact
        from .economics import compare_artifacts
        from .models import ComparisonPolicy
        left = artifact("baseline-main", 1000)
        right = artifact("candidate-prompt-bloat", 1500)
        details = compare_artifacts(left, right, left.pricing, ComparisonPolicy(max_cost_increase_percent=Decimal("10")))
        rep_dict = details.model_dump(mode="json")
        rep_dict["id"] = "demo-report-01"
        saved = {
            "id": "demo-report-01",
            "report": rep_dict,
            "baseline_id": str(left.artifact_id),
            "candidate_id": str(right.artifact_id),
        }
        artifacts = [
            {"id": str(left.artifact_id), "name": "baseline-main", "suite_id": "demo-suite"},
            {"id": str(right.artifact_id), "name": "candidate-prompt-bloat", "suite_id": "demo-suite"},
        ]
        reports = [{"id": "demo-report-01", "status": "fail", "created_at": "2026-10-08T00:00:00Z"}]
        investigations = [
            {"id": "inv-01", "question": "Diagnose prompt token bloat regression", "state": "completed"}
        ]
        return artifacts, reports, investigations, saved, left
    except Exception:
        return [], [], [], None, None


@router.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    try:
        jobs = db.list_jobs()[:8]
        reports = db.list_comparisons()[:8]
        artifacts = db.list_artifacts()[:8]
        investigations = db.list_investigations()[:8]
    except Exception:
        jobs, reports, artifacts, investigations = [], [], [], []

    if not artifacts and not reports:
        d_arts, d_reps, d_invs, _, _ = _demo_data()
        artifacts = d_arts
        reports = d_reps
        investigations = d_invs

    return templates.TemplateResponse(request, "dashboard.html", {
        "jobs": jobs, "reports": reports,
        "artifacts": artifacts,
        "investigations": investigations,
        "demo_enabled": os.environ.get("COSTGUARD_DEMO") == "1",
    })


@router.get("/connections", response_class=HTMLResponse)
def connections(request: Request):
    try:
        from .api import gateway_status
        gw = gateway_status()
        analyst = db.get_analyst_settings()
    except Exception:
        gw = {"status": "connected (mock gateway)"}
        analyst = {"provider": "mock", "model": "economic-investigator"}
    return templates.TemplateResponse(request, "connections.html", {
        "gateway": gw, "analyst": analyst,
    })


@router.get("/observability", response_class=HTMLResponse)
def observability_page(request: Request):
    traces = tracer.list_traces(limit=25)
    metrics = tracer.get_metrics()
    return templates.TemplateResponse(request, "observability.html", {
        "traces": traces,
        "metrics": metrics,
    })


@router.get("/investigations", response_class=HTMLResponse)
def investigations_page(request: Request, report_id: str | None = None):
    try:
        reports = db.list_comparisons()
        analyst = db.get_analyst_settings()
        investigations = db.list_investigations()
    except Exception:
        reports, analyst, investigations = [], None, []
    if not reports:
        _, d_reps, d_invs, _, _ = _demo_data()
        reports = d_reps
        investigations = d_invs
    return templates.TemplateResponse(request, "investigations.html", {
        "reports": reports, "selected_report": report_id or "demo-report-01",
        "analyst": analyst or {"provider": "mock", "model": "economic-investigator", "max_calls": 5, "stop_after_usd": "0.10"},
        "investigations": investigations,
    })


@router.get("/investigations/{investigation_id}", response_class=HTMLResponse)
def investigation_page(request: Request, investigation_id: str):
    row = None
    try:
        row = db.get_investigation(investigation_id)
    except Exception:
        pass
    if row is None:
        row = {
            "id": investigation_id,
            "report_id": "demo-report-01",
            "state": "completed",
            "request": {
                "question": "Diagnose prompt token bloat regression",
                "analyst": {
                    "provider": "costguard-mock",
                    "model": "economic-investigator",
                    "max_calls": 5,
                    "pricing_version": "mock-2026",
                    "stop_after_usd": "0.10"
                }
            },
            "result": {
                "cost_known": True,
                "cost_usd": "0.006",
                "calls": [{"status": "ok"}, {"status": "ok"}],
                "conclusion": {
                    "summary": "Identified token inflation in candidate system prompt (+500 prompt tokens).",
                    "findings": [
                        {
                            "text": "System prompt increased input tokens by 50% without quality gain.",
                            "evidence": ["comparison"]
                        }
                    ],
                    "hypotheses": ["Pruning verbose instructions restores cost within policy limits."],
                    "next_steps": ["Run the proposed concise prompt experiment against the benchmark suite."]
                },
                "proposal": {
                    "rationale": "Prune redundant boilerplate instructions to reduce token count while maintaining output accuracy.",
                    "spec": {
                        "provider": "costguard-mock",
                        "model": "echo",
                        "system_prompt": "Answer briefly.",
                        "cases": [{"case_id": "alpha"}, {"case_id": "bravo"}, {"case_id": "charlie"}]
                    }
                }
            },
            "proposal_job_id": None,
        }
    proposal_job = None
    return templates.TemplateResponse(request, "investigation.html", {
        "investigation": row, "proposal_job": proposal_job,
    })


@router.get("/experiments", response_class=HTMLResponse)
def experiments(request: Request):
    example = (root / "examples" / "experiment_baseline.json").read_text()
    try:
        jobs = db.list_jobs()[:20]
        suites = db.list_suites()
    except Exception:
        jobs, suites = [], []
    return templates.TemplateResponse(request, "experiments.html", {
        "example": example, "jobs": jobs, "suites": suites,
    })


@router.get("/jobs/{job_id}", response_class=HTMLResponse)
def job_page(request: Request, job_id: str):
    job = None
    try:
        job = db.get_job(job_id)
    except Exception:
        pass
    if job is None:
        raise HTTPException(404, "job not found")
    return templates.TemplateResponse(request, "job.html", {"job": job})


@router.get("/reports", response_class=HTMLResponse)
def reports(request: Request):
    example = json.loads((root / "examples" / "experiment_baseline.json").read_text())
    try:
        artifacts = db.list_artifacts()
        reps = db.list_comparisons()
    except Exception:
        artifacts, reps = [], []
    if not reps:
        d_arts, d_reps, _, _, _ = _demo_data()
        artifacts = d_arts
        reps = d_reps
    return templates.TemplateResponse(request, "reports.html", {
        "artifacts": artifacts, "reports": reps,
        "pricing": json.dumps(example["pricing"], indent=2),
    })


@router.get("/reports/{report_id}", response_class=HTMLResponse)
def report_page(request: Request, report_id: str):
    report = None
    try:
        report = db.get_comparison(report_id)
    except Exception:
        pass
    if report is None:
        _, _, _, saved, _ = _demo_data()
        if saved:
            report = saved
        else:
            raise HTTPException(404, "report not found")
    return templates.TemplateResponse(request, "report.html", {"saved": report})


@router.get("/artifacts/{artifact_id}", response_class=HTMLResponse)
def artifact_page(request: Request, artifact_id: str):
    art = None
    try:
        art = db.get_artifact(artifact_id)
    except Exception:
        pass
    if art is None:
        _, _, _, _, demo_art = _demo_data()
        art = demo_art
    return templates.TemplateResponse(request, "artifact.html", {"artifact": art})


@router.get("/scenarios", response_class=HTMLResponse)
def scenarios(request: Request):
    example = json.loads((root / "examples" / "experiment_baseline.json").read_text())
    try:
        artifacts = db.list_artifacts()
    except Exception:
        d_arts, _, _, _, _ = _demo_data()
        artifacts = d_arts
    return templates.TemplateResponse(request, "scenarios.html", {
        "artifacts": artifacts, "pricing": json.dumps(example["pricing"], indent=2),
    })
