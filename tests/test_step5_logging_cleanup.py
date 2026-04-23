from __future__ import annotations

from pathlib import Path


def test_no_raw_prints_left_in_package() -> None:
    root = Path(__file__).resolve().parents[1] / "src" / "portfolio_qaoa_bench"
    offenders = []
    for path in root.glob("*.py"):
        if path.name == "logger.py":
            continue
        text = path.read_text(encoding="utf-8")
        if "print(" in text:
            offenders.append(path.name)
    assert offenders == []
