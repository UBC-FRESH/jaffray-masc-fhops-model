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

### Gurobi vs HiGHS (2026-10-09)
Gurobi 13.0.3 (gurobipy, academic named-user licence on jupyterhub03, expires 2027-10-09), venv
`/tmp/opencode/venv-fhops101-grb` (`data/output/rerun_v101_probe/gurobi/environment.txt`). Same
probe and settings (1 thread, 1800 s + 300 s earliness). Planned / locked = m3 delivered in the
window plan / in its lock span (7 d).

| window | HiGHS planned / locked | Gurobi planned / locked | HiGHS RSS | Gurobi RSS |
|---|---|---|---|---|
| ni_18 sub14 | 73473 / 32291 | 75820 / 34616 | 1.0 GB | 0.4 GB |
| ni_18 sub56 | **0 / 0 (empty)** | 247612 / 8811 | 1.7 GB | 1.1 GB |
| ka_40 sub14 | **0 / 0 (empty)** | 110337 / 40211 | 2.4 GB | 0.7 GB |
| ni_40 sub14 | 129777 / 52471 | 133996 / 55842 | 2.1 GB | 0.9 GB |
| pg_40 sub14 | 115023 / 44714 | 123064 / 43220 | 1.9 GB | 0.7 GB |
| ni_40 sub112 | **0 / 0 (empty)** | 870778 / 1341 | 4.7 GB | 3.1 GB |

- Both solvers hit the time limit in both stages on every probed window, so the wall time per window
  is the same (~2100 s) and the grid estimate does not change.
- Gurobi finds a non-empty incumbent on all 6 windows; HiGHS returns empty plans on 3 of 6. Where both
  have incumbents, Gurobi's objective is 0.8–1.5 % better.
- ni_40 sub112 on Gurobi plans 870778 m3 but locks only 1341 m3 in the first week. Stage 2
  (earliness) is time-limited, so work is deferred past the lock span. Expect long-window,
  short-lock runs to under-deliver for solver-time reasons.
- Smoke on Gurobi (`data/output/rerun_v101_gurobi_smoke/`): every ka_6 MIP run delivers 30913 m3 at
  30 s/window (HiGHS: 310–30913 m3). Two runs replay with 1 `missing_prereq` violation caused by
  tiny-production rows (≤ 1.7e-4 m3). Reported on UBC-FRESH/fhops#157 (MINOR-N2 also occurs in stage
  1 with Gurobi).
- The harness now takes `--mip-solver {highs,gurobi}`. A non-HiGHS backend writes to
  `data/output/rerun_v101_<solver>/`, and the backend is recorded per run (`mip_solver`).

### Time-limit calibration (2026-10-10)
Gurobi 13.0.3, 1 thread, first window only, stage 1 limit 7200 s and stage 2 (earliness) limit
1800 s, 8 windows run concurrently. Logs and parsed trajectories are in `data/output/rerun_v101_calib/`
(`scripts/calib_trajectory_v101.py` → `trajectory_checkpoints.csv`, `stage_totals.csv`).

Stage 1: shortfall of the incumbent at time t versus the 7200 s incumbent (%), and the gap at 1800 s.

| window | 300 s | 900 s | 1800 s | 3600 s | gap @1800 s | gap @7200 s |
|---|---|---|---|---|---|---|
| ka_40 sub14 | 1.37 | 0.89 | 0.39 | 0.09 | 5.19 | 4.82 |
| ni_40 sub14 | 0.18 | 0.01 | 0.01 | 0.01 | 0.58 | 0.57 |
| pg_40 sub14 | 0.12 | 0.00 | 0.00 | 0.00 | 0.80 | 0.79 |
| ni_40 sub112 | none | none | 1.11 | 0.05 | 3.30 | 2.16 |
| ni_18 sub14 | 0.31 | 0.28 | 0.12 | 0.03 | 0.39 | 0.27 |
| ni_18 sub56 | 0.01 | 0.00 | 0.00 | 0.00 | 0.82 | 0.82 |
| pg_18 sub28 | 0.48 | 0.20 | 0.10 | 0.01 | 1.33 | 1.23 |
| ka_6 sub112 | optimal in 2.8 s | | | | 0 | 0 |

- At 1800 s stage 1 is on a plateau: the incumbent is within 0.4 % of the 7200 s value except on the
  112-day size-40 window (1.1 %). The remaining gap (0.4–5 %) comes from the bound and barely
  closes by 7200 s.
- 1800 s is close to the minimum for the largest windows. On ni_40 sub112 the root LP takes 646 s
  (470 work units) and the first non-empty incumbent appears at 1354 s; before that only the empty
  plan exists.
- Work rate: 0.9–1.2 work units/s (0.63 on ni_40 sub112) with 8 concurrent jobs on 36 physical
  cores. With 70 workers (hyperthreads) the rate per process will be lower, and the 112-day size-40
  windows risk returning empty plans again. Recommendation: at most about 36 concurrent MIP
  workers.
- Stage 2 (earliness) is far from converged: the gap at 1800 s is 10–85 %. The shortfall versus the
  1800 s value is 0–23 % at 300 s and 0–3 % at 900 s (pg_40 sub14: 14.5 %). Locked volume in the first
  week, stage 2 at 300 s (2026-10-09 probe, stage 1 at 1800 s) versus 1800 s (this run, stage 1 at
  7200 s; confounded): ni_40 sub112 1341 → 12658 m3; ni_18 sub56 8811 → 18892 m3. Sub14 windows
  change by about 5 % or less. A 300 s earliness limit therefore understates what long windows lock
  in their first days.
- FHOPS passes the same `solver_options` to both stages, so a Gurobi `WorkLimit` cannot be set per
  stage without an FHOPS change. A per-stage deterministic limit would need an FHOPS extension
  (candidate for 1.0.2).
- The harness now writes `runs/<run_id>.gurobi.log` for Gurobi MIP runs.

## Design decision (2026-10-10, G. Paradis): option B
This supersedes the 2026-10-07 MIP settings.
- **MIP arm:** Gurobi 13.0.3, cold start, 1 thread, stage 1 limited to 1800 s per window, earliness
  stage 2 limited to **900 s**. The reasons are in the calibration above: Gurobi avoids empty
  incumbents, 1800 s sits on the stage-1 plateau, and 300 s understates what long windows lock early.
- **Concurrency:** 36 MIP workers (one per physical core) and 34 SA workers in a separate pool on the
  remaining logical cores. SA is iteration-bounded, so load does not change its result.
- Worst-case wall time is about 4.5 days. All 36 lock-1 MIP runs start first, and each is at most
  112 × 2700 s ≈ 85 h.
- Output: `data/output/rerun_v101_gurobi/`. The HiGHS probe results remain the open-source
  reference.

## Status
- [x] Runner written and smoke-tested on FHOPS 1.0.0 (pipeline only).
- [ ] Re-run full grid on FHOPS 1.0.1 (launched 2026-10-10, option B).
- [ ] Analysis: compare conclusions with Ch. 4; report to fhops-manuscript#20.
