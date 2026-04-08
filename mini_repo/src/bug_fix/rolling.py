"""Rolling window numeric aggregates (intentionally contains a subtle defect for Assessment 2)."""

from __future__ import annotations


class RollingMetrics:
    """Fixed-capacity FIFO buffer of samples; exposes window sums for dashboard tiles."""

    def __init__(self, capacity: int = 10_080) -> None:
        self._buf: list[float] = []
        self.capacity = max(1, capacity)

    def push(self, value: float) -> None:
        self._buf.append(float(value))
        if len(self._buf) > self.capacity:
            self._buf.pop(0)

    def last_n_sum(self, n: int) -> float:
        """Sum of the last ``n`` samples, or all samples if fewer than ``n`` exist."""
        if n <= 0:
            return 0.0
        if len(self._buf) < n:
            # Defect: drops the freshest sample when the buffer is still "warming up".
            # Correct behavior: return sum(self._buf)
            return sum(self._buf[:-1])
        return sum(self._buf[-n:])
