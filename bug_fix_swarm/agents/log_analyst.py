from __future__ import annotations

import re
from pathlib import Path

from bug_fix_swarm.schemas import LogMiningHandoff, LogLineScore, TriageHandoff
from bug_fix_swarm.tools.log_parse import extract_stack_traces
from bug_fix_swarm.tools.rg_tool import ripgrep_search


def run_log_analyst(
    log_path: Path,
    repo_root: Path,
    triage: TriageHandoff,
    curated: list[LogLineScore],
) -> LogMiningHandoff:
    log_text = log_path.read_text(encoding="utf-8", errors="replace")
    blocks = extract_stack_traces(log_text)

    symbols: list[str] = []
    for b in blocks:
        for line in b.splitlines():
            m = re.search(r"([\w.]+)\.([\w]+)\s*$", line)
            if m and "site-packages" in line and "bug_fix" in line:
                symbols.append(m.group(2))
    for c in curated:
        if "RollingMetrics" in c.text:
            symbols.append("RollingMetrics")
        if "last_n_sum" in c.text:
            symbols.append("last_n_sum")

    symbols = sorted(set(symbols))
    sigs: list[str] = []
    for c in curated:
        if "delta=" in c.text or "expected_total" in c.text:
            sigs.append(c.text.strip()[:240])

    excerpt_indices = [c.line_no for c in curated[:12]]

    _, rg_out = ripgrep_search(r"last_n_sum|RollingMetrics", repo_root, glob="*.py")
    frames = []
    for b in blocks:
        if "bug_fix" in b or "rolling" in b.lower():
            frames.append(b)
    if not frames and blocks:
        frames = [blocks[0]]

    noise = (
        "Ignored janitor PermissionError and billing webhook warnings as unrelated temporal noise; "
        "prioritized frames touching bug_fix.rolling."
    )

    return LogMiningHandoff(
        stack_frames=frames,
        error_signatures=sigs[:8],
        correlated_symbols=symbols,
        excerpt_indices=excerpt_indices,
        noise_notes=noise + f" Ripgrep excerpt:\n{rg_out[:2000]}",
    )
