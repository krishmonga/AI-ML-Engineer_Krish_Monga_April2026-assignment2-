from __future__ import annotations

from pathlib import Path

from bug_fix_swarm.schemas import LogLineScore, TriageHandoff
from bug_fix_swarm.tools.log_parse import score_log_lines


def run_signal_curator(log_path: Path, triage: TriageHandoff) -> tuple[list[LogLineScore], str]:
    """Rank log lines; down-rank known noise families while preserving traceback signal."""
    ranked = score_log_lines(log_path, triage)
    top_k = 12
    top = sorted(ranked, key=lambda x: x.salience, reverse=True)[:top_k]
    total_rows = len(log_path.read_text(encoding="utf-8", errors="replace").splitlines())
    note = (
        f"Top-{len(top)} lines by salience (of {total_rows} rows); "
        "noise families penalized; traceback and symbol hits dominate the head of the ranking."
    )
    return top, note
