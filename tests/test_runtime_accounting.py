from pathlib import Path

from layerfield_qaoa.config import RunConfig
from layerfield_qaoa.pipeline import run_benchmark
from layerfield_qaoa.results import TimingBreakdown
from layerfield_qaoa.simulator import _apply_job_queue_latency, _estimate_billed_seconds, _mock_calibration_metrics


class _FakeTranspiled:
    def count_ops(self):
        return {"ecr": 5, "swap": 2}

    def depth(self):
        return 10

    def size(self):
        return 20


def test_job_mode_adds_queue_latency() -> None:
    cfg = RunConfig(execution_billing_mode="job", job_queue_latency_seconds=3.0).normalized()
    timing = TimingBreakdown(total_seconds=1.0, execution_seconds=0.5)
    updated = _apply_job_queue_latency(timing, cfg)
    assert updated.queue_latency_seconds == 3.0
    assert updated.total_seconds == 4.0


def test_session_billing_uses_total_seconds() -> None:
    cfg = RunConfig(execution_billing_mode="session", qpu_billing_basis="execution").normalized()
    timing = TimingBreakdown(classical_overhead_seconds=2.0, execution_seconds=1.0, total_seconds=5.0)
    assert _estimate_billed_seconds(timing, cfg) == 5.0


def test_calibration_proxy_metrics_are_seeded_and_positive() -> None:
    cfg = RunConfig(calibration_aware_routing=True, transpile_topology="heavy_hex_5").normalized()
    mean_err, max_err, penalty = _mock_calibration_metrics(_FakeTranspiled(), cfg, "heavy_hex_5")
    assert mean_err > 0.0
    assert max_err >= mean_err
    assert penalty > 0.0


def test_trace_timing_breakdown_sums_consistently(tmp_path: Path) -> None:
    cfg = RunConfig(
        n_assets=6,
        budget=2,
        p_layers=1,
        evaluation_budget=4,
        n_init_points=2,
        shots=64,
        output_prefix=str(tmp_path / "timing"),
    ).normalized()
    payload = run_benchmark(cfg, verbose=False)
    for summary in payload["methods"].values():
        timing = summary["timing_totals"]
        subtotal = (
            float(timing["classical_overhead_seconds"])
            + float(timing["circuit_construction_seconds"])
            + float(timing["transpilation_seconds"])
            + float(timing["execution_seconds"])
            + float(timing["mitigation_seconds"])
            + float(timing["queue_latency_seconds"])
        )
        assert abs(subtotal - float(timing["total_seconds"])) < 1e-6
