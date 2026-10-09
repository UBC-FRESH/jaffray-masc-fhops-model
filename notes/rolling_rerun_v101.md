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

## Caveats found while preparing the re-run (2026-10-06)
- The "MIP baseline delivers 30913 m3" smoke value above is itself an artifact: HiGHS found no
  28-day ka_6 solution within 30 s, and FHOPS 1.0.0 `compute_kpis` reports full delivery for an
  empty plan (UBC-FRESH/fhops#108). The old 7896 m3 rolling MIP value came from the last window
  only (earlier windows hit the time limit and their incumbents were discarded; fixed by fhops#99).
- MILP plans replay with sequencing violations under playback (UBC-FRESH/fhops#109), which
  understates MILP plan quality; the re-run must wait for that fix.
- The runner now records `n_locked_assignments` and flags `empty_plan` / iteration warnings so
  failed solves cannot be mistaken for good plans.

## Design decision (2026-10-07, G. Paradis)
- MIP arm is **like-for-like** with Ch. 4 (option a): cold-start HiGHS, 1800 s per window, no SA seeding.
- FHOPS 1.0.1 rolling MILP windows use the earliness tie-break (two-stage: stage 2 maximises early
  production subject to the stage-1 objective; reported objective unchanged). Stage 2 is capped at
  `--mip-earliness-time-limit` (default 300 s) so a window cannot take 2 × 1800 s.
- Memory guard: size-40 MIP runs execute in a separate pool (`--large-mip-workers`, default 6).
- Runs are scored on the stitched plan; window statuses (`no_solution`, `skipped`, `empty`) are
  recorded per run so time-limited empty windows are visible, not hidden in totals.

## Feasibility check on FHOPS 1.0.1 (2026-10-09)
Environment: fresh venv `/tmp/opencode/venv-fhops101`, `fhops==1.0.1` from PyPI, highspy 1.15.1,
Pyomo 6.10.1, Python 3.12.3 (`data/output/rerun_v101_probe/environment.txt`). Host: 72 cores,
754 GB RAM, load ~2-3.
- Smoke (`data/output/rerun_v101_smoke/`, 10/10 ok, 3 min 22 s): ka_6 sub14/lock7 MIP now delivers
  30913 m3 with 0 sequencing violations (pre-fix: 7896 m3, 13 violations); all SA runs deliver the
  full 30913 m3. At the 30 s smoke limit the MIP baseline and sub28 MIP runs under-deliver
  (309.9 / 18617 / 27126 m3) because HiGHS is time-limited; expected, not a pipeline fault.
- Probe (`scripts/probe_mip_window_v101.py`, first window only, 1800 s + 300 s earliness, 1 thread;
  `data/output/rerun_v101_probe/`):

  | window | wall (s) | peak RSS (GB) | first window result |
  |---|---|---|---|
  | ka_40 sub14/lock7 | 2123 | 2.4 | **empty** incumbent (0 m3 planned) |
  | ni_40 sub14/lock7 | 2120 | 2.1 | 129777 m3 planned, 52471 m3 locked |
  | pg_40 sub14/lock7 | 2127 | 1.9 | 115023 m3 planned, 44714 m3 locked |
  | ni_40 sub112/lock7 | 2263 | 4.7 | **empty** incumbent (0 m3 planned) |

  Every size-40 window hits the time limit in both stages. Cold HiGHS returns empty plans on some
  14-day and on 112-day size-40 windows even at 1800 s (FHOPS 1.0.1 known limitation, now
  confirmed at 1800 s). Memory is not a constraint on this host (≤ 4.7 GB per run).
- Worst-case per-run MIP wall time (all windows time-limited, ~2120 s each): lock 1 = 112 windows
  ≈ 66 h; lock 7 = 16 ≈ 9.4 h; lock 14 = 8 ≈ 4–4.7 h; baseline ≈ 0.6 h. Critical path = the 36
  lock-1 MIP runs. With `--workers 70 --large-mip-workers 39` all 36 start at once, so the grid
  needs ≈ 66–70 h (≈ 3 days) in the worst case; with the default 6 large workers the size-40 MIP
  pool alone needs ≈ 6.5 days.

## Status
- [x] Runner written and smoke-tested on FHOPS 1.0.0 (pipeline only).
- [ ] Re-run full grid on FHOPS 1.0.1 (after fhops#91/#92 merge).
- [ ] Analysis: compare conclusions with Ch. 4; report to fhops-manuscript#20.
