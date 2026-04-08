from __future__ import annotations

import json
from pathlib import Path

import yaml
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from bug_fix_swarm.agents.critic import run_critic
from bug_fix_swarm.agents.fix_planner import run_fix_planner
from bug_fix_swarm.agents.log_analyst import run_log_analyst
from bug_fix_swarm.agents.reproduction import write_and_run_repro
from bug_fix_swarm.agents.signal_curator import run_signal_curator
from bug_fix_swarm.agents.triage import run_triage
from bug_fix_swarm.ledger import EvidenceLedger
from bug_fix_swarm.schemas import FinalReport, model_to_dict

_YAML_DUMP_KW = {
    "sort_keys": False,
    "allow_unicode": True,
    "default_flow_style": False,
    "width": 120,
}


class SwarmOrchestrator:
    """
    Deterministic state machine: TRIAGE → CURATE → LOG_MINING → REPRO → FIX_PLAN → CRITIC → REPORT.

    Coordinator merges critic feedback into confidence adjustment on the final artifact only
    (does not re-run agents — documents governance).
    """

    def __init__(
        self,
        *,
        project_root: Path,
        bug_report: Path,
        logs: Path,
        mini_repo: Path,
        out_dir: Path,
    ) -> None:
        self.project_root = project_root
        self.bug_report = bug_report
        self.logs = logs
        self.mini_repo = mini_repo
        self.out_dir = out_dir
        self.console = Console()
        self.ledger = EvidenceLedger(out_dir / "evidence_ledger.jsonl")

    def run(self, *, write_patch: bool = False) -> FinalReport:
        c = self.console
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.ledger.reset()

        c.print(Panel.fit("[bold]bug_fix_swarm[/] — Assessment 2 pipeline", style="cyan"))

        c.rule("[1] Triage Agent")
        triage = run_triage(self.bug_report)
        self.ledger.append(
            phase="TRIAGE",
            agent="TriageAgent",
            action="parse_bug_report",
            tool=None,
            payload=model_to_dict(triage),
        )
        c.print(f"  Hypotheses: {triage.hypotheses}")

        c.rule("[2] Signal Curator Agent (extra)")
        curated, cur_note = run_signal_curator(self.logs, triage)
        self.ledger.append(
            phase="CURATE",
            agent="SignalCuratorAgent",
            action="score_log_lines",
            tool="score_log_lines",
            payload={"note": cur_note, "top_lines": [model_to_dict(x) for x in curated[:8]]},
        )
        c.print(f"  {cur_note}")

        c.rule("[3] Log Analyst Agent")
        mining = run_log_analyst(self.logs, self.mini_repo, triage, curated)
        self.ledger.append(
            phase="LOG_MINING",
            agent="LogAnalystAgent",
            action="stack_traces_and_ripgrep",
            tool="extract_stack_traces+ripgrep_search",
            payload=model_to_dict(mining),
        )
        c.print(f"  Symbols: {mining.correlated_symbols}")

        c.rule("[4] Reproduction Agent")
        repro_path = self.out_dir / "repro_generated_warm_window.py"
        repro = write_and_run_repro(
            out_path=repro_path,
            mini_repo=self.mini_repo,
            triage=triage,
            mining=mining,
        )
        self.ledger.append(
            phase="REPRO",
            agent="ReproductionAgent",
            action="write_and_run_pytest",
            tool="run_pytest",
            payload=model_to_dict(repro),
        )
        c.print(Panel(repro.stdout + repro.stderr, title="pytest output", subtitle=f"exit={repro.exit_code}"))

        c.rule("[5] Fix Planner Agent")
        plan = run_fix_planner(mini_repo=self.mini_repo, triage=triage, mining=mining, repro=repro)
        self.ledger.append(
            phase="FIX_PLAN",
            agent="FixPlannerAgent",
            action="synthesize_patch_plan",
            tool="ripgrep_search",
            payload=model_to_dict(plan),
        )

        c.rule("[6] Reviewer / Critic Agent")
        critic = run_critic(repro=repro, plan=plan, mining=mining)
        self.ledger.append(
            phase="CRITIC",
            agent="ReviewerCriticAgent",
            action="challenge_plan",
            tool=None,
            payload=model_to_dict(critic),
        )

        conf = plan.confidence
        if not critic.repro_minimal_ok:
            conf *= 0.85
        if not critic.fix_plan_safe:
            conf *= 0.9

        report = FinalReport(
            bug_summary=triage.bug_summary,
            evidence={
                "log_excerpts": [curated[i].text for i in range(min(5, len(curated)))],
                "stack_trace_blocks": mining.stack_frames,
                "ripgrep_context_tail": mining.noise_notes[-1500:],
            },
            repro_steps=[
                f"Generated artifact: {repro.artifact_path}",
                "Run: " + " ".join(repro.run_command),
                "Expected before fix: failing assertion on warm-window total (47.5 vs actual).",
            ],
            repro_artifact_path=repro.artifact_path,
            root_cause_hypothesis=plan.root_cause,
            hypothesis_confidence=round(min(0.99, conf), 4),
            patch_plan={
                "files_modules_impacted": plan.files_impacted,
                "approach": plan.approach,
                "risks": plan.risks,
                "optional_unified_diff_hint": "In last_n_sum partial branch, replace sum(self._buf[:-1]) with sum(self._buf).",
            },
            validation_plan={
                "tests_to_add": [
                    "Property: for len(buf)<n, last_n_sum(n)==sum(buf).",
                    "Regression: repro test merged into mini_repo/tests.",
                ],
                "regression_checks": plan.validation_plan,
            },
            open_questions=critic.requests_more_evidence
            + [
                "Confirm canary vs stable log streams share identical bug_fix wheel hash.",
                "Verify finance export uses same code path as dashboard tile.",
            ],
        )

        self.ledger.append(
            phase="SYNTHESIS",
            agent="Coordinator",
            action="assemble_final_report",
            tool=None,
            payload=model_to_dict(report),
        )

        json_path = self.out_dir / "investigation_report.json"
        yaml_path = self.out_dir / "investigation_report.yaml"
        rd = model_to_dict(report)
        json_path.write_text(json.dumps(rd, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        yaml_path.write_text(yaml.safe_dump(rd, **_YAML_DUMP_KW), encoding="utf-8")

        ledger_json, ledger_yaml = self.ledger.export_json_and_yaml(self.out_dir)

        c.rule("[bold green]Structured outputs written")
        c.print("  Investigation report:")
        c.print(f"    JSON:  {json_path}")
        c.print(f"    YAML:  {yaml_path}")
        c.print("  Evidence ledger:")
        c.print(f"    JSONL: {self.ledger.path}  (append-only trace)")
        c.print(f"    JSON:  {ledger_json}  (full array)")
        c.print(f"    YAML:  {ledger_yaml}")

        tbl = Table(title="Handoff summary")
        tbl.add_column("Agent")
        tbl.add_column("Result")
        tbl.add_row("Triage", triage.title[:50] + "…")
        tbl.add_row("Log mining", f"{len(mining.stack_frames)} trace blocks")
        tbl.add_row("Repro", "FAIL (expected)" if repro.failed else "PASS (unexpected)")
        tbl.add_row("Critic", f"minimal_ok={critic.repro_minimal_ok} safe={critic.fix_plan_safe}")
        c.print(tbl)

        if write_patch:
            patch = self._proposed_unified_diff()
            patch_path = self.out_dir / "proposed_fix.patch"
            patch_path.write_text(patch, encoding="utf-8")
            c.print(f"  Patch: {patch_path}")

        return report

    def _proposed_unified_diff(self) -> str:
        """Single-file unified diff for the warm-window defect (optional deliverable)."""
        return """--- a/mini_repo/src/bug_fix/rolling.py
+++ b/mini_repo/src/bug_fix/rolling.py
@@ -19,8 +19,6 @@ class RollingMetrics:
         if n <= 0:
             return 0.0
         if len(self._buf) < n:
-            # Defect: drops the freshest sample when the buffer is still "warming up".
-            # Correct behavior: return sum(self._buf)
-            return sum(self._buf[:-1])
+            return sum(self._buf)
         return sum(self._buf[-n:])
"""
