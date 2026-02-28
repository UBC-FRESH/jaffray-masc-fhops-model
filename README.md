# Jaffray MASc FHOPS Modelling Inputs

This workspace assembles the nine MASc case-study scenarios (k/ni/pg × 6/18/40)
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

Each scenario bundle contains:
- `scenario.yaml` — FHOPS scenario metadata.
- `data/blocks.csv` — blocks with landing IDs, stand metrics, and work required.
- `data/machines.csv` — machine inventory with role assignments.
- `data/landings.csv` — one landing per block.
- `data/calendar.csv` — full availability for all machines and days.
- `data/prod_rates.csv` — per-machine per-block production rates.
- `qa_summary.yaml` — QA summary (counts, metric ranges, rate stats).

See `notes/scenario_bundle.md` for assumptions and modelling decisions.
