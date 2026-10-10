# Change Log

## 2026-10-10 (d)
- Grid restarted MIP-only after hyperthread contention halved the Gurobi work rate (details in
  `notes/rolling_rerun_v101.md`, "Hyperthread contention and restart"). Harness: per-solver
  manifest name.

Commands:
- `kill -TERM -- -<pgid>` of the first launch; removed artefacts of unfinished runs (`runs/*.log`, `*.gurobi.log`, `*_assignments.csv`, `*.json.tmp` without a JSON)
- `nohup /tmp/opencode/venv-fhops101-grb/bin/python scripts/rolling_rerun_v101.py --mip-solver gurobi --mip-earliness-time-limit 900 --solvers mip --mip-workers 36 --sa-workers 1 > data/output/rerun_v101_gurobi/run_mip.log 2>&1 &`
- Next, after the MIP phase: `scripts/rolling_rerun_v101.py --mip-solver gurobi --mip-earliness-time-limit 900 --solvers sa --sa-workers 70 > data/output/rerun_v101_gurobi/run_sa.log 2>&1`

## 2026-10-10 (c)
- README: added a "Rolling-horizon re-run on FHOPS 1.0.1" section with the exact commands.
- ROADMAP Phase 7: feasibility, decision and launch recorded. Analysis moves to the manuscript repo.

## 2026-10-10 (b)
- Decision (G. Paradis): option B. Gurobi, 1800 s stage 1, 900 s earliness, 36 MIP + 34 SA workers.
  Recorded in `notes/rolling_rerun_v101.md`.
- `scripts/rolling_rerun_v101.py`: separate MIP and SA pools (`--mip-workers`, default 36;
  `--sa-workers`). These replace `--workers` and `--large-mip-workers`; the memory guard is no
  longer needed (≤ 4.7 GB per run).
- Grid launched (see command below).

Commands:
- `scripts/rolling_rerun_v101.py --mip-solver gurobi --mip-earliness-time-limit 900 --dry-run` (234 specs; the first 36 pending are the lock-1 MIP runs)
- `scripts/rolling_rerun_v101.py --smoke --mip-solver gurobi --mip-earliness-time-limit 900 --mip-workers 6 --sa-workers 6 --out-root /tmp/opencode/grbtest/psmoke` (10/10 ok)
- `mkdir -p data/output/rerun_v101_gurobi && /tmp/opencode/venv-fhops101-grb/bin/pip freeze > data/output/rerun_v101_gurobi/environment.txt && nohup /tmp/opencode/venv-fhops101-grb/bin/python scripts/rolling_rerun_v101.py --mip-solver gurobi --mip-earliness-time-limit 900 --mip-workers 36 --sa-workers 34 > data/output/rerun_v101_gurobi/run.log 2>&1 &`

