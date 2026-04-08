from __future__ import annotations

import fnmatch
import re
import shutil
import subprocess
from pathlib import Path


def ripgrep_search(
    pattern: str,
    path: Path,
    *,
    max_matches: int = 50,
    glob: str | None = None,
) -> tuple[int, str]:
    """Run ripgrep (or fall back to Python scan if rg is unavailable). Returns (exit_code, combined_output)."""
    rg = shutil.which("rg")
    if rg:
        cmd = [rg, "--line-number", "--max-count", str(max_matches), pattern, str(path)]
        if glob:
            cmd.insert(1, f"--glob={glob}")
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        out = (p.stdout or "") + (p.stderr or "")
        return p.returncode, out

    hits: list[str] = []
    count = 0
    try:
        rx = re.compile(pattern)
    except re.error:
        rx = None
    root = path if path.is_dir() else path.parent
    files: list[Path] = []
    if path.is_file():
        files = [path]
    else:
        for f in root.rglob("*"):
            if not f.is_file():
                continue
            if glob and not fnmatch.fnmatch(f.name, glob.lstrip("*/")):
                continue
            if f.suffix not in {".py", ".md", ".txt", ".toml", ".json"}:
                continue
            files.append(f)
    for f in files:
        try:
            lines = f.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        for i, line in enumerate(lines, start=1):
            matched = (rx.search(line) if rx else None) or (pattern in line)
            if matched:
                hits.append(f"{f}:{i}:{line}")
                count += 1
                if count >= max_matches:
                    return 0, "\n".join(hits)
    return 0, "\n".join(hits)
