# FHOPS MASc Modelling Paper Roadmap

- [x] Phase 1 — Intake, alignment, and requirements
  - [x] Task 1.1 — Confirm scope and datasets
    - [x] Subtask 1.1.1 — Confirm the 3 study areas and 3 size tiers (S/M/L)
    - [x] Subtask 1.1.2 — Inventory existing `blocks.csv` inputs per scenario
    - [x] Subtask 1.1.3 — Define naming conventions for scenarios and outputs
  - [x] Task 1.2 — FHOPS data contract review
    - [x] Subtask 1.2.1 — Identify required input files and schema fields
    - [x] Subtask 1.2.2 — Map each required input to available or synthetic sources
    - [x] Subtask 1.2.3 — Document any missing or ambiguous requirements
  - [x] Task 1.3 — Reproducibility plan
    - [x] Subtask 1.3.1 — Decide script entry points and config format
    - [x] Subtask 1.3.2 — Define scenario manifests and metadata schema

- [ ] Phase 2 — Dataset synthesis design
  - [ ] Task 2.1 — Assess FHOPS synthesis tooling
    - [ ] Subtask 2.1.1 — Locate and evaluate existing FHOPS synthesis modules
    - [ ] Subtask 2.1.2 — Run a pilot synthesis on one scenario and capture gaps
    - [ ] Subtask 2.1.3 — Decide whether FHOPS changes are required
  - [ ] Task 2.2 — Input generation rules
    - [ ] Subtask 2.2.1 — Define rules for machines, systems, and productivity
    - [ ] Subtask 2.2.2 — Define rules for landings, distances, and timing
    - [ ] Subtask 2.2.3 — Define constraints, costs, and disturbance parameters
  - [ ] Task 2.3 — Validation plan
    - [ ] Subtask 2.3.1 — Specify FHOPS validation checks per input file
    - [ ] Subtask 2.3.2 — Define acceptance criteria for each scenario tier

- [x] Phase 3 — Implement synthesis pipeline
  - [x] Task 3.1 — Build reproducible generators
    - [x] Subtask 3.1.1 — Implement config-driven generators for missing inputs
    - [x] Subtask 3.1.2 — Create scenario manifest writer (metadata + provenance)
    - [x] Subtask 3.1.3 — Add deterministic seeds and logging
  - [x] Task 3.2 — Integrate FHOPS validation
    - [x] Subtask 3.2.1 — Add loader/validator checks for generated datasets
    - [x] Subtask 3.2.2 — Capture QA summaries (row counts, ranges, constraints)

- [ ] Phase 4 — Generate nine scenarios and QA
  - [x] Task 4.1 — Generate scenario inputs
    - [x] Subtask 4.1.1 — Produce S/M/L datasets for each study area
    - [x] Subtask 4.1.2 — Store outputs in versioned, scenario-specific folders
  - [ ] Task 4.2 — Validate and smoke test
    - [x] Subtask 4.2.1 — Run FHOPS loaders on all nine scenarios
    - [ ] Subtask 4.2.2 — Solve small/medium with MIP; large with heuristics
    - [ ] Subtask 4.2.3 — Record run metadata and QA outcomes

- [ ] Phase 5 — Documentation and delivery
  - [ ] Task 5.1 — Workflow documentation
    - [ ] Subtask 5.1.1 — Document end-to-end data generation workflow
    - [ ] Subtask 5.1.2 — Provide reproducible command list
  - [ ] Task 5.2 — Handoff package
    - [ ] Subtask 5.2.1 — Create a final manifest list for the nine scenarios
    - [ ] Subtask 5.2.2 — Summarize assumptions, limitations, and open questions

- [ ] Phase 6 — Repo cleanup and commit hygiene
  - [x] Task 6.1 — Audit working tree and classify artifacts
    - [x] Subtask 6.1.1 — Inventory untracked outputs, scripts, and logs
    - [x] Subtask 6.1.2 — Identify generated vs source files for commit grouping
  - [ ] Task 6.2 — Normalize experiment tooling and paths
    - [x] Subtask 6.2.1 — Replace absolute paths with repo-relative paths
    - [x] Subtask 6.2.2 — Ensure scripts write outputs to canonical folders
  - [ ] Task 6.3 — Repository hygiene
    - [x] Subtask 6.3.1 — Define ignores for reproducible/generated outputs
    - [ ] Subtask 6.3.2 — Decide which outputs belong in version control
  - [ ] Task 6.4 — Commit sequencing and merge
    - [ ] Subtask 6.4.1 — Chunk changes into related commits
    - [ ] Subtask 6.4.2 — Merge cleanup branch back to main and push