## 2026-10-10
- Time-limit calibration (#1): 8 first-window probes on Gurobi with stage 1 at 7200 s and stage 2 at
  1800 s, plus Gurobi logs. New `scripts/calib_trajectory_v101.py` parses the incumbent, bound, gap
  and work units at checkpoints. New `--log-file` option in `scripts/probe_mip_window_v101.py`.
  Findings in `notes/rolling_rerun_v101.md` ("Time-limit calibration").
- `scripts/rolling_rerun_v101.py`: Gurobi MIP runs write `runs/<run_id>.gurobi.log`.

Commands:
- `/usr/bin/time -v /tmp/opencode/venv-fhops101-grb/bin/python scripts/probe_mip_window_v101.py <ctx> <size> --sub <d> --lock 7 --solver gurobi --time-limit 7200 --earliness-time-limit 1800 --log-file data/output/rerun_v101_calib/<w>.gurobi.log --out data/output/rerun_v101_calib/<w>.json` for ka/ni/pg_40 sub14, ni_40 sub112, ni_18 sub14/sub56, pg_18 sub28, ka_6 sub112
- `/tmp/opencode/venv-fhops101-grb/bin/python scripts/calib_trajectory_v101.py data/output/rerun_v101_calib`
- `/tmp/opencode/venv-fhops101-grb/bin/python scripts/rolling_rerun_v101.py --smoke --mip-solver gurobi --solvers mip --contexts ka --sizes 6 --only-baselines --out-root /tmp/opencode/grbtest/hsmoke --workers 2` (log written)

## 2026-10-09 (b)
- Gurobi comparison (#1): academic licence installed to `~/gurobi.lic` (`grbgetkey`, not in repo).
  Six probe windows (size 18 and 40) on both backends, plus a Gurobi smoke run. Gurobi avoids the
  empty HiGHS incumbents (3/6 windows) at equal wall time. Table in `notes/rolling_rerun_v101.md`
  ("Gurobi vs HiGHS").
- `scripts/rolling_rerun_v101.py`: new `--mip-solver {highs,gurobi}` stored in `RunSpec.mip_solver`.
  The default out-root gets a `_<solver>` suffix for non-HiGHS backends. `--out-root` default is
  now resolved after parsing.
- `scripts/probe_mip_window_v101.py`: new `--solver` and `--threads` options.
- Tiny-production replay violations with Gurobi reported on UBC-FRESH/fhops#157.

Commands:
- `python3 -m venv /tmp/opencode/venv-fhops101-grb && /tmp/opencode/venv-fhops101-grb/bin/pip install fhops==1.0.1 gurobipy` (gurobipy 13.0.3)
- `/usr/bin/time -v <venv>/bin/python scripts/probe_mip_window_v101.py <ctx> <size> --sub <14|56|112> --lock 7 [--solver gurobi] --out ...` (ka/ni/pg_40 sub14, ni_40 sub112, ni_18 sub14/sub56)
- `/tmp/opencode/venv-fhops101-grb/bin/python scripts/rolling_rerun_v101.py --smoke --mip-solver gurobi --workers 16` (10/10 ok)
- `scripts/rolling_rerun_v101.py --dry-run` and `--mip-solver gurobi --dry-run` (234 specs each)

## 2026-10-09
- Feasibility check for the FHOPS 1.0.1 re-run (#1): fresh venv with `fhops==1.0.1` (PyPI),
  harness smoke test, and a one-window size-40 MIP probe. Added `scripts/probe_mip_window_v101.py`
  (first rolling window only, same solver settings as the harness). Evidence in
  `data/output/rerun_v101_smoke/` and `data/output/rerun_v101_probe/`; results and grid wall-clock
  estimate in `notes/rolling_rerun_v101.md` ("Feasibility check"). Manuscript work moves to
  `UBC-FRESH/fhops-cjfr-rolling-horizon`.

Commands:
- `python3 -m venv /tmp/opencode/venv-fhops101 && /tmp/opencode/venv-fhops101/bin/pip install fhops==1.0.1`
- `/usr/bin/time -v /tmp/opencode/venv-fhops101/bin/python scripts/rolling_rerun_v101.py --smoke --workers 16` (10/10 ok, 3:21, 0.25 GB)
- `/usr/bin/time -v /tmp/opencode/venv-fhops101/bin/python scripts/probe_mip_window_v101.py {ka,ni,pg} 40 --sub 14 --lock 7 --out data/output/rerun_v101_probe/<ctx>_40_sub14_lock7.json`
- `/usr/bin/time -v /tmp/opencode/venv-fhops101/bin/python scripts/probe_mip_window_v101.py ni 40 --sub 112 --lock 7 --out data/output/rerun_v101_probe/ni_40_sub112_lock7.json`
- `/tmp/opencode/venv-fhops101/bin/pip freeze > data/output/rerun_v101_probe/environment.txt`

## 2026-10-07
- `scripts/rolling_rerun_v101.py` updated for FHOPS 1.0.1: explicit earliness stage-2 limit (`--mip-earliness-time-limit`, default 300 s), separate memory-guarded pool for size-40 MIP runs (`--large-mip-workers`, default 6), per-run window status counts (`n_no_solution_windows`, `n_skipped_windows`, `n_empty_windows`). Design decision recorded in `notes/rolling_rerun_v101.md` (MIP arm like-for-like).

Commands:
- `/tmp/opencode/fhops-v101-venv/bin/python scripts/rolling_rerun_v101.py --dry-run` (234 specs; FHOPS 1.0.1 @ a0b2799)

## 2026-10-06
- Opened issue #1 and branch `feature/rolling-rerun-v101`: Ch. 4 rolling-horizon results were produced by FHOPS without inter-window state carry-forward (UBC-FRESH/fhops#90, #92).
- Added `scripts/rolling_rerun_v101.py` (same grid as Ch. 4 plus full-horizon baselines; stitched-plan KPI evaluation; resumable, parallel) and `notes/rolling_rerun_v101.md`; added roadmap Phase 7.
- Smoke-tested the pipeline on FHOPS 1.0.0 (pre-fix); outputs kept as evidence in `data/output/rerun_smoke_prefix_v100/`.

Commands:
- `/tmp/opencode/fhops-v101-venv/bin/python scripts/rolling_rerun_v101.py --dry-run` (234 specs)
- `/tmp/opencode/fhops-v101-venv/bin/python scripts/rolling_rerun_v101.py --smoke --workers 8` (10/10 ok; FHOPS 1.0.0 @ f60b638)

## 2026-03-24
- Added Phase 6 cleanup tasks to the roadmap and captured repo-cleanup notes.
- Added rolling-horizon experiment and analysis scripts with repo-relative paths.
- Removed ignore rules for experiment outputs to keep all generated artifacts tracked.
- Set local git identity to enable cleanup commits.
- Committed all experiment outputs and artifacts in a single cleanup commit.

Commands:
- `git checkout -b feature/repo-cleanup`
- `rg -n "/home/rjaffray" scripts`
- `rg -n "/home/" scripts`
- `rg -n "to_csv\\(" scripts`
- `git config --local user.name "gep"`
- `git config --local user.email "gep@localhost"`
- `git add ROADMAP.md notes/repo_cleanup.md`
- `git commit -m "Add repo cleanup phase and notes"`
- `git add scripts`
- `git commit -m "Add rolling experiment analysis scripts"`
- `git add .gitignore`
- `git commit -m "Ignore generated experiment outputs"`
- `apply_patch (remove experiment/output ignores from .gitignore)`
- `git add -A`
- `git commit -m "Commit experiment outputs and cleanup artifacts"`
- `git checkout main`
- `git merge feature/repo-cleanup`
- `git push origin main`
  - Push failed: missing GitHub credentials on this environment.
- `git add CHANGE_LOG.md`
- `git commit -m "Update change log for cleanup"`
- `git commit -m "Update change log commands"`

## 2026-02-27
- Added MASc modelling paper execution contract and project roadmap.
- Established planning notes folder and initial scenario-bundle note.
- Confirmed study-area labels (k/ni/pg) and scenario naming conventions.
- Inventoried all nine `blocks.csv` inputs and captured column schema.
- Reviewed FHOPS data contract and loader requirements; documented required inputs and gaps.
- Captured scenario-wide decisions for landing assignment, machine counts, and 16-week horizon.
- Mapped FHOPS input requirements to existing blocks and synthetic generators; documented remaining decisions.

Commands:
- `mkdir -p /home/gep/projects/jaffray-masc-fhops-model/notes`
- `python - <<'PY'
from pathlib import Path
import csv

base = Path('/home/gep/projects/jaffray-masc-fhops-model/data/input/blocks')
rows = []
for area in ['K','NI','PG']:
    for size in ['6','18','40']:
        path = base / f"{area}_{size}" / 'blocks.csv'
        if not path.exists():
            rows.append((area,size,'MISSING',0,0,''))
            continue
        with path.open() as f:
            reader = csv.reader(f)
            header = next(reader, [])
            nrows = sum(1 for _ in reader)
        rows.append((area,size,'OK',nrows,len(header),', '.join(header)))

print('area,size,status,rows,cols,columns')
for r in rows:
    print(','.join(map(str,r)))
PY`
- `rg -n "data contract|scenario" /home/gep/projects/fhops/src/fhops -g"*.py"`
- `sed -n '1,240p' /home/gep/projects/fhops/src/fhops/scenario/contract/models.py`
- `sed -n '240,640p' /home/gep/projects/fhops/src/fhops/scenario/contract/models.py`
- `rg -n "default_system_registry" /home/gep/projects/fhops/src/fhops/scenario/contract/models.py`
- `sed -n '640,760p' /home/gep/projects/fhops/src/fhops/scenario/contract/models.py`
- `rg -n "scenario.yaml|blocks.csv|machines.csv|production" /home/gep/projects/fhops/docs -g"*.rst"`
- `sed -n '1,220p' /home/gep/projects/fhops/docs/howto/data_contract.rst`
- `ls /home/gep/projects/fhops/src/fhops/scenario`
- `ls /home/gep/projects/fhops/src/fhops/scenario/io`
- `sed -n '1,260p' /home/gep/projects/fhops/src/fhops/scenario/io/loaders.py`
- `sed -n '260,520p' /home/gep/projects/fhops/src/fhops/scenario/io/loaders.py`
- `rg -n "synth|synthetic" /home/gep/projects/fhops/src/fhops/cli -g"*.py"`
- `sed -n '1,260p' /home/gep/projects/fhops/src/fhops/cli/synthetic.py`
- `sed -n '1,200p' /home/gep/projects/fhops/examples/tiny7/scenario.yaml`
- `sed -n '1,220p' /home/gep/projects/fhops/examples/synthetic/small/scenario.yaml`
- `python - <<'PY'
from pathlib import Path
import csv

base = Path('/home/gep/projects/jaffray-masc-fhops-model/data/input/blocks')
values = set()
for path in base.glob('*_*/blocks.csv'):
    with path.open() as f:
        reader = csv.DictReader(f)
        for row in reader:
            val = row.get('harvest_system_id')
            if val is None:
                continue
            val = val.strip()
            if val:
                values.add(val)
print('harvest_system_id values:')
for val in sorted(values):
    print(val)
PY`

## 2026-02-28
- Added reproducible generator script for MASc case-study scenarios (blocks → FHOPS bundles + manifests).
- Generated nine scenario bundles with FHOPS-ready CSVs/YAML and bundle manifest.
- Added loader validation option to the generator and validated all scenarios.
- Normalised manifest `blocks_source` paths to be repo-relative.
- Added QA summary outputs and shift-timeline defaults (3×8h, 7 days/week) to the generator.
- Updated requirements for generator/runtime dependencies.
- Chunked commits, attempted push (pending credentials), and ran solver sweep smoke tests (SA).
- Renamed Kamloops prefix from `k` to `ka` across inputs, outputs, and metadata; regenerated bundles.
- Documented generator usage and outputs in README and scenario notes.
- Clarified README paths to be repo-relative and audited documentation paths.
- Updated roadmap phase checkboxes and scenario-bundle note status.

Commands:
- `rg -n "ground_fb_loader_liveheel" /home/gep/projects/fhops/src/fhops -g"*.py" -g"*.yml" -g"*.yaml"`
- `sed -n '100,180p' /home/gep/projects/fhops/src/fhops/scheduling/systems/models.py`
- `rg -n "machine_role" /home/gep/projects/fhops/src/fhops -g"*.py"`
- `sed -n '1,80p' /home/gep/projects/fhops/src/fhops/scheduling/systems/models.py`
- `sed -n '140,240p' /home/gep/projects/fhops/src/fhops/costing/machine_rates.py`
- `rg -n "def estimate_grapple_skidder_productivity_adv6n7" -n /home/gep/projects/fhops/src/fhops/productivity`
- `sed -n '240,340p' /home/gep/projects/fhops/src/fhops/productivity/skidder_ft.py`
- `rg -n "def estimate_productivity" /home/gep/projects/fhops/src/fhops/productivity/lahrsen2025.py`
- `sed -n '120,200p' /home/gep/projects/fhops/src/fhops/productivity/lahrsen2025.py`
- `rg -n "def estimate_processor_productivity_berry2019" -n /home/gep/projects/fhops/src/fhops/productivity`
- `sed -n '720,820p' /home/gep/projects/fhops/src/fhops/productivity/processor_loader.py`
- `rg --files -g"*barko*" /home/gep/projects/fhops`
- `python - <<'PY'
import json
from pathlib import Path

path = Path('/home/gep/projects/fhops/src/fhops/data/loader_barko450.json')
print(path.exists())
if path.exists():
    data = json.loads(path.read_text())
    print(data.keys())
    for key, val in data.get('scenarios', {}).items():
        print(key, val)
PY`
- `python - <<'PY'
import json
from pathlib import Path

path = Path('/home/gep/projects/fhops/data/productivity/loader_barko450.json')
print(path.exists())
if path.exists():
    data = json.loads(path.read_text())
    print(data.keys())
    for key, val in data.get('scenarios', {}).items():
        print(key, val)
PY`
- `python - <<'PY'
import importlib.util
print('yaml', importlib.util.find_spec('yaml'))
PY`
- `python - <<'PY'
import sys
from pathlib import Path

fhops_root = Path('/home/gep/projects/fhops')
sys.path.insert(0, str(fhops_root / 'src'))

try:
    from fhops.productivity import (
        LahrsenModel,
        estimate_productivity,
        estimate_grapple_skidder_productivity_adv6n7,
        estimate_processor_productivity_berry2019,
        estimate_loader_productivity_barko450,
    )
    print('import ok')
    print(LahrsenModel)
except Exception as exc:
    print('import failed', exc)
PY`
- `python - <<'PY'
from pathlib import Path
from pypdf import PdfReader
import re

pdf = Path('/home/gep/projects/jaffray-masc-fhops-model/reference/Rosalia_Jaffray_MASc_Modelling_Paper__revision_0_.pdf')
reader = PdfReader(str(pdf))
text = '\\n'.join((page.extract_text() or '') for page in reader.pages)
clean = re.sub(r'\\s+', ' ', text)
for term in ['shift', 'hours', 'hour', 'daily', '24']:
    idx = clean.lower().find(term)
    if idx != -1:
        print(term, clean[idx-120:idx+120])
PY`
- `python - <<'PY'
import json
from pathlib import Path

path = Path('/home/gep/projects/fhops/data/productivity/loader_barko450.json')
print(path.exists())
if path.exists():
    data = json.loads(path.read_text())
    print(type(data.get('scenarios')))
    for item in data.get('scenarios'):
        print(item)
PY`
- `python - <<'PY'
from pathlib import Path
import csv

base = Path('/home/gep/projects/jaffray-masc-fhops-model/data/input/blocks')
mins = {
    'volume_per_ha': None,
    'stem_density_per_ha': None,
    'area_ha': None,
    'ground_slope_percent': None,
}

for path in base.glob('*_*/blocks.csv'):
    with path.open() as f:
        reader = csv.DictReader(f)
        for row in reader:
            for key in mins:
                val = float(row[key])
                if mins[key] is None or val < mins[key]:
                    mins[key] = val

print(mins)
PY`
- `python - <<'PY'
from pathlib import Path
import csv

base = Path('/home/gep/projects/jaffray-masc-fhops-model/data/input/blocks')
mins = {k: None for k in ['volume_per_ha', 'stem_density_per_ha', 'area_ha', 'ground_slope_percent']}
missing = {k: 0 for k in mins}

for path in base.glob('*_*/blocks.csv'):
    with path.open() as f:
        reader = csv.DictReader(f)
        for row in reader:
            for key in mins:
                raw = row.get(key, '')
                if raw is None or str(raw).strip() == '':
                    missing[key] += 1
                    continue
                val = float(raw)
                if mins[key] is None or val < mins[key]:
                    mins[key] = val

print('mins', mins)
print('missing', missing)
PY`
- `python - <<'PY'
from pathlib import Path
import csv

base = Path('/home/gep/projects/jaffray-masc-fhops-model/data/input/blocks')
for path in sorted(base.glob('*_*/blocks.csv')):
    total = 0.0
    with path.open() as f:
        reader = csv.DictReader(f)
        for row in reader:
            total += float(row['work_required'])
    print(path.parent.name, f"total_work={total:.1f}")
PY`
- `python -m pip install numpy`
- `python scripts/generate_case_study_inputs.py`
- `find /home/gep/projects/jaffray-masc-fhops-model/data/input/scenarios -maxdepth 2 -type d`
- `head -n 5 /home/gep/projects/jaffray-masc-fhops-model/data/input/scenarios/ka_6/data/blocks.csv`
- `python -m pip install pandas`
- `python - <<'PY'
from pathlib import Path
import sys

sys.path.insert(0, '/home/gep/projects/fhops/src')
from fhops.scenario.io import load_scenario

base = Path('/home/gep/projects/jaffray-masc-fhops-model/data/input/scenarios')
scenarios = sorted(base.glob('*/scenario.yaml'))
errors = []
for path in scenarios:
    try:
        sc = load_scenario(path)
        print(f"OK: {path.parent.name} blocks={len(sc.blocks)} machines={len(sc.machines)} days={sc.num_days}")
    except Exception as exc:
        errors.append((path, exc))
        print(f"FAIL: {path} -> {exc}")

if errors:
    raise SystemExit(f"{len(errors)} scenario(s) failed validation")
PY`
- `python scripts/generate_case_study_inputs.py`
- `python - <<'PY'
from pathlib import Path
import sys

sys.path.insert(0, '/home/gep/projects/fhops/src')
from fhops.scenario.io import load_scenario

base = Path('/home/gep/projects/jaffray-masc-fhops-model/data/input/scenarios')
scenarios = sorted(base.glob('*/scenario.yaml'))
errors = []
for path in scenarios:
    try:
        sc = load_scenario(path)
        print(f"OK: {path.parent.name} blocks={len(sc.blocks)} machines={len(sc.machines)} days={sc.num_days}")
    except Exception as exc:
        errors.append((path, exc))
        print(f"FAIL: {path} -> {exc}")

if errors:
    raise SystemExit(f"{len(errors)} scenario(s) failed validation")
PY`
- `python scripts/generate_case_study_inputs.py --validate`
- `PYTHONPATH=/home/gep/projects/fhops/src /home/gep/projects/jaffray-masc-fhops-model/.venv/bin/python - <<'PY'
from pathlib import Path
import pandas as pd

from fhops.scenario.io import load_scenario
from fhops.scenario.contract import Problem
from fhops.evaluation.metrics.kpis import compute_kpis

base = Path('/home/gep/projects/jaffray-masc-fhops-model/data/input/scenarios')
out_dir = Path('/home/gep/projects/jaffray-masc-fhops-model/data/output/solver_sweeps')

rows = []
for scenario_path in sorted(base.glob('*/scenario.yaml')):
    scenario_id = scenario_path.parent.name
    csv_path = out_dir / f\"{scenario_id}_sa.csv\"
    if not csv_path.exists():
        continue
    sc = load_scenario(scenario_path)
    pb = Problem.from_scenario(sc)
    df = pd.read_csv(csv_path)
    kpis = compute_kpis(pb, df)
    rows.append({
        'scenario': scenario_id,
        'completed_blocks': kpis.get('completed_blocks'),
        'remaining_work_total': kpis.get('remaining_work_total'),
        'total_production': kpis.get('total_production'),
        'makespan_day': kpis.get('makespan_day'),
    })

for row in rows:
    print(row)
PY`
- `python scripts/generate_case_study_inputs.py --validate`
- `head -n 20 /home/gep/projects/jaffray-masc-fhops-model/data/input/scenarios/ka_6/scenario.yaml`
- `head -n 20 /home/gep/projects/jaffray-masc-fhops-model/data/input/scenarios/ka_6/qa_summary.yaml`
- `head -n 20 /home/gep/projects/jaffray-masc-fhops-model/data/input/scenarios/qa_summary.yaml`
- `git -C /home/gep/projects/jaffray-masc-fhops-model status --short`
- `git -C /home/gep/projects/jaffray-masc-fhops-model config user.name "Codex"`
- `git -C /home/gep/projects/jaffray-masc-fhops-model config user.email "codex@openai.com"`
- `git -C /home/gep/projects/jaffray-masc-fhops-model add .gitignore`
- `git -C /home/gep/projects/jaffray-masc-fhops-model commit -m "Add local venv ignore"`
- `git -C /home/gep/projects/jaffray-masc-fhops-model add -A data/blocks data/input/blocks`
- `git -C /home/gep/projects/jaffray-masc-fhops-model commit -m "Move blocks inputs under data/input/blocks"`
- `git -C /home/gep/projects/jaffray-masc-fhops-model add AGENTS.md ROADMAP.md reference`
- `git -C /home/gep/projects/jaffray-masc-fhops-model commit -m "Add MASc governance docs and references"`
- `git -C /home/gep/projects/jaffray-masc-fhops-model add README.md requirements.txt scripts notes`
- `git -C /home/gep/projects/jaffray-masc-fhops-model commit -m "Add scenario generator and planning notes"`
- `git -C /home/gep/projects/jaffray-masc-fhops-model add data/input/scenarios`
- `git -C /home/gep/projects/jaffray-masc-fhops-model commit -m "Add generated FHOPS scenario bundles"`
- `git -C /home/gep/projects/jaffray-masc-fhops-model add CHANGE_LOG.md`
- `git -C /home/gep/projects/jaffray-masc-fhops-model commit -m "Add change log"`
- `git -C /home/gep/projects/jaffray-masc-fhops-model remote -v`
- `git -C /home/gep/projects/jaffray-masc-fhops-model push origin main`
- `PYTHONPATH=/home/gep/projects/fhops/src /home/gep/projects/jaffray-masc-fhops-model/.venv/bin/python -m fhops.cli.main --help`
- `PYTHONPATH=/home/gep/projects/fhops/src /home/gep/projects/jaffray-masc-fhops-model/.venv/bin/python -m fhops.cli.main solve-mip --help`
- `PYTHONPATH=/home/gep/projects/fhops/src /home/gep/projects/jaffray-masc-fhops-model/.venv/bin/python -m fhops.cli.main solve-heur --help`
- `mkdir -p /home/gep/projects/jaffray-masc-fhops-model/data/output/solver_sweeps`
- `PYTHONPATH=/home/gep/projects/fhops/src /home/gep/projects/jaffray-masc-fhops-model/.venv/bin/python -m fhops.cli.main solve-mip data/input/scenarios/ka_6/scenario.yaml --out data/output/solver_sweeps/ka_6_mip.csv --time-limit 60`
- `PYTHONPATH=/home/gep/projects/fhops/src /home/gep/projects/jaffray-masc-fhops-model/.venv/bin/python -m fhops.cli.main solve-heur data/input/scenarios/ka_6/scenario.yaml --out data/output/solver_sweeps/ka_6_sa.csv --iters 500 --seed 42 --kpi-mode basic`
- `PYTHONPATH=/home/gep/projects/fhops/src /home/gep/projects/jaffray-masc-fhops-model/.venv/bin/python - <<'PY'
from pathlib import Path
import subprocess
import sys
import os

base = Path('/home/gep/projects/jaffray-masc-fhops-model/data/input/scenarios')
out_dir = Path('/home/gep/projects/jaffray-masc-fhops-model/data/output/solver_sweeps')
out_dir.mkdir(parents=True, exist_ok=True)

python = '/home/gep/projects/jaffray-masc-fhops-model/.venv/bin/python'
module = 'fhops.cli.main'

sizes_iters = {
    '6': 500,
    '18': 800,
    '40': 400,
}

failures = []
for scenario_path in sorted(base.glob('*/scenario.yaml')):
    scenario_id = scenario_path.parent.name
    size = scenario_id.split('_')[-1]
    iters = sizes_iters.get(size, 500)
    out_path = out_dir / f\"{scenario_id}_sa.csv\"
    cmd = [
        python, '-m', module, 'solve-heur',
        str(scenario_path),
        '--out', str(out_path),
        '--iters', str(iters),
        '--seed', '42',
        '--kpi-mode', 'basic',
    ]
    print(f\"\\n=== {scenario_id} (iters={iters}) ===\")
    result = subprocess.run(
        cmd,
        env={**os.environ, 'PYTHONPATH': '/home/gep/projects/fhops/src'},
        cwd='/home/gep/projects/jaffray-masc-fhops-model',
        text=True,
        capture_output=True,
    )
    print(result.stdout)
    if result.returncode != 0:
        print(result.stderr)
        failures.append((scenario_id, result.returncode))

if failures:
    sys.exit(f\"Failures: {failures}\")
PY`
- `PYTHONPATH=/home/gep/projects/fhops/src /home/gep/projects/jaffray-masc-fhops-model/.venv/bin/python - <<'PY'
from pathlib import Path
import subprocess
import sys
import os

base = Path('/home/gep/projects/jaffray-masc-fhops-model/data/input/scenarios')
out_dir = Path('/home/gep/projects/jaffray-masc-fhops-model/data/output/solver_sweeps')
out_dir.mkdir(parents=True, exist_ok=True)

python = '/home/gep/projects/jaffray-masc-fhops-model/.venv/bin/python'
module = 'fhops.cli.main'

sizes_iters = {
    '6': 500,
    '18': 800,
    '40': 400,
}

failures = []
for scenario_path in sorted(base.glob('*/scenario.yaml')):
    scenario_id = scenario_path.parent.name
    size = scenario_id.split('_')[-1]
    iters = sizes_iters.get(size, 500)
    out_path = out_dir / f\"{scenario_id}_sa.csv\"
    if out_path.exists():
        print(f\"Skipping {scenario_id}; output exists\")
        continue
    cmd = [
        python, '-m', module, 'solve-heur',
        str(scenario_path),
        '--out', str(out_path),
        '--iters', str(iters),
        '--seed', '42',
        '--kpi-mode', 'basic',
    ]
    print(f\"\\n=== {scenario_id} (iters={iters}) ===\")
    result = subprocess.run(
        cmd,
        env={**os.environ, 'PYTHONPATH': '/home/gep/projects/fhops/src'},
        cwd='/home/gep/projects/jaffray-masc-fhops-model',
        text=True,
        capture_output=True,
    )
    print(result.stdout)
    if result.returncode != 0:
        print(result.stderr)
        failures.append((scenario_id, result.returncode))

if failures:
    sys.exit(f\"Failures: {failures}\")
PY`
- `PYTHONPATH=/home/gep/projects/fhops/src /home/gep/projects/jaffray-masc-fhops-model/.venv/bin/python -m fhops.cli.main solve-heur data/input/scenarios/ka_40/scenario.yaml --out data/output/solver_sweeps/ka_40_sa.csv --iters 200 --seed 42 --kpi-mode basic`
- `PYTHONPATH=/home/gep/projects/fhops/src /home/gep/projects/jaffray-masc-fhops-model/.venv/bin/python -m fhops.cli.main solve-heur data/input/scenarios/ka_40/scenario.yaml --out data/output/solver_sweeps/ka_40_sa.csv --iters 50 --seed 42 --kpi-mode basic`
- `PYTHONPATH=/home/gep/projects/fhops/src /home/gep/projects/jaffray-masc-fhops-model/.venv/bin/python -m fhops.cli.main solve-heur data/input/scenarios/ni_6/scenario.yaml --out data/output/solver_sweeps/ni_6_sa.csv --iters 500 --seed 42 --kpi-mode basic`
- `PYTHONPATH=/home/gep/projects/fhops/src /home/gep/projects/jaffray-masc-fhops-model/.venv/bin/python -m fhops.cli.main solve-heur data/input/scenarios/ni_6/scenario.yaml --out data/output/solver_sweeps/ni_6_sa.csv --iters 100 --seed 42 --kpi-mode basic`
- `PYTHONPATH=/home/gep/projects/fhops/src /home/gep/projects/jaffray-masc-fhops-model/.venv/bin/python -m fhops.cli.main solve-heur data/input/scenarios/pg_6/scenario.yaml --out data/output/solver_sweeps/pg_6_sa.csv --iters 100 --seed 42 --kpi-mode basic`
- `PYTHONPATH=/home/gep/projects/fhops/src /home/gep/projects/jaffray-masc-fhops-model/.venv/bin/python -m fhops.cli.main solve-heur data/input/scenarios/ni_18/scenario.yaml --out data/output/solver_sweeps/ni_18_sa.csv --iters 200 --seed 42 --kpi-mode basic`
- `PYTHONPATH=/home/gep/projects/fhops/src /home/gep/projects/jaffray-masc-fhops-model/.venv/bin/python -m fhops.cli.main solve-heur data/input/scenarios/ni_18/scenario.yaml --out data/output/solver_sweeps/ni_18_sa.csv --iters 50 --seed 42 --kpi-mode basic`
- `PYTHONPATH=/home/gep/projects/fhops/src /home/gep/projects/jaffray-masc-fhops-model/.venv/bin/python -m fhops.cli.main solve-heur data/input/scenarios/pg_18/scenario.yaml --out data/output/solver_sweeps/pg_18_sa.csv --iters 50 --seed 42 --kpi-mode basic`
- `PYTHONPATH=/home/gep/projects/fhops/src /home/gep/projects/jaffray-masc-fhops-model/.venv/bin/python -m fhops.cli.main solve-heur data/input/scenarios/ka_40/scenario.yaml --out data/output/solver_sweeps/ka_40_sa.csv --iters 20 --seed 42 --kpi-mode basic`
- `PYTHONPATH=/home/gep/projects/fhops/src /home/gep/projects/jaffray-masc-fhops-model/.venv/bin/python -m fhops.cli.main solve-heur data/input/scenarios/ni_40/scenario.yaml --out data/output/solver_sweeps/ni_40_sa.csv --iters 20 --seed 42 --kpi-mode basic`
- `PYTHONPATH=/home/gep/projects/fhops/src /home/gep/projects/jaffray-masc-fhops-model/.venv/bin/python -m fhops.cli.main solve-heur data/input/scenarios/ni_40/scenario.yaml --out data/output/solver_sweeps/ni_40_sa.csv --iters 10 --seed 42 --kpi-mode basic`
- `PYTHONPATH=/home/gep/projects/fhops/src /home/gep/projects/jaffray-masc-fhops-model/.venv/bin/python -m fhops.cli.main solve-heur data/input/scenarios/pg_40/scenario.yaml --out data/output/solver_sweeps/pg_40_sa.csv --iters 10 --seed 42 --kpi-mode basic`
- `ls /home/gep/projects/jaffray-masc-fhops-model/data/output/solver_sweeps`
- `for d in /home/gep/projects/jaffray-masc-fhops-model/data/input/blocks/K_*; do bn=$(basename "$d"); new=KA_${bn#K_}; mv "$d" "/home/gep/projects/jaffray-masc-fhops-model/data/input/blocks/$new"; done`
- `for d in /home/gep/projects/jaffray-masc-fhops-model/data/input/scenarios/k_*; do bn=$(basename "$d"); new=ka_${bn#k_}; mv "$d" "/home/gep/projects/jaffray-masc-fhops-model/data/input/scenarios/$new"; done`
- `for f in /home/gep/projects/jaffray-masc-fhops-model/data/output/solver_sweeps/k_*_sa.csv; do bn=$(basename "$f"); new=ka_${bn#k_}; mv "$f" "/home/gep/projects/jaffray-masc-fhops-model/data/output/solver_sweeps/$new"; done`
- `for f in /home/gep/projects/jaffray-masc-fhops-model/data/input/blocks/data/K_*.csv /home/gep/projects/jaffray-masc-fhops-model/data/input/blocks/data/K_*.csv.xml; do bn=$(basename "$f"); new=KA_${bn#K_}; mv "$f" "/home/gep/projects/jaffray-masc-fhops-model/data/input/blocks/data/$new"; done`
- `for f in /home/gep/projects/jaffray-masc-fhops-model/data/input/blocks/data/.ipynb_checkpoints/K_*-checkpoint.csv; do bn=$(basename "$f"); new=KA_${bn#K_}; mv "$f" "/home/gep/projects/jaffray-masc-fhops-model/data/input/blocks/data/.ipynb_checkpoints/$new"; done`
- `python - <<'PY'
from pathlib import Path

root = Path('/home/gep/projects/jaffray-masc-fhops-model')
patterns = {"k_": "ka_"}
file_exts = {'.md', '.yaml', '.yml', '.txt'}

for path in root.rglob('*'):
    if path.is_dir():
        continue
    if path.suffix.lower() not in file_exts:
        continue
    try:
        text = path.read_text(encoding='utf-8')
    except UnicodeDecodeError:
        continue
    new_text = text
    for old, new in patterns.items():
        new_text = new_text.replace(old, new)
    if new_text != text:
        path.write_text(new_text, encoding='utf-8')
PY`
- `python - <<'PY'
from pathlib import Path

root = Path('/home/gep/projects/jaffray-masc-fhops-model')
file_exts = {'.md', '.yaml', '.yml', '.txt'}

for path in root.rglob('*'):
    if path.is_dir():
        continue
    if path.suffix.lower() not in file_exts:
        continue
    try:
        text = path.read_text(encoding='utf-8')
    except UnicodeDecodeError:
        continue
    new_text = text.replace('data/input/blocks/K_', 'data/input/blocks/KA_')
    if new_text != text:
        path.write_text(new_text, encoding='utf-8')
PY`
- `python - <<'PY'
from pathlib import Path

root = Path('/home/gep/projects/jaffray-masc-fhops-model')
file_exts = {'.md', '.yaml', '.yml', '.txt'}
replacements = {
    'worka_': 'work_',
    'blocka_': 'block_',
}

for path in root.rglob('*'):
    if path.is_dir():
        continue
    if path.suffix.lower() not in file_exts:
        continue
    try:
        text = path.read_text(encoding='utf-8')
    except UnicodeDecodeError:
        continue
    new_text = text
    for old, new in replacements.items():
        new_text = new_text.replace(old, new)
    if new_text != text:
        path.write_text(new_text, encoding='utf-8')
PY`
- `python - <<'PY'
from pathlib import Path

root = Path('/home/gep/projects/jaffray-masc-fhops-model/data/input/scenarios')
for path in root.rglob('*.yaml'):
    text = path.read_text(encoding='utf-8')
    new_text = text.replace('area: k\\n', 'area: ka\\n')
    new_text = new_text.replace('MASc K ', 'MASc KA ')
    if new_text != text:
        path.write_text(new_text, encoding='utf-8')
PY`
- `python scripts/generate_case_study_inputs.py --validate`
- `python scripts/generate_case_study_inputs.py --validate`
- `git status -sb`
- `ls /home/gep/projects`
- `git status -sb`
- `rg -n "KPI|completion|unmet|remaining|finished|complete" notes/scenario_bundle.md`
- `sed -n '70,110p' notes/scenario_bundle.md`
- `ls data/output/solver_sweeps`
- `python - <<'PY'
import pandas as pd
from pathlib import Path

path = Path('data/output/solver_sweeps')
for csv in sorted(path.glob('*_sa.csv')):
    df = pd.read_csv(csv)
    status_cols = [c for c in df.columns if 'status' in c.lower()]
    print(csv.name, df.shape, status_cols[:3])
PY`
- `rg -n "\\bk_" /home/gep/projects/jaffray-masc-fhops-model`
- `rg -n "\\bK_" /home/gep/projects/jaffray-masc-fhops-model`
- `cat /home/gep/projects/jaffray-masc-fhops-model/AGENTS.md`
- `rg -n "data/blocks|data/input/blocks|input/blocks|input/scenarios|scenarios/" README.md notes ROADMAP.md CHANGE_LOG.md`
- `sed -n '1,240p' README.md`
- `sed -n '1,160p' data/input/scenarios/manifest.yaml`
- `sed -n '1,120p' data/input/scenarios/ka_6/scenario.yaml`
- `rg -n "k_" scripts/generate_case_study_inputs.py`
- `rg -n "area|AREA|size" scripts/generate_case_study_inputs.py`
- `sed -n '520,680p' scripts/generate_case_study_inputs.py`
- `rg -n "data/blocks|data/input/blocks|data/input/scenarios|blocks.csv" notes/scenario_bundle.md`
- `rg -n "area: k\\b|MASc K" data/input/scenarios`
- `sed -n '1,220p' ROADMAP.md`
- `rg -n "2026-02-28" CHANGE_LOG.md`
- `sed -n '72,130p' CHANGE_LOG.md`
- `python - <<'PY'
from pathlib import Path
import re

root = Path('/home/gep/projects/jaffray-masc-fhops-model')
md_files = list(root.rglob('*.md'))
missing = []
pattern = re.compile(r'`([^`]+)`')

for md in md_files:
    text = md.read_text(encoding='utf-8')
    for match in pattern.findall(text):
        token = match.strip()
        if '/' not in token and not token.startswith('.'):
            continue
        if token.startswith('http') or token.startswith('https'):
            continue
        if '<' in token and '>' in token:
            continue
        path = (root / token).resolve()
        if not path.exists():
            missing.append((md, token))

if not missing:
    print('No missing paths found in backticks.')
else:
    print('Missing paths:')
    for md, token in missing:
        print(f\"{md.relative_to(root)} -> {token}\")
PY`
- `python - <<'PY'
from pathlib import Path
import re

root = Path('/home/gep/projects/jaffray-masc-fhops-model')
md_files = list(root.rglob('*.md'))
missing = []
pattern = re.compile(r'`([^`]+)`')
code_fence = re.compile(r'```.*?```', re.S)

for md in md_files:
    text = md.read_text(encoding='utf-8')
    text = code_fence.sub('', text)
    for match in pattern.findall(text):
        token = match.strip()
        if '/' not in token and not token.startswith('.'):
            continue
        if token.startswith('http') or token.startswith('https'):
            continue
        if '<' in token and '>' in token:
            continue
        path = (root / token).resolve()
        if not path.exists():
            missing.append((md, token))

if not missing:
    print('No missing backtick paths found in markdown.')
else:
    print('Missing paths:')
    for md, token in missing:
        print(f\"{md.relative_to(root)} -> {token}\")
PY`
- `git diff --stat`
- `git diff README.md`
- `git diff --unified=5 CHANGE_LOG.md | head -n 80`
- `git status -sb`
- `git status -sb`
- `git add -A`
- `git status -sb`
- `head -n 5 data/input/scenarios/ka_6/scenario.yaml && echo '---' && head -n 5 data/input/scenarios/ka_40/scenario.yaml`
- `git add CHANGE_LOG.md README.md ROADMAP.md notes/scenario_bundle.md`
- `git commit -m "Rename Kamloops prefix to ka"`
