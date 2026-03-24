import json
import re
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = PROJECT_ROOT / "data" / "output"

JSON_DIR = OUT_DIR
OUTPUT_CSV = OUT_DIR / "rolling_master_dataset.csv"

def parse_filename_metadata(filename:str):
    pattern = r"(?P<context>[a-zA-Z]+)_(?P<size>\d+)_sub(?P<sub>\d+)_lock(?P<lock>\d+)_(?P<solver>\w+)_"
    match = re.search(pattern, filename)

    if not match:
        return {}

    return {
        "context": match.group("context"),
        "size": int(match.group("size")),
        "sub_days": int(match.group("sub")),
        "theta_weeks": int(match.group("sub")) / 7,
        "lock_days": int(match.group("lock")),
        "solver": match.group("solver"),
    }

def extract_metrics_from_json(json_path: Path):
    with json_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    iterations = data.get("iterations", [])
    metadata = data.get("metadata", {})

    if not iterations:
        return {}

    # First iteration objective (comparable)
    first_obj = iterations[0].get("objective")

    # Count time-limited iterations (MIP only)
    time_limited = 0
    for it in iterations:
        warnings = it.get("warnings", [])
        for w in warnings:
            if "maxTimeLimit" in w:
                time_limited += 1
                break

    total_iters = len(iterations)

    time_limit_fraction = (
        time_limited / total_iters if total_iters > 0 else 0
    )

    # Count optimal iterations
    optimal_count = 0
    for it in iterations:
        warnings = it.get("warnings", [])
        for w in warnings:
            if "optimal" in w:
                optimal_count += 1
                break

    return {
        "objective_iteration0": first_obj,
        "num_iterations": total_iters,
        "time_limited_iterations": time_limited,
        "time_limit_fraction": time_limit_fraction,
        "optimal_iterations": optimal_count,
        "total_locked_assignments": data.get("total_locked_assignments"),
        "master_days": metadata.get("master_days"),
    }


# ==========================================================
# MAIN
# ==========================================================
def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = []

    json_files = list(JSON_DIR.glob("*.json"))

    print(f"Found {len(json_files)} JSON files")

    for jf in json_files:
        meta = parse_filename_metadata(jf.name)
        if not meta:
            continue

        metrics = extract_metrics_from_json(jf)

        row = {
            "file": jf.name,
            **meta,
            **metrics,
        }

        rows.append(row)

    df = pd.DataFrame(rows)

    # Sort nicely for plotting
    df = df.sort_values(["size", "theta_weeks", "lock_days", "solver"])

    df.to_csv(OUTPUT_CSV, index=False)

    print("====================================")
    print("Master dataset written to:")
    print(OUTPUT_CSV)
    print("====================================")


if __name__ == "__main__":
    main()
