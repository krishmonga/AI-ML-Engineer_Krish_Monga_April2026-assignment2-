from __future__ import annotations

from pathlib import Path

from bug_fix_swarm.schemas import CriticHandoff, FixPlanHandoff, LogMiningHandoff, ReproHandoff


def run_critic(
    *,
    repro: ReproHandoff,
    plan: FixPlanHandoff,
    mining: LogMiningHandoff,
) -> CriticHandoff:
    art = Path(repro.artifact_path).read_text(encoding="utf-8") if repro.artifact_path else ""
    minimal_ok = repro.failed and "RollingMetrics" in art and "last_n_sum" in art
    fix_safe = (
        "sum(self._buf)" in plan.approach
        and plan.confidence >= 0.5
        and not any("ignore" in r.lower() for r in plan.risks[:1])
    )
    edge_cases = [
        "n == 0 must return 0.0",
        "Very large n relative to capacity — FIFO eviction interacts with window semantics",
        "Floating-point accumulation on long streams (precision vs finance use case)",
    ]
    more_evidence: list[str] = []
    if len(mining.stack_frames) > 1:
        more_evidence.append("Confirm which traceback corresponds to prod vs shadow pods in logs.")
    if plan.confidence < 0.7:
        more_evidence.append("Capture live heap dump of buffer contents at mismatch timestamp.")

    return CriticHandoff(
        repro_minimal_ok=bool(minimal_ok),
        fix_plan_safe=bool(fix_safe),
        edge_cases=edge_cases,
        requests_more_evidence=more_evidence,
    )
