"""Append-only evidence ledger (JSONL) plus structured JSON/YAML exports after each run."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


class EvidenceLedger:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def reset(self) -> None:
        """Clear JSONL so each pipeline run produces a fresh ledger (and matching JSON/YAML exports)."""
        self.path.write_text("", encoding="utf-8")

    def append(
        self,
        *,
        phase: str,
        agent: str,
        action: str,
        tool: str | None,
        payload: dict[str, Any],
    ) -> None:
        record = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "phase": phase,
            "agent": agent,
            "action": action,
            "tool": tool,
            "payload": payload,
        }
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    def read_all_records(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        out: list[dict[str, Any]] = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                out.append(json.loads(line))
        return out

    def export_json_and_yaml(self, out_dir: Path) -> tuple[Path, Path]:
        """Write the same ledger as a JSON array and a YAML document (in addition to .jsonl)."""
        entries = self.read_all_records()
        out_dir.mkdir(parents=True, exist_ok=True)
        json_path = out_dir / "evidence_ledger.json"
        yaml_path = out_dir / "evidence_ledger.yaml"
        json_path.write_text(
            json.dumps(entries, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        yaml_path.write_text(
            yaml.safe_dump(
                entries,
                sort_keys=False,
                allow_unicode=True,
                default_flow_style=False,
                width=120,
            ),
            encoding="utf-8",
        )
        return json_path, yaml_path
