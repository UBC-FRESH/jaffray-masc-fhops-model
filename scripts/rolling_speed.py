#!/usr/bin/env python3
"""
FHOPS rolling-horizon experiment runner (Thesis Version)

Features:
- Runs rolling horizon grid (context x size x theta x lock)
- Runs both MIP and SA
- Extracts performance metrics directly from JSON outputs
- Writes master CSV ready for plotting
- Robust paths relative to repo
"""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml


# ==========================================================
# EXPERIMENT GRID (ADJUST AS NEEDED)
# ==========================================================
CONTEXTS = ["ka", "ni", "pg"]
SIZES = ["6", "18", "40"]

THETA_WEEKS = [2, 4, 8]      
LOCK_DAYS = [7]

MIP_SOLVER = "highs"
MIP_TIME_LIMIT = 600        

SA_ITERS = 300
SA_SEED_BASE = 42


# ==========================================================
# PATHS
# ==========================================================
PROJECT_ROOT = Path(__file__).resolve().parents[1]
INPUT_ROOT = PROJECT_ROOT / "data" / "input" / "scenarios"
OUT_ROOT = PROJECT_ROOT / "data" / "output"

LOG_CSV = OUT_ROOT / "experiment_log_rolling.csv"
STDOUT_DIR = OUT_ROOT / "stdout"
STDERR_DIR = OUT_ROOT / "stderr"


# ==========================================================
# UTILITIES
# ==========================================================
def weeks_to_days(w: int) -> int:
    return w * 7


def fhops_executable() -> str:
    exe = Path(sys.executable).parent / "fhops"
    return str(exe) if exe.exists() else "fhops"


def scenario_yaml_path(context: str, size: str) -> Path:
    return INPUT_ROOT / f"{context}_{size}" / "scenario.yaml"


def read_base_horizon_days(scenario_yaml: Path) -> int | None:
    data: dict[str, Any] = yaml.safe_load(scenario_yaml.read_text(encoding="utf-8"))
    for path in [
        ("timeline", "days"),
        ("horizon_days",),
        ("planning", "horizon_days"),
    ]:
        cur = data
        ok = True
        for k in path:
            if isinstance(cur, dict) and k in cur:
                cur = cur[k]
            else:
                ok = False
                break
        if ok and isinstance(cur, int):
            return cur
    return None


def run_cmd(cmd: list[str], stdout_file: Path, stderr_file: Path, dry_run: bool) -> tuple[int, float]:
    stdout_file.parent.mkdir(parents=True, exist_ok=True)
    stderr_file.parent.mkdir(parents=True, exist_ok=True)

    if dry_run:
        print("DRY RUN:", " ".join(cmd))
        return 0, 0.0

    start = time.time()
    with stdout_file.open("w") as out, stderr_file.open("w") as err:
        p = subprocess.run(cmd, stdout=out, stderr=err)
    runtime = time.time() - start
    return p.returncode, runtime


def extract_metrics(json_path: Path) -> dict[str, Any]:
    if not json_path.exists():
        return {}

    try:
        with json_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return {}

    rolling = data.get("rolling_stats", {})

    sub_total = rolling.get("num_subproblems")
    sub_tl = rolling.get("num_time_limited")

    time_limit_fraction = None
    if sub_total and sub_total > 0 and sub_tl is not None:
        time_limit_fraction = sub_tl / sub_total

    return {
        "objective_value": data.get("objective_value"),
        "best_bound": data.get("best_bound"),
        "mip_gap": data.get("mip_gap"),
        "solver_status": data.get("solver_status"),
        "subproblems_total": sub_total,
        "subproblems_time_limited": sub_tl,
        "time_limit_fraction": time_limit_fraction,
        "cumulative_runtime": rolling.get("cumulative_runtime_sec"),
        "avg_subproblem_runtime": rolling.get("avg_runtime_sec"),
    }


