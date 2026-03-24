import json, glob, os
from pathlib import Path
import pandas as pd
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = PROJECT_ROOT / "data" / "output"

def parse_term_and_status(warnings):
    term = None
    status = None
    for w in warnings or []:
        if w.startswith("termination_condition="):
            term = w.split("=", 1)[1]
        if w.startswith("solver_status="):
            status = w.split("=", 1)[1]
    return status, term

rows = []
for path in glob.glob(str(OUT_DIR / "*.json")):
    with open(path, "r") as f:
        data = json.load(f)

    meta = data.get("metadata", {})
    time_limit = meta.get("mip_time_limit", None)

    for it in data.get("iterations", []):
        status, term = parse_term_and_status(it.get("warnings", []))

        # Heuristic runtime baseline:
        # - If time limit hit -> runtime = time_limit (e.g., 1800)
        # - Else -> runtime unknown (NaN)
        runtime_h = time_limit if term == "maxTimeLimit" else np.nan

        rows.append({
            "file": os.path.basename(path),
            "scenario": meta.get("scenario"),
            "solver": meta.get("solver"),
            "mip_solver": meta.get("mip_solver"),
            "time_limit_s": time_limit,

            "iteration_index": it.get("iteration_index"),
            "start_day": it.get("start_day"),
            "horizon_days": it.get("horizon_days"),
            "lock_days": it.get("lock_days"),
            "locked_assignments": it.get("locked_assignments"),

            "objective": it.get("objective"),
            "solver_status": status,
            "termination_condition": term,
            "runtime_s_heuristic": runtime_h,
        })

df = pd.DataFrame(rows)
OUT_DIR.mkdir(parents=True, exist_ok=True)
df.to_csv(OUT_DIR / "objective_solver_status_runtime.csv", index=False)
print(df.head(10))
