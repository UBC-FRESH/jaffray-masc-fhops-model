#!/usr/bin/env python3
"""Summarise Gurobi incumbent/bound trajectories from the time-limit calibration probes.

Reads ``<out>/*.gurobi.log`` written by ``probe_mip_window_v101.py --log-file`` (one log per window,
stage 1 = main objective, stage 2 = earliness tie-break; each stage starts at "Optimize a model").
For every stage it reports the incumbent, best bound and gap at fixed checkpoints, the relative
shortfall of the incumbent against the stage's final incumbent, and the work units per second
(from the final "Explored ... in S seconds (W work units)" line).

Outputs ``<out>/trajectory_checkpoints.csv``, ``<out>/stage_totals.csv`` and ``<out>/model_sizes.csv``
(rows, columns, binaries of the stage-1 model as reported by Gurobi before presolve).

Usage
-----
    python scripts/calib_trajectory_v101.py data/output/rerun_v101_calib
"""

from __future__ import annotations

import argparse
import math
import re
from pathlib import Path

import pandas as pd

CHECKPOINTS = [60, 300, 600, 900, 1800, 3600, 5400, 7200]
EXPLORED = re.compile(r"Explored .* in ([\d.]+) seconds \(([\d.]+) work units\)")
TIME_TOKEN = re.compile(r"^(\d+)s$")


def _num(token: str) -> float:
    try:
        return float(token.rstrip("%"))
    except ValueError:
        return math.nan


def parse_log(path: Path) -> tuple[list[pd.DataFrame], list[dict]]:
    stages: list[list[dict]] = []
    totals: list[dict] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("Optimize a model"):
            stages.append([])
            totals.append({})
            continue
        if not stages:
            continue
        m = EXPLORED.search(line)
        if m:
            totals[-1] = {"seconds": float(m.group(1)), "work_units": float(m.group(2))}
            continue
        if line.startswith("Best objective"):
            totals[-1]["final_line"] = line.strip()
            continue
        tokens = line.split()
        if len(tokens) < 6:
            continue
        t = TIME_TOKEN.match(tokens[-1])
        if not t:
            continue
        stages[-1].append(
            {
                "time_s": int(t.group(1)),
                "incumbent": _num(tokens[-5]),
                "best_bound": _num(tokens[-4]),
                "gap_pct": _num(tokens[-3]),
            }
        )
    return [pd.DataFrame(rows) for rows in stages], totals


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("out", type=Path)
    args = parser.parse_args()

    rows, total_rows = [], []
    for log in sorted(args.out.glob("*.gurobi.log")):
        window = log.name.removesuffix(".gurobi.log")
        frames, totals = parse_log(log)
        for stage, (df, tot) in enumerate(zip(frames, totals), start=1):
            total_rows.append({"window": window, "stage": stage, **tot})
            if df.empty:
                continue
            df = df.dropna(subset=["incumbent"])
            final_inc = df["incumbent"].iloc[-1] if not df.empty else math.nan
            end = tot.get("seconds", math.inf)
            for cp in CHECKPOINTS:
                if cp > end + 1:
                    continue
                upto = df[df["time_s"] <= cp]
                if upto.empty:
                    rows.append({"window": window, "stage": stage, "checkpoint_s": cp})
                    continue
                last = upto.iloc[-1]
                rows.append(
                    {
                        "window": window,
                        "stage": stage,
                        "checkpoint_s": cp,
                        "incumbent": last["incumbent"],
                        "best_bound": last["best_bound"],
                        "gap_pct": last["gap_pct"],
                        "shortfall_vs_final_pct": 100 * (final_inc - last["incumbent"]) / abs(final_inc)
                        if final_inc
                        else math.nan,
                    }
                )
    sizes = []
    model_re = re.compile(r"Optimize a model with (\d+) rows, (\d+) columns and (\d+) nonzeros")
    bin_re = re.compile(r"Variable types: (\d+) continuous, (\d+) integer \((\d+) binary\)")
    for log in sorted(args.out.glob("*.gurobi.log")):
        text = log.read_text(encoding="utf-8", errors="replace")
        m, b = model_re.search(text), bin_re.search(text)
        if m:
            sizes.append({"window": log.name.removesuffix(".gurobi.log"), "rows": int(m.group(1)),
                          "columns": int(m.group(2)), "nonzeros": int(m.group(3)),
                          "binaries": int(b.group(3)) if b else None})
    pd.DataFrame(sizes).to_csv(args.out / "model_sizes.csv", index=False)
    cp = pd.DataFrame(rows)
    tot = pd.DataFrame(total_rows)
    if not tot.empty and "work_units" in tot:
        tot["work_per_s"] = tot["work_units"] / tot["seconds"]
    cp.to_csv(args.out / "trajectory_checkpoints.csv", index=False)
    tot.to_csv(args.out / "stage_totals.csv", index=False)
    with pd.option_context("display.width", 200, "display.max_rows", 500):
        print(tot.to_string(index=False))
        print(cp.round(3).to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
