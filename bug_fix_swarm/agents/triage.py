from __future__ import annotations

import re
from pathlib import Path

from bug_fix_swarm.schemas import BugSummary, TriageHandoff


def run_triage(bug_report_path: Path) -> TriageHandoff:
    raw = bug_report_path.read_text(encoding="utf-8")

    def section(name: str) -> str:
        m = re.search(rf"##\s*{re.escape(name)}\s*\n(.*?)(?=\n##|\Z)", raw, re.S | re.I)
        return (m.group(1).strip() if m else "").strip()

    title_body = section("Title")
    title = title_body.splitlines()[0].strip() if title_body else "Untitled bug"

    env_block = section("Environment")
    env: dict[str, str] = {}
    for line in env_block.splitlines():
        if "**" in line and ":" in line:
            k, _, rest = line.partition(":")
            env[k.strip().strip("*").strip()] = rest.strip().strip("*").strip()

    hints_block = section("Reproduction hints")
    hints = [h.strip().lstrip("- ") for h in hints_block.splitlines() if h.strip().startswith("-")]

    hypotheses: list[str] = []
    if "partial" in raw.lower() or "warm" in raw.lower():
        hypotheses.append("partial buffer / warm-up branch mishandles tail slice")
    if "RollingMetrics" in raw or "rolling" in raw.lower():
        hypotheses.append("RollingMetrics.last_n_sum incorrect when len(buffer) < n")

    sev_raw = section("Severity")
    if "P1" in sev_raw:
        severity = "P1"
    elif "P0" in sev_raw:
        severity = "P0"
    elif "P2" in sev_raw:
        severity = "P2"
    else:
        severity = "unknown"

    summary = BugSummary(
        symptoms=section("Description")[:800] or title,
        scope="bug_fix dashboard rolling aggregate API + bug_fix library",
        severity=severity,
    )

    return TriageHandoff(
        title=title,
        expected_behavior=section("Expected behavior"),
        actual_behavior=section("Actual behavior"),
        environment=env,
        hints=hints or ["Compare window aggregate vs raw minute list during ramp-up"],
        hypotheses=hypotheses,
        bug_summary=summary,
    )
