"""Contract tests — one scenario exposes the warm-up window defect."""

from bug_fix.rolling import RollingMetrics


def test_full_buffer_window_matches_tail_sum() -> None:
    m = RollingMetrics(capacity=100)
    for x in (1.0, 2.0, 3.0, 4.0):
        m.push(x)
    assert m.last_n_sum(2) == 7.0


def test_warmup_window_should_include_all_samples() -> None:
    """Before ``n`` samples exist, the sum must include every pushed value."""
    m = RollingMetrics(capacity=500)
    m.push(10.0)
    m.push(20.0)
    m.push(17.5)
    # Request a wider window than filled; expected total is full buffer sum.
    assert m.last_n_sum(5) == 47.5
