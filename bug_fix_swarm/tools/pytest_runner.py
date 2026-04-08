from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def run_pytest(target: Path, *, cwd: Path | None = None, extra_env: dict[str, str] | None = None) -> tuple[int, str, str]:
    """Run pytest on a file or directory; returns (exit_code, stdout, stderr)."""
    env = {**os.environ, **(extra_env or {})}
    cmd = [sys.executable, "-m", "pytest", str(target), "-q", "--tb=short"]
    p = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
        timeout=120,
        env=env,
    )
    return p.returncode, p.stdout or "", p.stderr or ""
