#!/usr/bin/env python3
"""
FHOPS rolling-horizon experiment runner (MASc project)

- Runs rolling horizon for a grid of scenarios (context x size) and parameters (theta_weeks x lock_days)
- Runs both solvers: MIP and SA
- Writes per-run stdout/stderr logs + a master CSV log
- Uses robust paths (relative to this file), so it works no matter where VS Code runs from
- Forces the fhops executable from the active venv (no accidental system fhops)

USAGE (from anywhere):
  source .venv/bin/activate
  python scripts/run_rolling_grid.py

Optional:
  python scripts/run_rolling_grid.py --dry-run
"""

from __future__ import annotations

import argparse
import csv
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

# ----------------------------
# EXPERIMENT GRID
# ----------------------------
CONTEXTS = ["pg", "ka", "ni"]          # Prince George / Kamloops / North Island
SIZES = ["6", "18", "40"]             # dataset sizes
THETA_WEEKS = [2, 4, 8, 16]           # subproblem horizon (weeks)
LOCK_DAYS = [1, 7, 14]                # re-optimisation frequency (locked days)

# ----------------------------
# SOLVER SETTINGS
# ----------------------------
MIP_SOLVER = "highs"                  # fhops --mip-solver
MIP_TIME_LIMIT = 1800                 # seconds; fhops --mip-time-limit

SA_ITERS = 500                        # fhops --sa-iters
SA_SEED_BASE = 42                     # fhops --sa-seed (you can vary per run if desired)

# ----------------------------
# PROJECT PATHS (robust)
# ----------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[1]  # assumes script lives in: <repo>/scripts/
INPUT_ROOT = PROJECT_ROOT / "data" / "input" / "scenarios"
OUT_ROOT = PROJECT_ROOT / "data" / "output"

LOG_CSV = OUT_ROOT / "experiment_log_rolling.csv"
STDOUT_DIR = OUT_ROOT / "stdout"
STDERR_DIR = OUT_ROOT / "stderr"


def weeks_to_days(weeks: int) -> int:
    return weeks * 7


def fhops_executable() -> str:
    """
    Always run the fhops CLI from the same environment running this script.
    This avoids calling a system 'fhops' by accident.
    """
    exe = Path(sys.executable).parent / "fhops"
    if exe.exists():
        return str(exe)
    # Fallback: hope PATH resolves correctly (still fine if venv activated)
    return "fhops"


def scenario_yaml_path(context: str, size: str) -> Path:
    """
    Expected structure:
      data/input/scenarios/<context>_<size>/scenario.yaml
    Example:
      data/input/scenarios/ka_6/scenario.yaml
    """
    return INPUT_ROOT / f"{context}_{size}" / "scenario.yaml"


def read_base_horizon_days(scenario_yaml: Path) -> int | None:
    """
    Tries to detect scenario horizon days from YAML to avoid requesting longer horizons
    than the scenario supports.
    """
    data: dict[str, Any] = yaml.safe_load(scenario_yaml.read_text(encoding="utf-8"))

    candidate_paths = [
        ("timeline", "days"),
        ("timeline", "horizon_days"),
        ("horizon_days",),
        ("planning", "horizon_days"),
        ("planning", "days"),
        ("scenario", "horizon_days"),
        ("scenario", "days"),
    ]

    for path in candidate_paths:
        cur: Any = data
        ok = True
        for k in path:
            if isinstance(cur, dict) and k in cur:
                cur = cur[k]
            else:
                ok = False
                break
        if ok and isinstance(cur, int) and cur > 0:
            return cur

    return None


