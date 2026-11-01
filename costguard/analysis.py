from decimal import Decimal, ROUND_HALF_UP

from .models import (
    CaseCostComparison,
    ComparisonReport,
    ComparisonRequest,
    MetricComparison,
    ModelCostComparison,
    MonthlyProjection,
    OutcomeEconomics,
    OutcomeMetrics,
    PolicyResult,
    Workload,
)

MILLION = Decimal("1000000")
MONEY_PRECISION = Decimal("0.00000001")
METRIC_PRECISION = Decimal("0.0001")
PERCENT_PRECISION = Decimal("0.01")


def _round(value: Decimal, precision: Decimal) -> Decimal:
    return value.quantize(precision, rounding=ROUND_HALF_UP)


def _compare(
    baseline: Decimal,
    candidate: Decimal,
    precision: Decimal,
) -> MetricComparison:
    delta = candidate - baseline
    if baseline == 0:
        delta_percent = Decimal("0") if candidate == 0 else None
    else:
        delta_percent = _round((delta / baseline) * 100, PERCENT_PRECISION)

    return MetricComparison(
        baseline=_round(baseline, precision),
        candidate=_round(candidate, precision),
        delta=_round(delta, precision),
        delta_percent=delta_percent,
    )


def _call_cost(call, prices) -> Decimal:
    price = prices[call.key]
    input_cost = Decimal(call.input_tokens) * price.input_per_million_usd / MILLION
    output_cost = Decimal(call.output_tokens) * price.output_per_million_usd / MILLION
    return input_cost + output_cost


def _workload_costs(workload: Workload, prices) -> dict[str, Decimal]:
    return {
        run.case_id: run.additional_charges_usd + sum(
            (_call_cost(call, prices) for call in run.calls),
            start=Decimal("0"),
        )
        for run in workload.runs
    }


def _mean(values: list[Decimal]) -> Decimal:
    return sum(values, start=Decimal("0")) / Decimal(len(values))


def _model_costs(workload: Workload, prices) -> dict[tuple[str, str], Decimal]:
    totals: dict[tuple[str, str], Decimal] = {}
    for run in workload.runs:
        for call in run.calls:
            totals[call.key] = totals.get(call.key, Decimal("0")) + _call_cost(
                call, prices
            )
    run_count = Decimal(len(workload.runs))
    return {key: total / run_count for key, total in totals.items()}


def _paired_quality(
    request: ComparisonRequest,
) -> tuple[MetricComparison | None, int]:
    baseline = {run.case_id: run for run in request.baseline.runs}
    candidate = {run.case_id: run for run in request.candidate.runs}
    paired = [
        (baseline[case_id].quality_score, candidate[case_id].quality_score)
        for case_id in sorted(baseline)
        if baseline[case_id].quality_score is not None
        and candidate[case_id].quality_score is not None
    ]
    if not paired:
        return None, 0
    return (
        _compare(
            _mean([baseline_score for baseline_score, _ in paired]),
            _mean([candidate_score for _, candidate_score in paired]),
            METRIC_PRECISION,
        ),
        len(paired),
    )


def _calculate_workload_outcome(workload: Workload, costs: dict[str, Decimal]) -> OutcomeMetrics:
    total_tasks = len(workload.runs)
    if total_tasks == 0:
        return OutcomeMetrics(
            total_tasks=0,
            successful_tasks=0,
            failed_tasks=0,
            success_rate_percent=Decimal("0.00"),
            cost_per_task_usd=Decimal("0.00000000"),
            cost_per_successful_task_usd=Decimal("0.00000000"),
            wasted_spend_usd=Decimal("0.00000000"),
            wasted_spend_percent=Decimal("0.00"),
            efficiency_score=Decimal("0.0000"),
        )

    total_cost = sum(costs.values(), Decimal("0"))
    successful_runs = [
        run for run in workload.runs
        if getattr(run, "status", "ok") == "ok" and (run.quality_score is None or run.quality_score >= Decimal("0.70"))
    ]
    successful_tasks = len(successful_runs)
    failed_tasks = total_tasks - successful_tasks

    success_rate_percent = _round((Decimal(successful_tasks) / Decimal(total_tasks)) * 100, PERCENT_PRECISION)
    cost_per_task = _round(total_cost / Decimal(total_tasks), MONEY_PRECISION)

    if successful_tasks > 0:
        cost_per_successful_task = _round(total_cost / Decimal(successful_tasks), MONEY_PRECISION)
    else:
        cost_per_successful_task = _round(total_cost, MONEY_PRECISION)

    failed_case_ids = {run.case_id for run in workload.runs if run not in successful_runs}
    wasted_spend = sum((costs[case_id] for case_id in failed_case_ids), Decimal("0"))
    wasted_spend_usd = _round(wasted_spend, MONEY_PRECISION)

    if total_cost > 0:
        wasted_spend_percent = _round((wasted_spend / total_cost) * 100, PERCENT_PRECISION)
    else:
        wasted_spend_percent = Decimal("0.00")

    if cost_per_successful_task > 0:
        efficiency_score = _round(Decimal("100") / cost_per_successful_task, METRIC_PRECISION)
    else:
        efficiency_score = Decimal("0.0000")

    return OutcomeMetrics(
        total_tasks=total_tasks,
        successful_tasks=successful_tasks,
        failed_tasks=failed_tasks,
        success_rate_percent=success_rate_percent,
        cost_per_task_usd=cost_per_task,
        cost_per_successful_task_usd=cost_per_successful_task,
        wasted_spend_usd=wasted_spend_usd,
        wasted_spend_percent=wasted_spend_percent,
        efficiency_score=efficiency_score,
    )


