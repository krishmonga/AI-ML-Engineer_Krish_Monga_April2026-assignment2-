from __future__ import annotations

import re
from pathlib import Path

from bug_fix_swarm.schemas import LogLineScore, TriageHandoff


_TRACE_START = re.compile(r"^Traceback \(most recent call last\):")
_FRAME = re.compile(r'^\s*File "([^"]+)", line (\d+), in (\w+)')
_EXCEPTION = re.compile(r"^([A-Za-z][A-Za-z0-9_]+): (.+)$")


def extract_stack_traces(log_text: str) -> list[str]:
    """Parse log text into raw traceback blocks (preserves line order)."""
    lines = log_text.splitlines()
    blocks: list[str] = []
    i = 0
    while i < len(lines):
        if _TRACE_START.match(lines[i]):
            start = i
            i += 1
            while i < len(lines) and (lines[i].startswith(" ") or _FRAME.match(lines[i])):
                i += 1
            if i < len(lines) and _EXCEPTION.match(lines[i]):
                i += 1
            blocks.append("\n".join(lines[start:i]))
        else:
            i += 1
    return blocks


def score_log_lines(log_path: Path, triage: TriageHandoff) -> list[LogLineScore]:
    """Heuristic salience + red-herring tagging (Signal Curator tool path)."""
    text = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
    keywords = []
    for h in triage.hypotheses:
        keywords.extend(h.lower().split())
    for hint in triage.hints:
        keywords.extend(hint.lower().replace("/", " ").split())
    keywords.extend(
        w
        for w in triage.expected_behavior.lower().split()
        if len(w) > 4
    )
    noise_markers = (
        "deprecated",
        "urllib3",
        "stripe",
        "permission denied",
        "janitor",
        "nightly vacuum",
        "insecure",
        "shadow",
    )
    scores: list[LogLineScore] = []
    for idx, line in enumerate(text, start=1):
        low = line.lower()
        sal = 0.0
        tags: list[str] = []
        for kw in set(keywords):
            if kw and kw in low:
                sal += 1.2
        if "traceback" in low or "file \"/" in low:
            sal += 3.0
            tags.append("traceback")
        if "rollingmetrics" in low or "last_n_sum" in low:
            sal += 4.0
            tags.append("symbol")
        if "delta=" in low or "expected_total" in low:
            sal += 2.5
            tags.append("numeric_guard")
        herring = any(m in low for m in noise_markers)
        if herring:
            sal -= 1.5
            tags.append("noise_risk")
        scores.append(
            LogLineScore(
                line_no=idx,
                text=line,
                salience=max(0.0, sal),
                tags=tags,
                is_red_herring_risk=herring and "traceback" not in tags,
            )
        )
    scores.sort(key=lambda s: s.salience, reverse=True)
    return scores
