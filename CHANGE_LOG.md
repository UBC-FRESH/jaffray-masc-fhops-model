# Change Log

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
- Documented generator usage and outputs in README and scenario notes.

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
- `head -n 5 /home/gep/projects/jaffray-masc-fhops-model/data/input/scenarios/k_6/data/blocks.csv`
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
- `python scripts/generate_case_study_inputs.py --validate`
- `head -n 20 /home/gep/projects/jaffray-masc-fhops-model/data/input/scenarios/k_6/scenario.yaml`
- `head -n 20 /home/gep/projects/jaffray-masc-fhops-model/data/input/scenarios/k_6/qa_summary.yaml`
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
- `PYTHONPATH=/home/gep/projects/fhops/src /home/gep/projects/jaffray-masc-fhops-model/.venv/bin/python -m fhops.cli.main solve-mip data/input/scenarios/k_6/scenario.yaml --out data/output/solver_sweeps/k_6_mip.csv --time-limit 60`
- `PYTHONPATH=/home/gep/projects/fhops/src /home/gep/projects/jaffray-masc-fhops-model/.venv/bin/python -m fhops.cli.main solve-heur data/input/scenarios/k_6/scenario.yaml --out data/output/solver_sweeps/k_6_sa.csv --iters 500 --seed 42 --kpi-mode basic`
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
- `PYTHONPATH=/home/gep/projects/fhops/src /home/gep/projects/jaffray-masc-fhops-model/.venv/bin/python -m fhops.cli.main solve-heur data/input/scenarios/k_40/scenario.yaml --out data/output/solver_sweeps/k_40_sa.csv --iters 200 --seed 42 --kpi-mode basic`
- `PYTHONPATH=/home/gep/projects/fhops/src /home/gep/projects/jaffray-masc-fhops-model/.venv/bin/python -m fhops.cli.main solve-heur data/input/scenarios/k_40/scenario.yaml --out data/output/solver_sweeps/k_40_sa.csv --iters 50 --seed 42 --kpi-mode basic`
- `PYTHONPATH=/home/gep/projects/fhops/src /home/gep/projects/jaffray-masc-fhops-model/.venv/bin/python -m fhops.cli.main solve-heur data/input/scenarios/ni_6/scenario.yaml --out data/output/solver_sweeps/ni_6_sa.csv --iters 500 --seed 42 --kpi-mode basic`
- `PYTHONPATH=/home/gep/projects/fhops/src /home/gep/projects/jaffray-masc-fhops-model/.venv/bin/python -m fhops.cli.main solve-heur data/input/scenarios/ni_6/scenario.yaml --out data/output/solver_sweeps/ni_6_sa.csv --iters 100 --seed 42 --kpi-mode basic`
- `PYTHONPATH=/home/gep/projects/fhops/src /home/gep/projects/jaffray-masc-fhops-model/.venv/bin/python -m fhops.cli.main solve-heur data/input/scenarios/pg_6/scenario.yaml --out data/output/solver_sweeps/pg_6_sa.csv --iters 100 --seed 42 --kpi-mode basic`
- `PYTHONPATH=/home/gep/projects/fhops/src /home/gep/projects/jaffray-masc-fhops-model/.venv/bin/python -m fhops.cli.main solve-heur data/input/scenarios/ni_18/scenario.yaml --out data/output/solver_sweeps/ni_18_sa.csv --iters 200 --seed 42 --kpi-mode basic`
- `PYTHONPATH=/home/gep/projects/fhops/src /home/gep/projects/jaffray-masc-fhops-model/.venv/bin/python -m fhops.cli.main solve-heur data/input/scenarios/ni_18/scenario.yaml --out data/output/solver_sweeps/ni_18_sa.csv --iters 50 --seed 42 --kpi-mode basic`
- `PYTHONPATH=/home/gep/projects/fhops/src /home/gep/projects/jaffray-masc-fhops-model/.venv/bin/python -m fhops.cli.main solve-heur data/input/scenarios/pg_18/scenario.yaml --out data/output/solver_sweeps/pg_18_sa.csv --iters 50 --seed 42 --kpi-mode basic`
- `PYTHONPATH=/home/gep/projects/fhops/src /home/gep/projects/jaffray-masc-fhops-model/.venv/bin/python -m fhops.cli.main solve-heur data/input/scenarios/k_40/scenario.yaml --out data/output/solver_sweeps/k_40_sa.csv --iters 20 --seed 42 --kpi-mode basic`
- `PYTHONPATH=/home/gep/projects/fhops/src /home/gep/projects/jaffray-masc-fhops-model/.venv/bin/python -m fhops.cli.main solve-heur data/input/scenarios/ni_40/scenario.yaml --out data/output/solver_sweeps/ni_40_sa.csv --iters 20 --seed 42 --kpi-mode basic`
- `PYTHONPATH=/home/gep/projects/fhops/src /home/gep/projects/jaffray-masc-fhops-model/.venv/bin/python -m fhops.cli.main solve-heur data/input/scenarios/ni_40/scenario.yaml --out data/output/solver_sweeps/ni_40_sa.csv --iters 10 --seed 42 --kpi-mode basic`
- `PYTHONPATH=/home/gep/projects/fhops/src /home/gep/projects/jaffray-masc-fhops-model/.venv/bin/python -m fhops.cli.main solve-heur data/input/scenarios/pg_40/scenario.yaml --out data/output/solver_sweeps/pg_40_sa.csv --iters 10 --seed 42 --kpi-mode basic`
- `ls /home/gep/projects/jaffray-masc-fhops-model/data/output/solver_sweeps`
- `python scripts/generate_case_study_inputs.py --validate`
