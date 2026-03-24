# Repo Cleanup Notes

## Status
- Active (Phase 6 cleanup and commit hygiene)

## Findings
- Large untracked experiment outputs under `data/output/` and root-level CSVs.
- New experiment/analysis scripts added under `scripts/` and `scripts/figures/`.
- Several scripts reference absolute paths from a different user account.

## Decisions
- Normalize scripts to use repo-relative paths.
- Classify outputs as generated artifacts unless explicitly required for version control.

## Open questions
- Which experiment outputs/figures (if any) should be committed vs ignored?
- Should we archive a representative subset of outputs for reproducibility documentation?
