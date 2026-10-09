#!/usr/bin/env python3
"""Time one rolling-horizon MILP window on FHOPS 1.0.1 (feasibility probe for the re-run grid).

Solves only the first window of a rolling configuration (``max_iterations=1``) with the same
settings as ``rolling_rerun_v101.py`` (cold HiGHS, 1 thread, earliness stage on) and writes a
small JSON with wall time, window status and locked/planned delivery. Wrap it in
``/usr/bin/time -v`` to record peak memory.

``--solver gurobi`` needs ``gurobipy`` and a full Gurobi licence (the pip-bundled licence is
size-limited).

Usage
-----
    /usr/bin/time -v python scripts/probe_mip_window_v101.py ka 40 --sub 14 --lock 7 \
        --out data/output/rerun_v101_probe/ka_40_sub14_lock7.json
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("context")
    parser.add_argument("size")
    parser.add_argument("--sub", type=int, default=14)
    parser.add_argument("--lock", type=int, default=7)
    parser.add_argument("--time-limit", type=int, default=1800)
    parser.add_argument("--earliness-time-limit", type=int, default=300)
    parser.add_argument("--solver", default="highs", help="MILP backend passed to FHOPS (highs or gurobi)")
    parser.add_argument("--threads", type=int, default=1)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    import fhops
    from fhops.planning import solve_rolling_plan, summarize_plan
    from fhops.scenario.io import load_scenario

    path = PROJECT_ROOT / "data" / "input" / "scenarios" / f"{args.context}_{args.size}" / "scenario.yaml"
    scenario = load_scenario(str(path))
    start = time.time()
    result = solve_rolling_plan(
        scenario,
        master_days=int(scenario.num_days),
        subproblem_days=args.sub,
        lock_days=args.lock,
        solver="mip",
        mip_solver=args.solver,
        mip_time_limit=args.time_limit,
        mip_solver_options={"threads": args.threads},
        mip_earliness=True,
        mip_earliness_time_limit=args.earliness_time_limit,
        max_iterations=1,
    )
    wall = time.time() - start
    summary = summarize_plan(result)
    payload = {
        "fhops_version": fhops.__version__,
        "context": args.context,
        "size": args.size,
        "sub_days": args.sub,
        "lock_days": args.lock,
        "solver": args.solver,
        "threads": args.threads,
        "time_limit_s": args.time_limit,
        "earliness_time_limit_s": args.earliness_time_limit,
        "wall_time_s": wall,
        "summary": json.loads(json.dumps(summary, default=str)),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in payload.items() if k != "summary"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
