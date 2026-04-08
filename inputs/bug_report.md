# Bug Report: BF-4412 — bug_fix dashboard “warm window” totals drift low during ramp-up

## Title
Rolling revenue-equivalent totals under-count during the first minutes after deploy (warm-up window).

## Description
After deploying **bug_fix** `v2.3.0-canary`, the **15-minute rolling tile** on the executive dashboard reads **~20–37% below** the sum of per-minute ingest values shown in the raw drill-down table. The discrepancy **disappears** once enough minutes have accumulated (after the window is full). Finance noticed first because the tile feeds a reconciliation export.

## Expected behavior
For any requested window size `W`, if fewer than `W` samples exist, the API should return the **sum of all samples currently in the buffer** (the entire partial window).

## Actual behavior
While the buffer is still filling, the API returns a total that **omits the most recent sample** (the freshest minute). Once `len(samples) >= W`, totals match manual sums.

## Environment
- **Service:** `bug_fix-ingest` + `bug_fix` library `0.1.0`
- **Runtime:** Python 3.11.8
- **OS:** Linux (container `debian-bookworm-slim`)
- **Deploy:** Canary 12% → observed on `canary-az-b` only (same code path as stable)

## Reproduction hints
- Hit `GET /metrics/window?minutes=15` during the first ~3–8 minutes after a cold start or cache flush.
- Compare against `GET /metrics/minutes?limit=15` (non-aggregating list) — totals diverge until the buffer fills.
- Library symbol likely named `RollingMetrics` or similar; look for **partial buffer** / **warm-up** handling in window sum logic.

## Severity
**P1** — incorrect exec KPIs during incident windows (exactly when we look at these tiles most).
