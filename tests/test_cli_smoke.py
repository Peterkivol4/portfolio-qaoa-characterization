from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_cli_smoke_test_subprocess(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    env = {
        **__import__("os").environ,
        "PYTHONPATH": str(root / "src"),
    }
    result = subprocess.run(
        [sys.executable, "-m", "portfolio_qaoa_bench.cli", "--test"],
        cwd=root,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    assert "Smoke test passed." in result.stdout
