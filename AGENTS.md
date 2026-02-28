# Coding Agent Contract (Jaffray MASc FHOPS Model)

This contract defines how Codex (and collaborators) must operate in the
`jaffray-masc-fhops-model` workspace. Treat it as the root `AGENTS.md` for this
repository; it applies to all subdirectories unless a more specific `AGENTS.md`
overrides it.

## Non‑negotiables
- **Read before acting:** Re-read `ROADMAP.md`, the most recent updates in
  `reference/`, and any relevant notes before proposing or starting new work.
- **No silent changes:** Every change set must be recorded in `CHANGE_LOG.md`
  immediately after implementation. If the file does not exist, create it with an
  initial entry before the first change.
- **Reproducibility first:** Any data generation or transformation must be scripted
  (Python or bash). Manual edits to generated CSVs are not permitted.
- **Data lineage:** Preserve original inputs (e.g., `data/input/blocks/*/blocks.csv`)
  and generate outputs into clearly versioned, scenario-specific folders.
- **Assumptions are explicit:** All modelling assumptions, parameter defaults, and
  synthetic data rules must be documented alongside the scripts that implement them.
- **Cross-repo boundaries:** Do not modify the `fhops` repository unless explicitly
  required to support this project. If FHOPS changes are needed, propose them first
  with a plan and impact summary.

## Planning hygiene
- Update `ROADMAP.md` phase checkboxes whenever work starts, pauses, or completes.
- Maintain a living note under `notes/` for open questions, assumptions, and
  validation outcomes. If `notes/` does not exist, create it with an initial note
  tied to the active roadmap phase.
- Keep the roadmap aligned with the actual execution order; do not skip ahead.

## Data & QA expectations
- Validate every generated dataset with FHOPS loaders/validators before marking a
  scenario complete.
- Record scenario metadata (study area, size tier, input versions, seed values)
  in a manifest file stored with each scenario.
- Track any deviations from FHOPS data-contract requirements explicitly and
  include the rationale in notes and the change log.

## Documentation expectations
- Update `README.md` (or add a dedicated `docs/` note) with a reproducible workflow
  once generation scripts stabilize.
- Provide a clear “how to regenerate” section that includes the exact commands
  used to build the nine scenario inputs.

## Command cadence (before handing work back)
- Run the project-specific validation commands that are appropriate for the work
  completed (e.g., FHOPS dataset validation, scenario load tests).
- Record the exact commands executed in `CHANGE_LOG.md`.

## Collaboration
- Flag blockers or scope shifts in the relevant note and link them from the next
  changelog entry.
- Prefer small, reviewable changes tied directly to the roadmap task list.