def _calculate_outcome_economics(
    baseline: Workload,
    candidate: Workload,
    baseline_costs: dict[str, Decimal],
    candidate_costs: dict[str, Decimal],
) -> OutcomeEconomics:
    base_out = _calculate_workload_outcome(baseline, baseline_costs)
    cand_out = _calculate_workload_outcome(candidate, candidate_costs)

    cost_per_success_comp = _compare(
        base_out.cost_per_successful_task_usd,
        cand_out.cost_per_successful_task_usd,
        MONEY_PRECISION,
    )
    sr_comp = _compare(
        base_out.success_rate_percent,
        cand_out.success_rate_percent,
        PERCENT_PRECISION,
    )
    waste_comp = _compare(
        base_out.wasted_spend_usd,
        cand_out.wasted_spend_usd,
        MONEY_PRECISION,
    )

    marginal = None
    delta_success = cand_out.successful_tasks - base_out.successful_tasks
    delta_total_cost = sum(candidate_costs.values(), Decimal("0")) - sum(baseline_costs.values(), Decimal("0"))
    if delta_success > 0 and delta_total_cost > 0:
        marginal = _round(delta_total_cost / Decimal(delta_success), MONEY_PRECISION)

    if cand_out.cost_per_successful_task_usd > base_out.cost_per_successful_task_usd:
        diff_pct = cost_per_success_comp.delta_percent or 0
        summary = (
            f"Candidate unit economics regressed: Effective Cost per Successful Outcome (ECSO) increased by "
            f"{diff_pct}% to ${cand_out.cost_per_successful_task_usd} / task "
            f"(Success Rate: {cand_out.success_rate_percent}% vs {base_out.success_rate_percent}%)."
        )
    elif cand_out.cost_per_successful_task_usd < base_out.cost_per_successful_task_usd:
        summary = (
            f"Candidate unit economics improved: Effective Cost per Successful Outcome (ECSO) decreased to "
            f"${cand_out.cost_per_successful_task_usd} / task with {cand_out.success_rate_percent}% success rate."
        )
    else:
        summary = (
            f"Unit economics parity: Both workloads deliver successful outcomes at "
            f"${cand_out.cost_per_successful_task_usd} / task."
        )

    return OutcomeEconomics(
        baseline=base_out,
        candidate=cand_out,
        cost_per_successful_task=cost_per_success_comp,
        success_rate=sr_comp,
        wasted_spend=waste_comp,
        marginal_cost_per_success_usd=marginal,
        summary=summary,
    )


def _policy_result(
    request: ComparisonRequest,
    baseline_cost: Decimal,
    candidate_cost: Decimal,
    quality: MetricComparison | None,
    outcome: OutcomeEconomics | None = None,
) -> PolicyResult:
    policy = request.policy
    if policy is None or not any(value is not None for value in policy.model_dump().values()):
        return PolicyResult(status="not_evaluated", violations=[])

    violations: list[str] = []
    if policy.max_cost_increase_percent is not None:
        if baseline_cost == 0 and candidate_cost > 0:
            violations.append("cost increased from a zero-cost baseline")
        elif baseline_cost != 0:
            increase_percent = (
                (candidate_cost - baseline_cost) / baseline_cost
            ) * 100
            if increase_percent > policy.max_cost_increase_percent:
                displayed_increase = _round(increase_percent, PERCENT_PRECISION)
                violations.append(
                    f"cost increase {displayed_increase}% exceeds "
                    f"{policy.max_cost_increase_percent}%"
                )

    if (
        policy.max_candidate_cost_per_request_usd is not None
        and candidate_cost > policy.max_candidate_cost_per_request_usd
    ):
        displayed_cost = _round(candidate_cost, MONEY_PRECISION)
        violations.append(
            f"candidate cost ${displayed_cost} exceeds "
            f"${policy.max_candidate_cost_per_request_usd} per request"
        )

    if policy.max_candidate_cost_per_successful_task_usd is not None and outcome is not None:
        if outcome.candidate.cost_per_successful_task_usd > policy.max_candidate_cost_per_successful_task_usd:
            violations.append(
                f"candidate cost per successful task ${outcome.candidate.cost_per_successful_task_usd} "
                f"exceeds ${policy.max_candidate_cost_per_successful_task_usd}"
            )

    if policy.min_candidate_task_success_rate_percent is not None and outcome is not None:
        if outcome.candidate.success_rate_percent < policy.min_candidate_task_success_rate_percent:
            violations.append(
                f"candidate task success rate {outcome.candidate.success_rate_percent}% "
                f"is below required {policy.min_candidate_task_success_rate_percent}%"
            )

    if policy.max_candidate_wasted_spend_percent is not None and outcome is not None:
        if outcome.candidate.wasted_spend_percent > policy.max_candidate_wasted_spend_percent:
            violations.append(
                f"candidate wasted spend {outcome.candidate.wasted_spend_percent}% "
                f"exceeds {policy.max_candidate_wasted_spend_percent}%"
            )

    unknowns: list[str] = []
    if any(getattr(policy, field) is not None for field in (
        "max_candidate_mean_latency_ms", "max_candidate_model_calls_per_case",
        "max_candidate_retries_per_case", "max_candidate_tool_steps_per_case",
        "max_candidate_agent_steps_per_case",
    )):
        unknowns.append("execution-behavior policies require versioned execution artifacts")
    if policy.max_monthly_cost_usd is not None:
        if request.monthly_requests is None:
            unknowns.append("monthly requests are required for the monthly cost policy")
        elif candidate_cost * request.monthly_requests > policy.max_monthly_cost_usd:
            violations.append("projected monthly cost exceeds the configured limit")
    if policy.min_candidate_quality_score is not None:
        if quality is None:
            unknowns.append("paired quality scores are required for the quality policy")
        elif quality.candidate < policy.min_candidate_quality_score:
            violations.append("candidate quality score is below the configured minimum")

    return PolicyResult(
        status="fail" if violations else "inconclusive" if unknowns else "pass",
        violations=violations,
        unknowns=unknowns,
    )


