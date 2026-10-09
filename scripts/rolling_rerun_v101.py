#!/usr/bin/env python3
"""Re-run the Chapter 4 rolling-horizon grid on FHOPS 1.0.1 with stitched-plan evaluation.

Why this exists
---------------
FHOPS <= 1.0.0 carried no state between rolling-horizon windows (UBC-FRESH/fhops#90, #92), and the
original Chapter 4 analysis scored each run by the objective of its *last* window. This runner
repeats the same experiment grid on the fixed FHOPS release and scores every run on its
**stitched** locked plan, replayed against the full base scenario with deterministic playback
(``fhops.evaluation.metrics.kpis.compute_kpis``). A full-horizon solve with the same solver is run
for each scenario as the baseline (``master = sub = lock = num_days``).

Grid (identical to ``scripts/rolling_experiments.py``)
------------------------------------------------------
contexts {pg, ka, ni} x sizes {6, 18, 40} x theta {2, 4, 8, 16} weeks x lock {1, 7, 14} days x
solvers {sa (500 iters, seed 42), mip (HiGHS or Gurobi via ``--mip-solver``, 1800 s per window)}
= 216 runs + 18 baselines.

Outputs (``--out-root``, default ``data/output/rerun_v101``)
------------------------------------------------------------
- ``runs/<run_id>.json``: config, FHOPS version/commit, wall time, iteration summaries, KPIs.
- ``runs/<run_id>_assignments.csv``: stitched locked assignments.
- ``runs/<run_id>.log``: captured stdout/stderr of the worker.
- ``summary.csv``: one row per completed run (rebuilt with ``--summarize``).

Runs are resumable: a run whose JSON exists is skipped. Each worker is a fresh process and HiGHS
is limited to one thread, so ``--workers`` maps to physical cores.

Usage
-----
    python scripts/rolling_rerun_v101.py --dry-run
    python scripts/rolling_rerun_v101.py --smoke --workers 8          # quick pipeline check
    nohup python scripts/rolling_rerun_v101.py --workers 70 > rerun.log 2>&1 &
    python scripts/rolling_rerun_v101.py --summarize
"""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import subprocess
import sys
import time
import traceback
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
INPUT_ROOT = PROJECT_ROOT / "data" / "input" / "scenarios"

CONTEXTS = ["pg", "ka", "ni"]
SIZES = ["6", "18", "40"]
THETA_WEEKS = [2, 4, 8, 16]
LOCK_DAYS = [1, 7, 14]
SOLVERS = ["sa", "mip"]

SA_ITERS = 500
SA_SEED = 42
MIP_SOLVER = "highs"
MIP_TIME_LIMIT = 1800