def run_cmd(cmd: list[str], stdout_file: Path, stderr_file: Path, dry_run: bool) -> tuple[int, float]:
    """
    Runs subprocess command, writes stdout/stderr to files, returns (returncode, runtime_seconds).
    """
    stdout_file.parent.mkdir(parents=True, exist_ok=True)
    stderr_file.parent.mkdir(parents=True, exist_ok=True)

    if dry_run:
        print("DRY RUN:", " ".join(cmd))
        stdout_file.write_text("DRY RUN\n", encoding="utf-8")
        stderr_file.write_text("DRY RUN\n", encoding="utf-8")
        return 0, 0.0

    start = time.time()
    with stdout_file.open("w", encoding="utf-8") as out, stderr_file.open("w", encoding="utf-8") as err:
        p = subprocess.run(cmd, stdout=out, stderr=err, text=True)
    runtime = time.time() - start
    return p.returncode, runtime


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
    specs: list[RunSpec] = []
    for context in CONTEXTS:
        for size in SIZES:
            sc_path = scenario_yaml_path(context, size)
            if not sc_path.exists():
                print(f"SKIP (scenario not found): {sc_path}")
                continue

            base_days = read_base_horizon_days(sc_path)
            for theta in THETA_WEEKS:
                sub_days = weeks_to_days(theta)

                for lock in LOCK_DAYS:
                    # Choose master_days and clamp sub_days if necessary
                    if base_days is None:
                        # Safe fallback if we can't detect horizon: keep master=sub
                        master_days = sub_days
                    else:
                        # Use full scenario length as master horizon (typical)
                        master_days = base_days
                        # Ensure master_days >= sub_days (rolling doesn't make sense otherwise)
                        if sub_days > base_days:
                            # Clamp sub_days (and therefore master_days) to scenario horizon
                            sub_days = base_days
                            master_days = base_days
                        else:
                            master_days = max(master_days, sub_days)

                    specs.append(
                        RunSpec(
                            context=context,
                            size=size,
                            theta_weeks=theta,
                            lock_days=lock,
                            base_days=base_days,
                            master_days=master_days,
                            sub_days=sub_days,
                            scenario_yaml=sc_path,
                        )
                    )
    return specs


def ensure_log_header() -> None:
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    STDOUT_DIR.mkdir(parents=True, exist_ok=True)
    STDERR_DIR.mkdir(parents=True, exist_ok=True)

    if not LOG_CSV.exists():
        with LOG_CSV.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "context",
                    "size",
                    "dataset",
                    "base_horizon_days",
                    "theta_weeks",
                    "sub_days",
                    "lock_days",
                    "master_days_used",
                    "solver",
                    "success",
                    "returncode",
                    "runtime_sec",
                    "out_json",
                    "out_assignments",
                    "stdout_path",
                    "stderr_path",
                    "timestamp",
                ],
            )
            writer.writeheader()


