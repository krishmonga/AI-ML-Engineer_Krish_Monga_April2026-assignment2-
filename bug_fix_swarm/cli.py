from __future__ import annotations

import argparse
from pathlib import Path

from bug_fix_swarm.orchestrator import SwarmOrchestrator


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    p = argparse.ArgumentParser(
        description="bug_fix_swarm — multi-agent bug triage (Assessment 2).",
    )
    p.add_argument("--project-root", type=Path, default=root, help="Workspace root (contains mini_repo/, inputs/).")
    p.add_argument("--bug-report", type=Path, default=None, help="Path to bug report markdown.")
    p.add_argument("--logs", type=Path, default=None, help="Path to application logs.")
    p.add_argument("--mini-repo", type=Path, default=None, help="Path to mini repository.")
    p.add_argument("--out", type=Path, default=None, help="Output directory for reports and repro.")
    p.add_argument(
        "--write-patch",
        action="store_true",
        help="Emit output/proposed_fix.patch (optional unified diff; does not modify mini_repo).",
    )
    args = p.parse_args()

    pr: Path = args.project_root
    bug = args.bug_report or pr / "inputs" / "bug_report.md"
    logs = args.logs or pr / "inputs" / "app_logs.txt"
    mini = args.mini_repo or pr / "mini_repo"
    out = args.out or pr / "output"

    orch = SwarmOrchestrator(
        project_root=pr,
        bug_report=bug,
        logs=logs,
        mini_repo=mini,
        out_dir=out,
    )
    orch.run(write_patch=args.write_patch)


if __name__ == "__main__":
    main()
