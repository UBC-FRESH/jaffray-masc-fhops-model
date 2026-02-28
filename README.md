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
