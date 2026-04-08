"""
Auto-generated minimal repro ('Rolling revenue-equivalent totals under-count during the fir').
Targets hypothesis: partial-window sum omits freshest sample.
Symbols from log mining: RollingMetrics, last_n_sum.
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