@dataclass(frozen=True)
class RunSpec:
    """One rolling-horizon run (or a full-horizon baseline when ``baseline`` is true)."""

    context: str
    size: str
    solver: str
    master_days: int
    sub_days: int
    lock_days: int
    theta_weeks: int | None
    baseline: bool
    sa_iters: int
    mip_time_limit: int
    mip_earliness_time_limit: int = 300
    mip_solver: str = MIP_SOLVER

    @property
    def scenario_id(self) -> str:
        return f"{self.context}_{self.size}"

    @property
    def run_id(self) -> str:
        if self.baseline:
            return f"{self.scenario_id}_baseline_{self.solver}"
        return f"{self.scenario_id}_sub{self.sub_days}_lock{self.lock_days}_{self.solver}"

    @property
    def cost_rank(self) -> float:
        """Rough expected cost used to start the longest jobs first."""
        windows = max(1, self.master_days // max(1, self.lock_days))
        per_window = self.mip_time_limit if self.solver == "mip" else 30
        return windows * per_window * int(self.size)


def scenario_path(context: str, size: str) -> Path:
    return INPUT_ROOT / f"{context}_{size}" / "scenario.yaml"


def num_days_of(path: Path) -> int:
    from fhops.scenario.io import load_scenario

    return int(load_scenario(str(path)).num_days)


def build_specs(args: argparse.Namespace) -> list[RunSpec]:
    specs: list[RunSpec] = []
    sa_iters = 50 if args.smoke else SA_ITERS
    mip_limit = 30 if args.smoke else MIP_TIME_LIMIT
    early_limit = min(args.mip_earliness_time_limit, mip_limit)
    contexts = args.contexts or (["ka"] if args.smoke else CONTEXTS)
    sizes = args.sizes or (["6"] if args.smoke else SIZES)
    thetas = [2, 4] if args.smoke else THETA_WEEKS
    locks = [7, 14] if args.smoke else LOCK_DAYS
    for context in contexts:
        for size in sizes:
            path = scenario_path(context, size)
            if not path.exists():
                print(f"SKIP missing scenario {path}")
                continue
            days = num_days_of(path)
            master = 28 if args.smoke else days
            for solver in args.solvers or SOLVERS:
                specs.append(
                    RunSpec(
                        context, size, solver, master, master, master, None, True, sa_iters, mip_limit, early_limit,
                        args.mip_solver,
                    )
                )
                if args.only_baselines:
                    continue
                for theta in thetas:
                    sub = min(theta * 7, master)
                    for lock in locks:
                        if lock > sub:
                            continue
                        specs.append(
                            RunSpec(
                                context, size, solver, master, sub, lock, theta, False, sa_iters, mip_limit,
                                early_limit, args.mip_solver,
                            )
                        )
    return specs


def fhops_provenance() -> dict[str, str | None]:
    import fhops

    src = Path(fhops.__file__).resolve().parent
    commit = None
    with contextlib.suppress(Exception):
        commit = subprocess.run(
            ["git", "-C", str(src), "rev-parse", "HEAD"], capture_output=True, text=True, check=True
        ).stdout.strip()
    return {"fhops_version": getattr(fhops, "__version__", None), "fhops_commit": commit, "fhops_path": str(src)}


def _jsonable(value):
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    with contextlib.suppress(Exception):
        return float(value)
    return str(value)


def run_one(spec: RunSpec, runs_dir: str) -> tuple[str, str]:
    """Execute one spec in a worker process; returns (run_id, status)."""
    runs = Path(runs_dir)
    out_json = runs / f"{spec.run_id}.json"
    log_path = runs / f"{spec.run_id}.log"
    with log_path.open("w", encoding="utf-8") as log, contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
        try:
            from fhops.evaluation.metrics.kpis import compute_kpis
            from fhops.planning import rolling_assignments_dataframe, solve_rolling_plan, summarize_plan
            from fhops.scenario.contract import Problem
            from fhops.scenario.io import load_scenario

            scenario = load_scenario(str(scenario_path(spec.context, spec.size)))
            start = time.time()
            result = solve_rolling_plan(
                scenario,
                master_days=spec.master_days,
                subproblem_days=spec.sub_days,
                lock_days=spec.lock_days,
                solver=spec.solver,
                sa_iters=spec.sa_iters,
                sa_seed=SA_SEED,
                mip_solver=spec.mip_solver,
                mip_time_limit=spec.mip_time_limit,
                mip_solver_options={"threads": 1},
                mip_earliness=True,
                mip_earliness_time_limit=spec.mip_earliness_time_limit,
            )
            wall = time.time() - start
            assignments = rolling_assignments_dataframe(result)
            assignments.to_csv(runs / f"{spec.run_id}_assignments.csv", index=False)
            kpis = compute_kpis(Problem.from_scenario(scenario), assignments)
            payload = {
                "run_id": spec.run_id,
                "spec": asdict(spec),
                "provenance": fhops_provenance(),
                "wall_time_s": wall,
                "n_locked_assignments": int(len(assignments)),
                "plan_summary": _jsonable(summarize_plan(result)),
                "kpis": _jsonable(dict(kpis)),
                "objective_weights": _jsonable(
                    scenario.objective_weights.model_dump() if scenario.objective_weights else None
                ),
                "status": "ok",
            }
            tmp = out_json.with_suffix(".json.tmp")
            tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
            tmp.replace(out_json)
            return spec.run_id, "ok"
        except Exception:  # noqa: BLE001 - record and continue the grid
            traceback.print_exc()
            (runs / f"{spec.run_id}.failed").write_text(traceback.format_exc(), encoding="utf-8")
            return spec.run_id, "failed"


def summarize(out_root: Path) -> Path:
    import pandas as pd

    rows = []
    for path in sorted((out_root / "runs").glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        row = {"run_id": data["run_id"], **data["spec"], "wall_time_s": data["wall_time_s"]}
        row.update(data.get("provenance", {}))
        iterations = data["plan_summary"].get("iterations", [])
        row["n_iterations"] = len(iterations)
        row["n_locked_assignments"] = data.get("n_locked_assignments")
        row["empty_plan"] = data.get("n_locked_assignments") == 0
        row["n_iteration_warnings"] = sum(len(it.get("warnings") or []) for it in iterations)
        statuses = [it.get("status") for it in iterations]
        row["n_no_solution_windows"] = sum(1 for st in statuses if st == "no_solution")
        row["n_skipped_windows"] = sum(1 for st in statuses if st == "skipped")
        row["n_empty_windows"] = sum(1 for it in iterations if it.get("empty"))
        row["last_window_objective"] = iterations[-1].get("objective") if iterations else None
        for key, value in data["kpis"].items():
            if isinstance(value, (int, float)) or value is None:
                row[f"kpi_{key}"] = value
        rows.append(row)
    df = pd.DataFrame(rows)
    out = out_root / "summary.csv"
    df.to_csv(out, index=False)
    print(f"Wrote {out} ({len(df)} runs)")
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out-root", type=Path, default=None, help="default data/output/rerun_v101[_<mip-solver>]")
    parser.add_argument(
        "--mip-solver",
        default=MIP_SOLVER,
        choices=["highs", "gurobi"],
        help="MILP backend for the MIP arm (gurobi needs gurobipy and a full licence)",
    )
    parser.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 2))
    parser.add_argument("--contexts", nargs="*")
    parser.add_argument("--sizes", nargs="*")
    parser.add_argument("--solvers", nargs="*", choices=SOLVERS)
    parser.add_argument("--only-baselines", action="store_true")
    parser.add_argument(
        "--mip-earliness-time-limit",
        type=int,
        default=300,
        help="time limit (s) for the MILP earliness stage-2 solve in rolling windows (FHOPS 1.0.1)",
    )
    parser.add_argument(
        "--large-mip-workers",
        type=int,
        default=6,
        help="max concurrent MIP runs on size-40 scenarios (memory guard; large MILP builds use tens of GB)",
    )
    parser.add_argument("--smoke", action="store_true", help="tiny grid with short limits (pipeline check)")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--summarize", action="store_true", help="only rebuild summary.csv")
    args = parser.parse_args()

    if args.out_root is None:
        suffix = "" if args.mip_solver == "highs" else f"_{args.mip_solver}"
        args.out_root = PROJECT_ROOT / "data" / "output" / (f"rerun_v101{suffix}" + ("_smoke" if args.smoke else ""))
    runs_dir = args.out_root / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    if args.summarize:
        summarize(args.out_root)
        return 0

    prov = fhops_provenance()
    print(f"FHOPS {prov['fhops_version']} @ {prov['fhops_commit']} ({prov['fhops_path']})")
    specs = build_specs(args)
    pending = [s for s in specs if not (runs_dir / f"{s.run_id}.json").exists()]
    pending.sort(key=lambda s: s.cost_rank, reverse=True)
    print(f"{len(specs)} specs, {len(pending)} pending, workers={args.workers}")
    if args.dry_run:
        for spec in pending:
            print(spec.run_id)
        return 0

    (args.out_root / "manifest.json").write_text(
        json.dumps({"provenance": prov, "specs": [asdict(s) for s in specs]}, indent=2), encoding="utf-8"
    )
    failures = 0
    large = [s for s in pending if s.solver == "mip" and s.size == "40"]
    other = [s for s in pending if not (s.solver == "mip" and s.size == "40")]
    large_workers = max(1, min(args.large_mip_workers, args.workers))
    other_workers = max(1, args.workers - large_workers) if large else args.workers
    print(f"pools: large-MIP {len(large)} specs x {large_workers} workers; other {len(other)} x {other_workers}")
    with ProcessPoolExecutor(max_workers=large_workers, max_tasks_per_child=1) as large_pool, ProcessPoolExecutor(
        max_workers=other_workers, max_tasks_per_child=1
    ) as other_pool:
        futures = {large_pool.submit(run_one, spec, str(runs_dir)): spec for spec in large}
        futures.update({other_pool.submit(run_one, spec, str(runs_dir)): spec for spec in other})
        for done, future in enumerate(as_completed(futures), start=1):
            run_id, status = future.result()
            failures += status != "ok"
            print(f"[{done}/{len(pending)}] {run_id}: {status}", flush=True)
    summarize(args.out_root)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
