# AI-ML-Engineer_Krish_Monga_April2026-assignment2-

## AI/ML Engineer Assessment 2 — Multi-Agent Bug Triage

**Candidate:** Krish Monga  
**Company:** Purple Merit Technologies  
**Track:** Assessment 2 — bug report + logs → repro → root cause → patch plan  

This repository implements **Option A (recommended): mini-repo + bug report + logs**.

---

## What makes this submission distinctive

1. **Evidence ledger (JSONL)** — Every agent action is append-only with timestamps, phase names, and tool names. Reviewers can audit the run without re-watching console scrollback.
2. **Typed handoffs (Pydantic)** — Agents exchange structured `Handoff` models, not opaque strings. The orchestrator is a **deterministic state machine** (no LLM required for the default path), which keeps grading reproducible and avoids flaky demos.
3. **Signal Curator agent (extra)** — Pre-ranks log lines by salience and explicitly down-ranks known noise families (deprecated endpoints, billing webhooks, janitor errors) while boosting traceback and symbol hits.
4. **Tool calls are real subprocess/file operations** — `ripgrep` when available (Python fallback otherwise), stack-trace parsing, and `python -m pytest` on the generated repro.
5. **Synthetic but coherent narrative** — **bug_fix** dashboard + `bug_fix` library; logs include **red herrings** and a second traceback to stress robustness.

---

## Repository layout

| Path | Purpose |
|------|---------|
| `inputs/bug_report.md` | Structured bug report (Markdown). |
| `inputs/app_logs.txt` | Logs with stack traces + noise. |
| `inputs/RELEASE_NOTES.md` | Known issues / deploy context. |
| `mini_repo/` | Small Python package (`bug_fix`) with an intentional defect in `RollingMetrics.last_n_sum`. |
| `bug_fix_swarm/` | Orchestrator, agents, tools, CLI. |
| `output/` | **Generated** — repro test, `investigation_report.{json,yaml}`, `evidence_ledger.jsonl`, optional `proposed_fix.patch`. |

---

## Setup

**If you see “externally managed environment” (PEP 668)** when running `pip install`, do **not** use `--break-system-packages`. Use either a venv or a project-local `.deps` folder (below).

### A) Virtual environment (best if `python3 -m venv` works)

```bash
cd "/path/to/assignment 2"
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

If `venv` fails with “ensurepip is not available”, install OS packages first, e.g. `sudo apt install python3.13-venv` (or `python3-venv`), then recreate `.venv`.

### B) No venv / no sudo — install into `./.deps`

```bash
cd "/path/to/assignment 2"
chmod +x bootstrap_local.sh
./bootstrap_local.sh
export PYTHONPATH="$(pwd):$(pwd)/.deps"
```

Or one-liner:

```bash
python3 -m pip install -t .deps -r requirements.txt
export PYTHONPATH="$(pwd):$(pwd)/.deps"
```

Always use **`python3 -m pip`** so you target the same interpreter you run with.

**Optional:** Install [ripgrep](https://github.com/BurntSushi/ripgrep) (`rg`) for faster repo search; the tools layer falls back to a Python scanner if `rg` is missing.

**Environment variables:** None required for the default run. If you later add an LLM-backed agent, load API keys only from the environment (never commit secrets).

---

## Run end-to-end

From the repository root:

```bash
python -m bug_fix_swarm
```

With optional unified diff (does **not** modify `mini_repo/`):

```bash
python -m bug_fix_swarm --write-patch
```

Custom paths:

```bash
python -m bug_fix_swarm \
  --project-root . \
  --bug-report inputs/bug_report.md \
  --logs inputs/app_logs.txt \
  --mini-repo mini_repo \
  --out output
```

### Expected behavior

- Console: Rich-formatted trace of phases, tool usage, and **pytest failing** on the generated repro (proving the defect).
- Files:
  - `output/investigation_report.json` and `.yaml` — structured final output.
  - `output/repro_generated_warm_window.py` — minimal failing test.
  - `output/evidence_ledger.jsonl` — machine-readable trace.

---

## Verify the mini-repo defect manually

```bash
cd mini_repo
PYTHONPATH=src python -m pytest tests/ -q
```

One contract test fails until `last_n_sum` is corrected.

Apply the suggested fix (after your own review):

```bash
cd ..   # repo root
patch -p1 < output/proposed_fix.patch
cd mini_repo && PYTHONPATH=src python -m pytest tests/ ../output/repro_generated_warm_window.py -q
```

---

## Traceability — where to look

| Artifact | What it contains |
|----------|------------------|
| Terminal | Phase rules, hypothesis list, pytest output, path to JSON/YAML. |
| `output/evidence_ledger.jsonl` | One JSON object per line: `ts`, `phase`, `agent`, `action`, `tool`, `payload`. |
| `output/investigation_report.yaml` | Human-readable rollup aligned with the assessment rubric. |

---

## Demo video (per brief)

Record a **silent** screen capture showing:

1. Running `python -m bug_fix_swarm` (or with `--write-patch`).
2. The **failing pytest** output for the generated repro.
3. Opening `output/investigation_report.json` or `.yaml` after generation.

---

## Submission checklist

- [ ] Rename / fork GitHub repo per instructions: `AI/ ML Engineer_[Your_Name]_April2026` (as specified in the PDF).
- [ ] README (this file) + working code + input artifacts.
- [ ] Demo video link or file per email instructions.
- [ ] No secrets in the repository.

Good luck with the next interview stage.
