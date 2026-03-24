#!/usr/bin/env python3

import json
import pandas as pd
from pathlib import Path

# -----------------------------
# CONFIG
# -----------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = PROJECT_ROOT / "data" / "output"

LOG_PATH = OUT_DIR / "experiments_full.csv"
OUT_PATH = OUT_DIR / "log_analysis.csv"

# -----------------------------
# JSON PARSER
# -----------------------------
def parse_rolling_json(path: Path) -> dict:
    if not path.exists():
        return {}

    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return {}

    meta = data.get("metadata", {})
    iterations = data.get("iterations", [])

    objectives = []
    terminations = []
    iter_runtimes = []

    for it in iterations:
        obj = it.get("objective")
        if obj is not None:
            objectives.append(obj)

        # termination_condition stored inside warnings list
        for w in it.get("warnings", []):
            if w.startswith("termination_condition="):
                terminations.append(w.split("=")[1])

        if it.get("runtime_s") is not None:
            iter_runtimes.append(it["runtime_s"])

    num_iter = len(iterations)
    num_time_limit = terminations.count("maxTimeLimit")
    num_optimal = terminations.count("optimal")

    return {
        "num_iterations": num_iter,
        "num_time_limit": num_time_limit,
        "num_optimal": num_optimal,
        "time_limit_rate": num_time_limit / num_iter if num_iter else None,
        "objective_first": objectives[0] if objectives else None,
        "objective_mean": sum(objectives) / len(objectives) if objectives else None,
        "objective_best": max(objectives) if objectives else None,
        "mean_iter_runtime": (
            sum(iter_runtimes) / len(iter_runtimes) if iter_runtimes else None
        ),
        "solver": meta.get("solver"),
        "mip_solver": meta.get("mip_solver"),
        "mip_time_limit": meta.get("mip_time_limit"),
    }


# -----------------------------
# MAIN
# -----------------------------
def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print("Reading experiment log...")
    df = pd.read_csv(LOG_PATH)

    analysis_rows = []

    for _, row in df.iterrows():
        json_path = Path(row["out_json"])

        metrics = parse_rolling_json(json_path)

        merged = row.to_dict()
        merged.update(metrics)

        analysis_rows.append(merged)

    out_df = pd.DataFrame(analysis_rows)

    out_df.to_csv(OUT_PATH, index=False)

    print("===================================")
    print("Analysis-ready dataset created:")
    print(OUT_PATH)
    print("===================================")
    print("\nPreview:")
    print(out_df.head())

if __name__ == "__main__":
    main()
