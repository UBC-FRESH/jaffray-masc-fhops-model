# Jaffray MASc FHOPS Modelling Inputs

This workspace assembles the nine MASc case-study scenarios (ka/ni/pg × 6/18/40)
for the FHOPS modelling paper. Source block inputs live under
`data/input/blocks/<AREA>_<SIZE>/blocks.csv`, while FHOPS-ready scenario bundles
are generated into `data/input/scenarios/<area>_<size>/`.

## Generate scenarios (reproducible)

```
python scripts/generate_case_study_inputs.py --validate
```

Notes:
- The generator expects a sibling `fhops` repo at `../fhops`. Override with
  `--fhops-root /path/to/fhops` or `FHOPS_ROOT=/path/to/fhops`.
- The script uses FHOPS productivity helpers (requires FHOPS dependencies such
  as `numpy` and `pandas`).
- A bundle manifest is written to `data/input/scenarios/manifest.yaml`, and each
  scenario has its own `manifest.yaml`.
- Shift schedule assumes 3 shifts/day × 8 hours/shift, 7 days/week (continuous).

## Output structure

Each scenario bundle contains (paths shown relative to the repo root):
- `data/input/scenarios/<area>_<size>/scenario.yaml` — FHOPS scenario metadata.
- `data/input/scenarios/<area>_<size>/data/blocks.csv` — blocks with landing IDs, stand metrics, and work required.
- `data/input/scenarios/<area>_<size>/data/machines.csv` — machine inventory with role assignments.
- `data/input/scenarios/<area>_<size>/data/landings.csv` — one landing per block.
- `data/input/scenarios/<area>_<size>/data/calendar.csv` — full availability for all machines and days.
- `data/input/scenarios/<area>_<size>/data/prod_rates.csv` — per-machine per-block production rates.
- `data/input/scenarios/<area>_<size>/qa_summary.yaml` — QA summary (counts, metric ranges, rate stats).

See `notes/scenario_bundle.md` for assumptions and modelling decisions.

## Rolling-horizon re-run on FHOPS 1.0.1 (issue #1)

Chapter 4 of the thesis was run on FHOPS 1.0.0a2, which carried no state between rolling-horizon
windows, and scored each run by its last window. Those numbers are superseded by the re-run below.
Background, decisions and evidence are in `notes/rolling_rerun_v101.md`; the manuscript lives in
`UBC-FRESH/fhops-cjfr-rolling-horizon`.

```
python3 -m venv .venv && .venv/bin/pip install fhops==1.0.1 gurobipy   # Gurobi needs a full licence
.venv/bin/python scripts/rolling_rerun_v101.py --mip-solver gurobi --mip-earliness-time-limit 900 --dry-run
nohup .venv/bin/python scripts/rolling_rerun_v101.py --mip-solver gurobi --mip-earliness-time-limit 900 \
    --mip-workers 36 --sa-workers 34 > data/output/rerun_v101_gurobi/run.log 2>&1 &
.venv/bin/python scripts/rolling_rerun_v101.py --mip-solver gurobi --summarize   # rebuild summary.csv
```

Supporting scripts:
- `scripts/probe_mip_window_v101.py`: time a single first window (`--solver`, `--log-file`).
- `scripts/calib_trajectory_v101.py`: parse Gurobi logs into incumbent, bound and gap checkpoints.
