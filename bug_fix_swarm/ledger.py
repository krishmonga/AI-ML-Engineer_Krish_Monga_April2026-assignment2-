"""Append-only evidence ledger (JSONL) — traceability without relying on console order alone."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class EvidenceLedger:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

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