def append_log_row(row: dict[str, Any]) -> None:
    with LOG_CSV.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "context",
                "size",
                "dataset",
                "base_horizon_days",
                "theta_weeks",
                "sub_days",
                "lock_days",
                "master_days_used",
                "solver",
                "success",
                "returncode",
                "runtime_sec",
                "out_json",
                "out_assignments",
                "stdout_path",
                "stderr_path",
                "timestamp",
            ],
        )
        writer.writerow(row)
        f.flush()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Print commands but do not execute.")
    args = parser.parse_args()

    ensure_log_header()
    specs = build_run_specs()

    print("=========================================")
    print("RUNNING FHOPS ROLLING-HORIZON GRID")
    print(f"Project root: {PROJECT_ROOT}")
    print(f"Input root:   {INPUT_ROOT}")
    print(f"Output root:  {OUT_ROOT}")
    print(f"Log CSV:      {LOG_CSV}")
    print(f"FHOPS exe:    {fhops_executable()}")
    print("=========================================")

    for spec in specs:
        dataset = f"{spec.context}_{spec.size}"
        ts_tag = datetime.now().strftime("%Y%m%d_%H%M%S")
        run_tag = f"{dataset}_sub{spec.sub_days}_lock{spec.lock_days}"

        print(
            f"\n▶ {dataset} | θ={spec.theta_weeks}w sub_days={spec.sub_days} | lock_days={spec.lock_days} | master_days={spec.master_days}"
        )
        if spec.base_days is None:
            print("  (base horizon days: unknown from YAML; using safe master=sub)")
        else:
            print(f"  (base horizon days detected: {spec.base_days})")

        # -------------------
        # 1) Rolling MIP
        # -------------------
        out_json_mip = OUT_ROOT / f"{run_tag}_mip_{ts_tag}.json"
        out_assign_mip = OUT_ROOT / f"{run_tag}_mip_{ts_tag}_assignments.csv"
        stdout_mip = STDOUT_DIR / f"{run_tag}_mip_{ts_tag}.out.txt"
        stderr_mip = STDERR_DIR / f"{run_tag}_mip_{ts_tag}.err.txt"

        mip_cmd = [
            fhops_executable(),
            "plan",
            "rolling",
            str(spec.scenario_yaml),
            "--master-days", str(spec.master_days),
            "--sub-days", str(spec.sub_days),
            "--lock-days", str(spec.lock_days),
            "--solver", "mip",
            "--mip-solver", MIP_SOLVER,
            "--mip-time-limit", str(MIP_TIME_LIMIT),
            "--out-json", str(out_json_mip),
            "--out-assignments", str(out_assign_mip),
        ]

        rc, rt = run_cmd(mip_cmd, stdout_mip, stderr_mip, dry_run=args.dry_run)
        mip_success = (rc == 0)
        print("✅ MIP OK" if mip_success else f"❌ MIP FAILED (code {rc})")

        append_log_row({
            "context": spec.context,
            "size": spec.size,
            "dataset": dataset,
            "base_horizon_days": spec.base_days,
            "theta_weeks": spec.theta_weeks,
            "sub_days": spec.sub_days,
            "lock_days": spec.lock_days,
            "master_days_used": spec.master_days,
            "solver": "mip",
            "success": mip_success,
            "returncode": rc,
            "runtime_sec": round(rt, 3),
            "out_json": str(out_json_mip),
            "out_assignments": str(out_assign_mip),
            "stdout_path": str(stdout_mip),
            "stderr_path": str(stderr_mip),
            "timestamp": datetime.now().isoformat(sep=" ", timespec="seconds"),
        })

        # -------------------
        # 2) Rolling SA
        # -------------------
        out_json_sa = OUT_ROOT / f"{run_tag}_sa_{ts_tag}.json"
        out_assign_sa = OUT_ROOT / f"{run_tag}_sa_{ts_tag}_assignments.csv"
        stdout_sa = STDOUT_DIR / f"{run_tag}_sa_{ts_tag}.out.txt"
        stderr_sa = STDERR_DIR / f"{run_tag}_sa_{ts_tag}.err.txt"

        sa_seed = SA_SEED_BASE
        sa_cmd = [
            fhops_executable(),
            "plan",
            "rolling",
            str(spec.scenario_yaml),
            "--master-days", str(spec.master_days),
            "--sub-days", str(spec.sub_days),
            "--lock-days", str(spec.lock_days),
            "--solver", "sa",
            "--sa-iters", str(SA_ITERS),
            "--sa-seed", str(sa_seed),
            "--out-json", str(out_json_sa),
            "--out-assignments", str(out_assign_sa),
        ]

        rc2, rt2 = run_cmd(sa_cmd, stdout_sa, stderr_sa, dry_run=args.dry_run)
        sa_success = (rc2 == 0)
        print("✅ SA OK" if sa_success else f"❌ SA FAILED (code {rc2})")

        append_log_row({
            "context": spec.context,
            "size": spec.size,
            "dataset": dataset,
            "base_horizon_days": spec.base_days,
            "theta_weeks": spec.theta_weeks,
            "sub_days": spec.sub_days,
            "lock_days": spec.lock_days,
            "master_days_used": spec.master_days,
            "solver": "sa",
            "success": sa_success,
            "returncode": rc2,
            "runtime_sec": round(rt2, 3),
            "out_json": str(out_json_sa),
            "out_assignments": str(out_assign_sa),
            "stdout_path": str(stdout_sa),
            "stderr_path": str(stderr_sa),
            "timestamp": datetime.now().isoformat(sep=" ", timespec="seconds"),
        })

    print("\n=========================================")
    print("✅ ALL ROLLING RUNS COMPLETE")
    print(f"📄 Log saved: {LOG_CSV}")
    print(f"📁 Outputs:   {OUT_ROOT}")
    print("=========================================")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())