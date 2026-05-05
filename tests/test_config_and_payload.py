from __future__ import annotations

from layerfield_qaoa.cli import build_parser
from layerfield_qaoa.config import RunConfig
from layerfield_qaoa.constants import PAYLOAD_SCHEMA_VERSION, RESEARCH_QUESTION
from layerfield_qaoa.reporting import build_run_payload
from layerfield_qaoa.results import EvaluationRecord, SearchTrace, TimingBreakdown


def _dummy_trace(method: str) -> SearchTrace:
    return SearchTrace(
        method=method,
        objective_history=[-1.0],
        raw_objective_history=[-1.0],
        best_valid_history=[-1.0],
        valid_ratio_history=[1.0],
        feasible_hit_history=[1.0],
        variance_history=[0.1],
        approx_gap_history=[0.0],
        evaluation_records=[
            EvaluationRecord(
                evaluation_index=0,
                params=[0.1, 0.2],
                objective=-1.0,
                raw_objective=-1.0,
                variance=0.1,
                observation_noise_variance=0.01,
                best_valid_energy=-1.0,
                valid_ratio=1.0,
                feasible_hit=True,
                approx_gap=0.0,
                timing={},
                backend_stats={},
            )
        ],
        elapsed_seconds=0.01,
        total_objective_calls=1,
        timing_totals=TimingBreakdown(total_seconds=0.01),
    )


class _DummyInstance:
    exact_feasible_energy = -1.0


class _LargeDummyInstance:
    exact_feasible_energy = None


def test_parser_defaults_follow_runspec() -> None:
    defaults = RunConfig()
    parser = build_parser()
    args = parser.parse_args([])
    assert args.n_assets == defaults.n_assets
    assert args.execution_mode == defaults.execution_mode
    assert args.bootstrap_resamples == defaults.bootstrap_resamples


def test_reporting_uses_shared_constants() -> None:
    cfg = RunConfig().normalized()
    payload = build_run_payload(cfg, _DummyInstance(), {"random": _dummy_trace("random")})
    assert payload["schema_version"] == PAYLOAD_SCHEMA_VERSION
    assert payload["project_positioning"]["research_question"] == RESEARCH_QUESTION


def test_payload_surfaces_missing_exact_reference() -> None:
    cfg = RunConfig(n_assets=16, budget=4, execution_mode="aer_sampler", backend_name="aer_simulator").normalized()
    payload = build_run_payload(cfg, _LargeDummyInstance(), {"random": _dummy_trace("random")})
    assert payload["exact_reference_available"] is False
    assert payload["exact_reference_warning"]
