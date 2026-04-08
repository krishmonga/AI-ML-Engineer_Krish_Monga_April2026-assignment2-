# bug_fix v2.3.0-canary — release notes (synthetic)

## Feature
- Rolling window aggregates for executive dashboard tiles (`bug_fix` library `0.1.0`).

## Known risks
- Cold-start paths for wide windows depend on correct partial-buffer semantics in `RollingMetrics`.
- Canary traffic may produce sparse samples; validate totals against raw minute series during ramp-up.
