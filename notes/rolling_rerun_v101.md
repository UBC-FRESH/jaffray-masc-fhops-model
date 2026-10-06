# Rolling-horizon re-run on FHOPS 1.0.1 (issue #1)

## Why
FHOPS <= 1.0.0 (this project used editable `1.0.0a2`) carried no state between rolling-horizon
windows (UBC-FRESH/fhops#90/#92): each window re-planned full block volume, staged inter-role
inventory and role progress reset to zero, boundary moves were free, user locks were dropped, and
blackouts were not rebased. The Chapter 4 analysis (`scripts/json_processing_to_summary.py`) also
scored runs by the **last window's objective**, which is not the value of the stitched plan.

## Method
- Runner: `scripts/rolling_rerun_v101.py` (resumable; one process per run; HiGHS 1 thread).
- Same grid as Ch. 4: {pg, ka, ni} x {6, 18, 40} x theta {2, 4, 8, 16} wk x lock {1, 7, 14} d x
  {SA 500 iters seed 42, MIP HiGHS 1800 s/window} = 216 runs, plus 18 full-horizon baselines
  (master = sub = lock = 112 d).
- Metric: stitched locked plan replayed against the base scenario with deterministic playback
  (`compute_kpis`): delivered volume, remaining volume, mobilisation cost, sequencing violations;
  compared with the same-solver full-horizon baseline. `last_window_objective` is kept only for
  comparison with Ch. 4.

## Pre-fix smoke evidence (FHOPS 1.0.0, 2026-10-06)
`data/output/rerun_smoke_prefix_v100/` (ka_6, master 28 d, SA 50 iters, MIP 30 s/window):
- ka_6 MIP baseline delivers 30913 m3; sub14/lock7 MIP delivers only 7896 m3 with 13 sequencing
  violations (window restarts the role chain with zero staged inventory).
- SA lock7 delivers 13506 m3 vs 30380 m3 baseline.
This indicates the Ch. 4 lock-span effect is at least partly an artifact of the missing carry-forward.

## Status
- [x] Runner written and smoke-tested on FHOPS 1.0.0 (pipeline only).
- [ ] Re-run full grid on FHOPS 1.0.1 (after fhops#91/#92 merge).
- [ ] Analysis: compare conclusions with Ch. 4; report to fhops-manuscript#20.
