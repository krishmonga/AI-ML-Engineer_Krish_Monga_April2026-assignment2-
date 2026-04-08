from __future__ import annotations

from pathlib import Path

from bug_fix_swarm.schemas import FixPlanHandoff, LogMiningHandoff, ReproHandoff, TriageHandoff
from bug_fix_swarm.tools.rg_tool import ripgrep_search


def run_fix_planner(
    *,
    mini_repo: Path,
    triage: TriageHandoff,
    mining: LogMiningHandoff,
    repro: ReproHandoff,
) -> FixPlanHandoff:
    _, hits = ripgrep_search("def last_n_sum", mini_repo, glob="*.py")
    impacted: list[str] = []
    for line in hits.splitlines():
        if ":" in line:
            path_part = line.split(":", 2)[0]
            impacted.append(path_part)
    impacted = sorted(set(impacted)) or [str(mini_repo / "src/bug_fix/rolling.py")]

    root_cause = (
        "In last_n_sum, the branch for len(self._buf) < n uses sum(self._buf[:-1]), "
        "which drops the newest sample during buffer warm-up. The contract requires summing "
        "all buffered samples when fewer than n exist."
    )
    approach = (
        "Replace partial-buffer return with sum(self._buf). Add regression test for warm-up "
        "window (already embodied by the generated repro). Optionally add property test: "
        "for all n >= len(buf), last_n_sum(n) == sum(buf)."
    )
    risks = [
        "If any caller relied on the buggy omission (unlikely), changing semantics could alter dashboards briefly.",
        "Large buffers: sum() is O(k); acceptable for stated capacities.",
    ]
    validation = [
        "Run pytest on mini_repo/tests and the generated repro (expect pass after fix).",
        "Manual: simulate cold start, query window endpoint before buffer fills, compare to raw list sum.",
        "Add edge case tests: n==0, n==1, single push with large n.",
    ]
    confidence = 0.86 if repro.failed else 0.55

    if not repro.failed:
        validation.insert(0, "Repro did not fail — verify artifact paths and PYTHONPATH before merging hypothesis.")

    return FixPlanHandoff(
        root_cause=root_cause,
        confidence=confidence,
        files_impacted=impacted,
        approach=approach,
        risks=risks,
        validation_plan=validation,
    )
