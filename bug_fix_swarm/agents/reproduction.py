from __future__ import annotations

from pathlib import Path

from bug_fix_swarm.schemas import LogMiningHandoff, ReproHandoff, TriageHandoff
from bug_fix_swarm.tools.pytest_runner import run_pytest


def write_and_run_repro(
    *,
    out_path: Path,
    mini_repo: Path,
    triage: TriageHandoff,
    mining: LogMiningHandoff,
) -> ReproHandoff:
    """Emit a minimal pytest file that fails on the warm-window defect, then execute it."""
    src = mini_repo / "src"
    body = f'''"""
Auto-generated minimal repro ({triage.title[:60]!r}).
Targets hypothesis: partial-window sum omits freshest sample.
Symbols from log mining: {", ".join(mining.correlated_symbols) or "RollingMetrics"}.
"""
from __future__ import annotations

import sys
from pathlib import Path

_MINI_SRC = Path(__file__).resolve().parents[1] / "mini_repo" / "src"
sys.path.insert(0, str(_MINI_SRC))

from bug_fix.rolling import RollingMetrics


def test_warm_window_must_sum_all_samples_when_underfilled():
    m = RollingMetrics(capacity=500)
    m.push(10.0)
    m.push(20.0)
    m.push(17.5)
    assert m.last_n_sum(5) == 47.5
'''
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(body, encoding="utf-8")

    project_root = mini_repo.parent
    code, out, err = run_pytest(out_path, cwd=project_root, extra_env={"PYTHONPATH": str(src)})
    return ReproHandoff(
        artifact_path=str(out_path),
        run_command=["python", "-m", "pytest", str(out_path), "-q", "--tb=short"],
        failed=code != 0,
        stdout=out,
        stderr=err,
        exit_code=code,
    )