def compare_workloads(request: ComparisonRequest) -> ComparisonReport:
    prices = request.pricing.as_map()
    baseline_costs = _workload_costs(request.baseline, prices)
    candidate_costs = _workload_costs(request.candidate, prices)

    baseline_mean_cost = _mean(list(baseline_costs.values()))
    candidate_mean_cost = _mean(list(candidate_costs.values()))
    cost_comparison = _compare(
        baseline_mean_cost,
        candidate_mean_cost,
        MONEY_PRECISION,
    )

    baseline_latency = _mean([run.latency_ms for run in request.baseline.runs])
    candidate_latency = _mean([run.latency_ms for run in request.candidate.runs])

    baseline_models = _model_costs(request.baseline, prices)
    candidate_models = _model_costs(request.candidate, prices)
    model_costs = [
        ModelCostComparison(
            provider=provider,
            model=model,
            cost_per_request_usd=_compare(
                baseline_models.get((provider, model), Decimal("0")),
                candidate_models.get((provider, model), Decimal("0")),
                MONEY_PRECISION,
            ),
        )
        for provider, model in sorted(set(baseline_models) | set(candidate_models))
    ]
    model_costs.sort(
        key=lambda item: (
            -item.cost_per_request_usd.delta,
            item.provider,
            item.model,
        )
    )

    case_costs = [
        CaseCostComparison(
            case_id=case_id,
            cost_usd=_compare(
                baseline_costs[case_id],
                candidate_costs[case_id],
                MONEY_PRECISION,
            ),
        )
        for case_id in baseline_costs
    ]
    case_costs.sort(key=lambda item: (-item.cost_usd.delta, item.case_id))

    monthly_projection = None
    if request.monthly_requests is not None:
        monthly_projection = MonthlyProjection(
            requests=request.monthly_requests,
            cost_usd=_compare(
                baseline_mean_cost * request.monthly_requests,
                candidate_mean_cost * request.monthly_requests,
                MONEY_PRECISION,
            ),
        )

    quality, quality_cases_compared = _paired_quality(request)
    outcome_economics = _calculate_outcome_economics(
        request.baseline, request.candidate, baseline_costs, candidate_costs
    )

    assumptions = [
        "Every workload case has equal weight.",
        "Costs use the supplied pricing catalog and observed token counts.",
        "Outcome economics evaluates effective cost per successful task (ECSO) and wasted spend.",
    ]
    if quality is not None:
        assumptions.append(
            "Quality compares only cases scored in both baseline and candidate."
        )
    if request.monthly_requests is not None:
        assumptions.append(
            "Monthly projection assumes the compared workload mix is representative."
        )

    return ComparisonReport(
        baseline=request.baseline.name,
        candidate=request.candidate.name,
        cases_compared=len(request.baseline.runs),
        pricing_version=request.pricing.version,
        cost_per_request_usd=cost_comparison,
        mean_latency_ms=_compare(
            baseline_latency,
            candidate_latency,
            METRIC_PRECISION,
        ),
        quality_score=quality,
        quality_cases_compared=quality_cases_compared,
        case_costs=case_costs,
        model_costs=model_costs,
        monthly_projection=monthly_projection,
        policy=_policy_result(
            request, baseline_mean_cost, candidate_mean_cost, quality, outcome_economics
        ),
        assumptions=assumptions,
        outcome_economics=outcome_economics,
    )