@dataclass(frozen=True)
class RunSpec:
    context: str
    size: str
    theta_weeks: int
    lock_days: int
    base_days: int | None
    master_days: int
    sub_days: int
    scenario_yaml: Path


def build_run_specs() -> list[RunSpec]:
    specs = []
    for context in CONTEXTS:
        for size in SIZES:
            sc = scenario_yaml_path(context, size)
            if not sc.exists():
                continue

            base_days = read_base_horizon_days(sc)

            for theta in THETA_WEEKS:
                sub_days = weeks_to_days(theta)

                for lock in LOCK_DAYS:
                    master_days = base_days if base_days else sub_days
                    if base_days and sub_days > base_days:
                        sub_days = base_days

                    specs.append(
                        RunSpec(
                            context=context,
                            size=size,
                            theta_weeks=theta,
                            lock_days=lock,
                            base_days=base_days,
                            master_days=master_days,
                            sub_days=sub_days,
                            scenario_yaml=sc,
                        )
                    )
    return specs


# ==========================================================
# CSV SETUP
# ==========================================================
FIELDNAMES = [
    "context",
    "size",
    "theta_weeks",
    "sub_days",
    "lock_days",
    "solver",
    "success",
    "returncode",
    "runtime_sec",
    "objective_value",
    "best_bound",
    "mip_gap",
    "solver_status",
    "subproblems_total",
    "subproblems_time_limited",
    "time_limit_fraction",
    "cumulative_runtime",
    "avg_subproblem_runtime",
    "timestamp",
]


def ensure_csv():
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    if not LOG_CSV.exists():
        with LOG_CSV.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            writer.writeheader()


def append_row(row: dict[str, Any]):
    with LOG_CSV.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writerow(row)


# ==========================================================
# MAIN
# ==========================================================
def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    ensure_csv()
    specs = build_run_specs()

    print("Running FHOPS Rolling Grid...")
    print(f"Output CSV: {LOG_CSV}")
    print("=================================")

    for spec in specs:
        dataset = f"{spec.context}_{spec.size}"
        print(f"\n▶ {dataset} | θ={spec.theta_weeks}w | lock={spec.lock_days}")

        for solver in ["mip", "sa"]:

            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            tag = f"{dataset}_sub{spec.sub_days}_lock{spec.lock_days}_{solver}_{ts}"

            out_json = OUT_ROOT / f"{tag}.json"
            stdout_file = STDOUT_DIR / f"{tag}.out.txt"
            stderr_file = STDERR_DIR / f"{tag}.err.txt"

            cmd = [
                fhops_executable(),
                "plan",
                "rolling",
                str(spec.scenario_yaml),
                "--master-days", str(spec.master_days),
                "--sub-days", str(spec.sub_days),
                "--lock-days", str(spec.lock_days),
                "--solver", solver,
                "--out-json", str(out_json),
            ]

            if solver == "mip":
                cmd += [
                    "--mip-solver", MIP_SOLVER,
                    "--mip-time-limit", str(MIP_TIME_LIMIT),
                ]
            else:
                cmd += [
                    "--sa-iters", str(SA_ITERS),
                    "--sa-seed", str(SA_SEED_BASE),
                ]

            rc, runtime = run_cmd(cmd, stdout_file, stderr_file, args.dry_run)
            success = (rc == 0)

            metrics = extract_metrics(out_json)

            row = {
                "context": spec.context,
                "size": spec.size,
                "theta_weeks": spec.theta_weeks,
                "sub_days": spec.sub_days,
                "lock_days": spec.lock_days,
                "solver": solver,
                "success": success,
                "returncode": rc,
                "runtime_sec": round(runtime, 3),
                "timestamp": datetime.now().isoformat(),
                **metrics,
            }

            append_row(row)

            print(f"  {solver.upper()} → {'OK' if success else 'FAIL'} | runtime={round(runtime,1)}s")

    print("\nAll runs complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
