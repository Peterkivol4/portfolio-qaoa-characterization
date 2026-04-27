from __future__ import annotations

import csv
import json
from collections import defaultdict
from dataclasses import replace
from pathlib import Path
from typing import Any

import numpy as np

from .config import SpinRunConfig
from .p_layer_geometry import PLayerResolutionRecord, run_single_spin_instance
from .parameter_emergence import (
    ConfusionPair,
    angle_distance,
    minimum_p_for_threshold,
    parameter_confusion_score,
    parameter_transfer_loss,
)
from .spin_hamiltonian import regime_parameters


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys())
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _serialize_record(record: PLayerResolutionRecord) -> dict[str, Any]:
    payload = record.to_dict()
    payload["best_params"] = json.dumps(payload["best_params"])
    return payload


def load_resolution_records_csv(path: str | Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with Path(path).open(newline="") as handle:
        for row in csv.DictReader(handle):
            row = dict(row)
            row["best_params"] = json.loads(row.get("best_params", "[]"))
            for key in row:
                if key == "regime" or key == "optimizer":
                    continue
                if key == "best_params":
                    continue
                try:
                    if "." in row[key] or "e" in row[key].lower():
                        row[key] = float(row[key])
                    else:
                        row[key] = int(row[key])
                except Exception:
                    pass
            rows.append(row)
    return rows


def parse_thresholds(text: str) -> dict[str, float]:
    thresholds: dict[str, float] = {}
    for chunk in text.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        key, value = chunk.split("=", 1)
        thresholds[key.strip()] = float(value.strip())
    return thresholds


def _records_by_regime(records: list[PLayerResolutionRecord]) -> dict[str, list[PLayerResolutionRecord]]:
    grouped: dict[str, list[PLayerResolutionRecord]] = defaultdict(list)
    for record in records:
        grouped[record.regime].append(record)
    return grouped


def _resolution_summary(records: list[PLayerResolutionRecord], thresholds: dict[str, float]) -> dict[str, Any]:
    summary_rows: list[dict[str, Any]] = []
    for regime, regime_records in sorted(_records_by_regime(records).items()):
        payload_rows = [record.to_dict() for record in sorted(regime_records, key=lambda item: (item.p_layers, item.n_spins, item.seed))]
        summary_rows.append(
            {
                "regime": regime,
                "minimum_p_for_energy_recovery": minimum_p_for_threshold(payload_rows, "energy_error", thresholds["energy"]),
                "minimum_p_for_magnetization_recovery": minimum_p_for_threshold(payload_rows, "magnetization_z_error", thresholds["magnetization"]),
                "minimum_p_for_correlation_recovery": minimum_p_for_threshold(payload_rows, "nearest_neighbor_correlation_error", thresholds["correlation"]),
                "minimum_p_for_fidelity_recovery": minimum_p_for_threshold(payload_rows, "ground_state_fidelity", 1.0 - thresholds["fidelity"]),
            }
        )
    return {"thresholds": thresholds, "regime_thresholds": summary_rows}


def _resolution_report_text(records: list[PLayerResolutionRecord], summary: dict[str, Any]) -> str:
    lines = [
        "# p-Layer Physical Resolution Report",
        "",
        "QAOA depth is treated here as a physical resolution limit: the report tracks when energy, magnetization, correlations, and fidelity become recoverable as p increases.",
        "",
        "## Thresholds",
        "",
    ]
    for key, value in summary["thresholds"].items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Minimum p by regime", "", "| Regime | p for energy | p for magnetization | p for correlations | p for fidelity |", "|---|---:|---:|---:|---:|"])
    for row in summary["regime_thresholds"]:
        lines.append(
            f"| {row['regime']} | {row['minimum_p_for_energy_recovery']} | "
            f"{row['minimum_p_for_magnetization_recovery']} | "
            f"{row['minimum_p_for_correlation_recovery']} | "
            f"{row['minimum_p_for_fidelity_recovery']} |"
        )
    if records:
        mean_runtime = float(np.mean([record.runtime_seconds for record in records]))
        mean_energy_error = float(np.mean([record.energy_error for record in records]))
        lines.extend(
            [
                "",
                "## Aggregate trends",
                "",
                f"- Mean runtime per record: {mean_runtime:.4f} s",
                f"- Mean energy error across the sweep: {mean_energy_error:.4f}",
                f"- Records generated: {len(records)}",
            ]
        )
    return "\n".join(lines) + "\n"


def run_p_layer_sweep(
    *,
    base_cfg: SpinRunConfig,
    n_spins_values: list[int],
    p_values: list[int],
    j2_values: list[float],
    h_values: list[float],
    output_dir: str | Path,
    thresholds: dict[str, float] | None = None,
) -> dict[str, Any]:
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    thresholds = thresholds or {"energy": 0.02, "magnetization": 0.05, "correlation": 0.05, "fidelity": 0.10}
    records: list[PLayerResolutionRecord] = []

    for n_spins in n_spins_values:
        for p_layers in p_values:
            for j2 in j2_values:
                for transverse_field in h_values:
                    for seed_offset in range(base_cfg.seeds):
                        cfg = replace(
                            base_cfg,
                            n_spins=n_spins,
                            p_layers=p_layers,
                            j2=j2,
                            transverse_field=transverse_field,
                            seed=base_cfg.seed + seed_offset,
                        )
                        records.append(run_single_spin_instance(cfg))

    csv_rows = [_serialize_record(record) for record in records]
    _write_csv(out_dir / "p_resolution_records.csv", csv_rows)
    summary = _resolution_summary(records, thresholds)
    (out_dir / "p_resolution_summary.json").write_text(json.dumps(summary, indent=2))
    (out_dir / "p_resolution_report.md").write_text(_resolution_report_text(records, summary))
    return {
        "records_path": str(out_dir / "p_resolution_records.csv"),
        "summary_path": str(out_dir / "p_resolution_summary.json"),
        "report_path": str(out_dir / "p_resolution_report.md"),
        "record_count": len(records),
    }


def run_parameter_confusion_study(
    *,
    base_cfg: SpinRunConfig,
    n_spins: int,
    p_values: list[int],
    regimes: list[str],
    output_dir: str | Path,
) -> dict[str, Any]:
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    records_by_key: dict[tuple[str, int], PLayerResolutionRecord] = {}
    pair_rows: list[dict[str, Any]] = []

    for regime in regimes:
        preset = regime_parameters(regime)
        for p_layers in p_values:
            cfg = replace(
                base_cfg,
                n_spins=n_spins,
                p_layers=p_layers,
                regime=regime,
                j1=preset["j1"],
                j2=preset["j2"],
                transverse_field=preset["transverse_field"],
                disorder_strength=preset["disorder_strength"],
            )
            records_by_key[(regime, p_layers)] = run_single_spin_instance(cfg)

    regime_list = sorted(regimes)
    for p_layers in p_values:
        for idx, left_regime in enumerate(regime_list):
            for right_regime in regime_list[idx + 1 :]:
                left = records_by_key[(left_regime, p_layers)]
                right = records_by_key[(right_regime, p_layers)]
                left_obs = np.array(
                    [
                        left.energy_error,
                        left.magnetization_z_error,
                        left.magnetization_x_error,
                        left.nearest_neighbor_correlation_error,
                    ],
                    dtype=float,
                )
                right_obs = np.array(
                    [
                        right.energy_error,
                        right.magnetization_z_error,
                        right.magnetization_x_error,
                        right.nearest_neighbor_correlation_error,
                    ],
                    dtype=float,
                )
                pair = ConfusionPair(
                    left_regime=left_regime,
                    right_regime=right_regime,
                    p_layers=p_layers,
                    angle_distance=angle_distance(np.asarray(left.best_params), np.asarray(right.best_params)),
                    observable_distance=float(np.linalg.norm(left_obs - right_obs)),
                    transfer_loss=parameter_transfer_loss(np.asarray(left.best_params), np.asarray(right.best_params)),
                    confusion_score=parameter_confusion_score(
                        np.array([left.j1, left.j2, left.h, left.disorder_strength], dtype=float),
                        np.array([right.j1, right.j2, right.h, right.disorder_strength], dtype=float),
                        np.asarray(left.best_params),
                        np.asarray(right.best_params),
                        left_obs,
                        right_obs,
                    ),
                )
                pair_rows.append(
                    {
                        "left_regime": pair.left_regime,
                        "right_regime": pair.right_regime,
                        "p_layers": pair.p_layers,
                        "angle_distance": pair.angle_distance,
                        "observable_distance": pair.observable_distance,
                        "transfer_loss": pair.transfer_loss,
                        "confusion_score": pair.confusion_score,
                    }
                )

    _write_csv(out_dir / "parameter_confusion_records.csv", pair_rows)
    summary = {
        "max_confusion_score": max((row["confusion_score"] for row in pair_rows), default=0.0),
        "mean_confusion_score": float(np.mean([row["confusion_score"] for row in pair_rows])) if pair_rows else 0.0,
        "pairs": len(pair_rows),
    }
    (out_dir / "parameter_confusion_summary.json").write_text(json.dumps(summary, indent=2))
    lines = [
        "# Parameter Confusion Report",
        "",
        "Low-depth QAOA can make distinct Hamiltonians look too similar in angle space and observable space. This report quantifies that similarity directly.",
        "",
        f"- Pair count: {summary['pairs']}",
        f"- Mean confusion score: {summary['mean_confusion_score']:.4f}",
        f"- Max confusion score: {summary['max_confusion_score']:.4f}",
    ]
    (out_dir / "parameter_confusion_report.md").write_text("\n".join(lines) + "\n")
    return {
        "records_path": str(out_dir / "parameter_confusion_records.csv"),
        "summary_path": str(out_dir / "parameter_confusion_summary.json"),
        "report_path": str(out_dir / "parameter_confusion_report.md"),
    }


def write_resolution_cost_report(
    records: list[dict[str, Any]],
    *,
    thresholds: dict[str, float],
    output_dir: str | Path,
) -> dict[str, Any]:
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    regime_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        regime_groups[str(record["regime"])].append(record)

    summary_rows: list[dict[str, Any]] = []
    for regime, group in sorted(regime_groups.items()):
        energy_rows = [row for row in group if float(row["energy_error"]) <= thresholds["energy"]]
        corr_rows = [row for row in group if float(row["nearest_neighbor_correlation_error"]) <= thresholds["correlation"]]
        fid_rows = [row for row in group if float(row["ground_state_fidelity"]) >= 1.0 - thresholds["fidelity"]]
        summary_rows.append(
            {
                "regime": regime,
                "seconds_per_correlation_recovery": None if not corr_rows else float(np.mean([row["runtime_seconds"] for row in corr_rows])),
                "objective_calls_per_phase_recovery": None if not energy_rows else float(np.mean([row["objective_calls"] for row in energy_rows])),
                "shots_per_fidelity_threshold": None if not fid_rows else float(np.mean([row.get("objective_calls", 0) * row.get("parameter_count", 0) for row in fid_rows])),
            }
        )

    (out_dir / "resolution_cost_summary.json").write_text(json.dumps({"thresholds": thresholds, "rows": summary_rows}, indent=2))
    lines = [
        "# Resolution Cost Report",
        "",
        "This report interprets runtime as the cost of resolving physical structure rather than merely the cost of running an optimizer.",
        "",
        "## Thresholds",
    ]
    for key, value in thresholds.items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Regime-level cost", "", "| Regime | seconds_per_correlation_recovery | objective_calls_per_phase_recovery | shots_per_fidelity_threshold |", "|---|---:|---:|---:|"])
    for row in summary_rows:
        lines.append(
            f"| {row['regime']} | {row['seconds_per_correlation_recovery']} | "
            f"{row['objective_calls_per_phase_recovery']} | {row['shots_per_fidelity_threshold']} |"
        )
    (out_dir / "resolution_cost_report.md").write_text("\n".join(lines) + "\n")
    return {
        "summary_path": str(out_dir / "resolution_cost_summary.json"),
        "report_path": str(out_dir / "resolution_cost_report.md"),
    }


__all__ = [
    "load_resolution_records_csv",
    "parse_thresholds",
    "run_p_layer_sweep",
    "run_parameter_confusion_study",
    "write_resolution_cost_report",
]
