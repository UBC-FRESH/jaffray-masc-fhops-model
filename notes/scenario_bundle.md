# MASc Modelling Paper — Scenario Bundle Notes

## Status
- Active (Phase 4 generation and QA)

## Decisions
- Study-area labels: `ka` (Kamloops), `ni` (North Island), `pg` (Prince George).
- Scenario naming: `<area>_<size>` where size is `6`, `18`, `40`.
- Output layout: `data/input/scenarios/<area>_<size>/`.
- Manifests: one per scenario plus a parent manifest for the 3×3 bundle.
- Landings: one landing per block (`landing_id` unique per block).
- Machine counts: small/medium/large = 6/12/24 machines.
- Planning horizon: `num_days = 112` (16 weeks) for all nine scenarios.

## Inventory (blocks.csv)
- `ka_6`, `ka_18`, `ka_40` present with 6/18/40 rows respectively.
- `ni_6`, `ni_18`, `ni_40` present with 6/18/40 rows respectively.
- `pg_6`, `pg_18`, `pg_40` present with 6/18/40 rows respectively.
- All nine `blocks.csv` files share the same 7 columns:
  `id`, `work_required`, `volume_per_ha`, `stem_density_per_ha`, `area_ha`,
  `ground_slope_percent`, `harvest_system_id`.
  - Current `harvest_system_id` values: `ground_fb_loader_liveheel`.

## FHOPS data-contract summary (v1.0.0)
- Scenario YAML must reference CSV tables for: `blocks`, `machines`, `landings`,
  `calendar`, `prod_rates`.
- Required `blocks.csv` columns: `id`, `landing_id`, `work_required`.
- Required `machines.csv` columns: `id` (optional: `role`, `crew`, `daily_hours`,
  `operating_cost`, `repair_usage_hours`).
- Required `landings.csv` columns: `id` (optional: `daily_capacity`).
- Required `calendar.csv` columns: `machine_id`, `day` (optional: `available`).
- Required `production_rates.csv` columns: `machine_id`, `block_id`, `rate`.
- Optional tables: `harvest_systems`, `shift_calendar`, `crew_assignments`,
  `road_construction`, plus optional YAML blocks for `timeline`, `mobilisation`,
  `objective_weights`, `locked_assignments`, and `geo` references.

## Gaps to resolve
- `blocks.csv` is missing the required `landing_id` column.
- Stand metrics use `volume_per_ha` instead of `volume_per_ha_m3` (FHOPS contract
  expects the `_m3` suffix); decide whether to map/rename in generated outputs.

## Input mapping (Phase 1.2.2)
- `blocks.csv`: source = existing per-scenario `data/input/blocks/<AREA>_<SIZE>/blocks.csv`,
  then transform to FHOPS schema:
  - add `landing_id` = `L01..LNN` (one landing per block).
  - prefix block IDs with `B` so FHOPS treats them as strings (e.g., `B74735`).
  - rename `volume_per_ha` -> `volume_per_ha_m3`.
  - keep `stem_density_per_ha`, `ground_slope_percent`, `work_required`, `harvest_system_id`.
  - carry `area_ha` forward for metadata only (not required by FHOPS).
- `landings.csv`: synthetic; one landing per block; set `daily_capacity=2` (pending final check).
- `machines.csv`: synthetic; counts by size tier (6/12/24); assign roles matching
  `ground_fb_loader_liveheel` system (feller_buncher, grapple_skidder, processor, loader).
  Use FHOPS default operating cost lookup by setting `role` and leaving `operating_cost` blank/0.
- `calendar.csv`: synthetic; full availability; create rows for every machine and day (1..112).
  `available=1`.
- `production_rates.csv`: synthetic; derive per-machine per-block rates using FHOPS productivity
  helpers (Lahrsen + associated models), keyed by block metrics and machine role.
- `scenario.yaml`: synthetic; includes `name`, `num_days=112`, `schema_version=1.0.0`,
  and `data` paths for the above CSVs. Optional sections left empty unless needed.

## Resolved decisions (Phase 1.2.3)
- Landing `daily_capacity` fixed at 2 for all scenarios.
- Machine roles distributed evenly across `feller_buncher`, `grapple_skidder`,
  `processor`, and `loader` (remainder assigned in role order).

## Generator notes
- Output bundle path: `data/input/scenarios/<area>_<size>/`.
- Generator: `scripts/generate_case_study_inputs.py` (supports `--validate` to run FHOPS loader checks).
- Daily hours set to 24 for all machines (3 shifts/day × 8 hours).
- Timeline config emits shifts `S1`, `S2`, `S3` with 8 hours each; `days_per_week=7`.
- Loader rates use Barko 450 TN-46 `ground_skid_block` scenario.
- Feller-buncher, skidder, and processor rates use Lahrsen 2025, ADV6N7, and Berry 2019 helpers.
- Production rates are floored at 1.0 m³/day to avoid negative regression outputs.
- Missing slopes are replaced with the scenario median.
- QA summaries are written per scenario (`qa_summary.yaml`) and bundled in `data/input/scenarios/qa_summary.yaml`.

## Solver sweep smoke tests (2026-02-28)
- SA runs executed with reduced iteration budgets to confirm solver execution; outputs stored in
  `data/output/solver_sweeps/*_sa.csv`.
- Iteration budgets used:
  - Size 6: `ka_6` (500 iters), `ni_6` (100), `pg_6` (100).
  - Size 18: `ka_18` (800), `ni_18` (50), `pg_18` (50).
  - Size 40: `ka_40` (20), `ni_40` (10), `pg_40` (10).
- MIP smoke test on `ka_6` failed with HiGHS (no feasible solution found within the 60s limit);
  needs follow-up (driver/limits/feasibility checks).
- KPI check against SA outputs shows full completion for `ka_6`, `ka_18`, `ka_40`, and `pg_6`;
  the remaining scenarios still have nonzero `remaining_work_total` under the reduced budgets.

## Assumptions to document in manifests
- All nine scenarios are compiled with consistent input schemas and parameter
  defaults.
- Existing `blocks.csv` inputs remain authoritative and unmodified.

## Open questions
- Which FHOPS synthesis modules are required vs. new scripts in this repo.
- Final metadata fields for per-scenario manifests and the parent bundle manifest.
