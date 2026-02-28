#!/usr/bin/env python3
"""Generate FHOPS-ready scenario bundles for the MASc case-study blocks."""

from __future__ import annotations

import argparse
import csv
import math
import os
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterable

import yaml

DEFAULT_NUM_DAYS = 112
DEFAULT_LANDING_CAPACITY = 2
DEFAULT_DAILY_HOURS = 24.0
DEFAULT_SHIFT_HOURS = 8.0
DEFAULT_SHIFT_NAMES = ("S1", "S2", "S3")
DEFAULT_DAYS_PER_WEEK = 7

REPO_ROOT = Path(__file__).resolve().parents[1]

ROLE_ORDER = ("feller_buncher", "grapple_skidder", "processor", "loader")
ROLE_PREFIX = {
    "feller_buncher": "fb",
    "grapple_skidder": "sk",
    "processor": "pr",
    "loader": "ld",
}

SIZE_MACHINE_COUNTS = {"6": 6, "18": 12, "40": 24}


@dataclass(frozen=True)
class BlockRow:
    """Raw block input from the Jaffray MASc datasets."""

    id: str
    work_required: float
    volume_per_ha: float
    stem_density_per_ha: float
    area_ha: float
    ground_slope_percent: float
    harvest_system_id: str


@dataclass(frozen=True)
class ScenarioSpec:
    """Derived scenario metadata for output bundles."""

    area: str
    size: str
    num_days: int
    machine_count: int
    landing_capacity: int
    daily_hours: float

    @property
    def scenario_id(self) -> str:
        return f"{self.area}_{self.size}"


def _resolve_fhops_root(explicit: str | None) -> Path:
    if explicit:
        candidate = Path(explicit).expanduser().resolve()
        if candidate.exists():
            return candidate
        raise FileNotFoundError(candidate)
    env = os.getenv("FHOPS_ROOT")
    if env:
        candidate = Path(env).expanduser().resolve()
        if candidate.exists():
            return candidate
        raise FileNotFoundError(candidate)
    return Path(__file__).resolve().parents[2] / "fhops"


def _load_productivity_helpers(fhops_root: Path) -> dict[str, object]:
    sys.path.insert(0, str(fhops_root / "src"))
    try:
        from fhops.productivity import (
            LahrsenModel,
            estimate_grapple_skidder_productivity_adv6n7,
            estimate_loader_productivity_barko450,
            estimate_processor_productivity_berry2019,
            estimate_productivity,
        )
        from fhops.productivity.skidder_ft import ADV6N7DeckingMode
    except Exception as exc:  # pragma: no cover - surface missing deps clearly
        raise RuntimeError(
            "Failed to import FHOPS productivity helpers. "
            "Ensure FHOPS dependencies (e.g., numpy) are installed."
        ) from exc
    return {
        "LahrsenModel": LahrsenModel,
        "estimate_productivity": estimate_productivity,
        "estimate_grapple_skidder_productivity_adv6n7": estimate_grapple_skidder_productivity_adv6n7,
        "estimate_processor_productivity_berry2019": estimate_processor_productivity_berry2019,
        "estimate_loader_productivity_barko450": estimate_loader_productivity_barko450,
        "ADV6N7DeckingMode": ADV6N7DeckingMode,
    }


def _median(values: Iterable[float]) -> float:
    items = sorted(values)
    if not items:
        return 0.0
    mid = len(items) // 2
    if len(items) % 2:
        return items[mid]
    return 0.5 * (items[mid - 1] + items[mid])


def _sigma(value: float) -> float:
    return round(value * 0.2, 6)


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def _estimate_distances(area_ha: float, landing_index: int) -> tuple[float, float]:
    width_m = math.sqrt(max(area_ha, 0.01) * 10_000.0)
    mean_skid = width_m / 2.0
    distance = _clamp(mean_skid + landing_index * 30.0 + 40.0, 120.0, 900.0)
    loader_distance = _clamp(distance * 0.55, 80.0, 360.0)
    return distance, loader_distance


def _read_blocks(path: Path) -> list[BlockRow]:
    rows: list[BlockRow] = []
    with path.open(newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            rows.append(
                BlockRow(
                    id=str(row["id"]),
                    work_required=float(row["work_required"]),
                    volume_per_ha=float(row["volume_per_ha"]),
                    stem_density_per_ha=float(row["stem_density_per_ha"]),
                    area_ha=float(row["area_ha"]),
                    ground_slope_percent=(
                        float(row["ground_slope_percent"])
                        if str(row.get("ground_slope_percent", "")).strip()
                        else float("nan")
                    ),
                    harvest_system_id=str(row["harvest_system_id"]),
                )
            )
    slopes = [row.ground_slope_percent for row in rows if not math.isnan(row.ground_slope_percent)]
    fallback = _median(slopes)
    cleaned: list[BlockRow] = []
    for row in rows:
        slope = row.ground_slope_percent
        if math.isnan(slope):
            slope = fallback
        cleaned.append(
            BlockRow(
                id=row.id,
                work_required=row.work_required,
                volume_per_ha=row.volume_per_ha,
                stem_density_per_ha=row.stem_density_per_ha,
                area_ha=row.area_ha,
                ground_slope_percent=slope,
                harvest_system_id=row.harvest_system_id,
            )
        )
    return cleaned


def _normalize_block_id(raw_id: str) -> str:
    return f"B{raw_id}"


def _build_machine_counts(total: int) -> dict[str, int]:
    per_role = total // len(ROLE_ORDER)
    remainder = total % len(ROLE_ORDER)
    counts = {role: per_role for role in ROLE_ORDER}
    for idx in range(remainder):
        counts[ROLE_ORDER[idx]] += 1
    return counts


def _make_machine_rows(counts: dict[str, int], daily_hours: float) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for role in ROLE_ORDER:
        prefix = ROLE_PREFIX[role]
        for idx in range(counts[role]):
            rows.append(
                {
                    "id": f"{prefix}_{idx + 1:02d}",
                    "role": role,
                    "daily_hours": daily_hours,
                    "operating_cost": 0.0,
                }
            )
    return rows


def _estimate_role_rates(
    helpers: dict[str, object],
    block: BlockRow,
    landing_index: int,
    daily_hours: float,
) -> dict[str, float]:
    avg_stem_size = block.volume_per_ha / block.stem_density_per_ha
    skidding_distance, _loader_distance = _estimate_distances(block.area_ha, landing_index)
    estimate_productivity = helpers["estimate_productivity"]
    LahrsenModel = helpers["LahrsenModel"]
    estimate_skidder = helpers["estimate_grapple_skidder_productivity_adv6n7"]
    ADV6N7DeckingMode = helpers["ADV6N7DeckingMode"]
    estimate_processor = helpers["estimate_processor_productivity_berry2019"]
    estimate_loader = helpers["estimate_loader_productivity_barko450"]

    fb = estimate_productivity(
        avg_stem_size=avg_stem_size,
        volume_per_ha=block.volume_per_ha,
        stem_density=block.stem_density_per_ha,
        ground_slope=block.ground_slope_percent,
        model=LahrsenModel.DAILY,
        validate_ranges=False,
    )
    skidder = estimate_skidder(
        skidding_distance_m=skidding_distance,
        decking_mode=ADV6N7DeckingMode.SKIDDER_LOADER,
        payload_m3=7.69,
        utilisation=0.85,
        delay_minutes=0.12,
        support_ratio=0.4,
    )
    processor = estimate_processor(
        piece_size_m3=avg_stem_size,
        tree_form_category=0,
        delay_multiplier=0.91,
    )
    loader = estimate_loader(scenario="ground_skid_block")

    def _floor(value: float, floor: float = 1.0) -> float:
        return round(max(value, floor), 6)

    return {
        "feller_buncher": _floor(fb.predicted_m3_per_pmh * daily_hours),
        "grapple_skidder": _floor(skidder.productivity_m3_per_pmh * daily_hours),
        "processor": _floor(processor.productivity_m3_per_pmh * daily_hours),
        "loader": _floor(loader.avg_volume_per_shift_m3),
    }


def _write_csv(path: Path, fieldnames: list[str], rows: Iterable[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _write_scenario_yaml(path: Path, spec: ScenarioSpec) -> None:
    payload = {
        "name": f"MASc {spec.area.upper()} {spec.size} blocks",
        "num_days": spec.num_days,
        "schema_version": "1.0.0",
        "data": {
            "blocks": "data/blocks.csv",
            "machines": "data/machines.csv",
            "landings": "data/landings.csv",
            "calendar": "data/calendar.csv",
            "prod_rates": "data/prod_rates.csv",
        },
        "timeline": {
            "shifts": [
                {"name": name, "hours": DEFAULT_SHIFT_HOURS, "shifts_per_day": 1}
                for name in DEFAULT_SHIFT_NAMES
            ],
            "blackouts": [],
            "days_per_week": DEFAULT_DAYS_PER_WEEK,
        },
        "objective_weights": {"production": 1.0, "mobilisation": 0.5},
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(payload, handle, sort_keys=False)


def _write_manifest(path: Path, spec: ScenarioSpec, source_blocks: Path, totals: dict[str, float]) -> None:
    try:
        source_ref = str(source_blocks.resolve().relative_to(REPO_ROOT))
    except ValueError:
        source_ref = str(source_blocks)
    payload = {
        "scenario_id": spec.scenario_id,
        "area": spec.area,
        "size": spec.size,
        "num_days": spec.num_days,
        "machine_count": spec.machine_count,
        "landing_capacity": spec.landing_capacity,
        "daily_hours": spec.daily_hours,
        "blocks_source": source_ref,
        "generated_on": str(date.today()),
        "totals": totals,
        "assumptions": {
            "landing_per_block": True,
            "harvest_system_id": "ground_fb_loader_liveheel",
            "objective_weights": {"production": 1.0, "mobilisation": 0.5},
            "shift_schedule": {
                "shifts_per_day": len(DEFAULT_SHIFT_NAMES),
                "hours_per_shift": DEFAULT_SHIFT_HOURS,
                "days_per_week": DEFAULT_DAYS_PER_WEEK,
            },
            "loader_productivity_model": "barko450_ground_skid_block",
            "feller_buncher_productivity_model": "lahrsen_2025_daily",
            "skidder_productivity_model": "adv6n7",
            "processor_productivity_model": "berry_2019",
            "slope_fallback": "median_of_scenario_blocks",
        },
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(payload, handle, sort_keys=False)


def _write_bundle_manifest(path: Path, scenarios: list[dict[str, object]]) -> None:
    payload = {
        "bundle_id": "masc_case_study_3x3",
        "generated_on": str(date.today()),
        "scenarios": scenarios,
        "notes": "Nine MASc case-study scenarios compiled with consistent assumptions.",
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(payload, handle, sort_keys=False)


def _summary_stats(values: list[float]) -> dict[str, float]:
    if not values:
        return {"min": 0.0, "max": 0.0, "mean": 0.0}
    return {
        "min": min(values),
        "max": max(values),
        "mean": sum(values) / len(values),
    }


def _write_qa_summary(
    path: Path,
    spec: ScenarioSpec,
    blocks: list[BlockRow],
    block_rows: list[dict[str, object]],
    machines: list[dict[str, object]],
    landings: list[dict[str, object]],
    calendar: list[dict[str, object]],
    prod_rates: list[dict[str, object]],
) -> None:
    role_counts: dict[str, int] = {}
    for machine in machines:
        role = str(machine["role"])
        role_counts[role] = role_counts.get(role, 0) + 1

    prod_by_role: dict[str, list[float]] = {role: [] for role in ROLE_ORDER}
    for entry in prod_rates:
        role = None
        machine_id = str(entry["machine_id"])
        for machine in machines:
            if machine["id"] == machine_id:
                role = str(machine["role"])
                break
        if role is None:
            continue
        prod_by_role.setdefault(role, []).append(float(entry["rate"]))

    blocks_work = [float(row["work_required"]) for row in block_rows]
    slopes = [float(row["ground_slope_percent"]) for row in block_rows]
    volumes = [float(row["volume_per_ha_m3"]) for row in block_rows]
    densities = [float(row["stem_density_per_ha"]) for row in block_rows]
    stem_sizes = [float(row["avg_stem_size_m3"]) for row in block_rows]

    payload = {
        "scenario_id": spec.scenario_id,
        "counts": {
            "blocks": len(blocks),
            "machines": len(machines),
            "landings": len(landings),
            "calendar_rows": len(calendar),
            "prod_rate_rows": len(prod_rates),
        },
        "block_metrics": {
            "work_required": _summary_stats(blocks_work),
            "ground_slope_percent": _summary_stats(slopes),
            "volume_per_ha_m3": _summary_stats(volumes),
            "stem_density_per_ha": _summary_stats(densities),
            "avg_stem_size_m3": _summary_stats(stem_sizes),
        },
        "machine_roles": role_counts,
        "production_rates": {
            role: _summary_stats(rates) for role, rates in prod_by_role.items()
        },
        "rate_floor_count": {
            role: sum(1 for rate in prod_by_role.get(role, []) if rate <= 1.0)
            for role in ROLE_ORDER
        },
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(payload, handle, sort_keys=False)


def _write_bundle_qa_summary(path: Path, scenario_summaries: list[dict[str, object]]) -> None:
    payload = {
        "generated_on": str(date.today()),
        "scenarios": scenario_summaries,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(payload, handle, sort_keys=False)


def generate_all(
    blocks_dir: Path,
    out_dir: Path,
    num_days: int,
    landing_capacity: int,
    daily_hours: float,
    fhops_root: Path,
    validate: bool,
) -> None:
    helpers = _load_productivity_helpers(fhops_root)
    load_scenario = None
    if validate:
        sys.path.insert(0, str(fhops_root / "src"))
        try:
            from fhops.scenario.io import load_scenario as _load_scenario
        except Exception as exc:  # pragma: no cover - ensure clear failure
            raise RuntimeError("Failed to import FHOPS scenario loader for validation.") from exc
        load_scenario = _load_scenario
    scenarios_manifest: list[dict[str, object]] = []
    scenario_summaries: list[dict[str, object]] = []
    for blocks_path in sorted(blocks_dir.glob("*_*/blocks.csv")):
        folder = blocks_path.parent.name
        if "_" not in folder:
            continue
        area_raw, size = folder.split("_", 1)
        area = area_raw.lower()
        machine_count = SIZE_MACHINE_COUNTS.get(size)
        if machine_count is None:
            raise ValueError(f"Unknown size tier '{size}' from {folder}")
        spec = ScenarioSpec(
            area=area,
            size=size,
            num_days=num_days,
            machine_count=machine_count,
            landing_capacity=landing_capacity,
            daily_hours=daily_hours,
        )
        blocks = _read_blocks(blocks_path)
        landing_ids = [f"L{idx + 1:02d}" for idx in range(len(blocks))]
        block_rows: list[dict[str, object]] = []
        totals = {"total_work_required": 0.0}
        rates_by_block: dict[str, dict[str, float]] = {}
        for idx, block in enumerate(blocks):
            avg_stem_size = block.volume_per_ha / block.stem_density_per_ha
            block_id = _normalize_block_id(block.id)
            block_rows.append(
                {
                    "id": block_id,
                    "landing_id": landing_ids[idx],
                    "harvest_system_id": block.harvest_system_id,
                    "work_required": round(block.work_required, 6),
                    "earliest_start": 1,
                    "latest_finish": num_days,
                    "avg_stem_size_m3": round(avg_stem_size, 6),
                    "volume_per_ha_m3": round(block.volume_per_ha, 6),
                    "stem_density_per_ha": round(block.stem_density_per_ha, 6),
                    "ground_slope_percent": round(block.ground_slope_percent, 6),
                    "volume_per_ha_m3_sigma": _sigma(block.volume_per_ha),
                    "stem_density_per_ha_sigma": _sigma(block.stem_density_per_ha),
                }
            )
            totals["total_work_required"] += block.work_required
            rates_by_block[block_id] = _estimate_role_rates(
                helpers, block, idx, daily_hours
            )

        counts = _build_machine_counts(machine_count)
        machines = _make_machine_rows(counts, daily_hours)
        landings = [
            {"id": landing_id, "daily_capacity": landing_capacity} for landing_id in landing_ids
        ]
        calendar = [
            {"machine_id": machine["id"], "day": day, "available": 1}
            for machine in machines
            for day in range(1, num_days + 1)
        ]
        prod_rates = []
        for machine in machines:
            role = machine["role"]
            for block in blocks:
                block_id = _normalize_block_id(block.id)
                prod_rates.append(
                    {
                        "machine_id": machine["id"],
                        "block_id": block_id,
                        "rate": rates_by_block[block_id][role],
                    }
                )

        scenario_dir = out_dir / spec.scenario_id
        data_dir = scenario_dir / "data"
        _write_csv(
            data_dir / "blocks.csv",
            [
                "id",
                "landing_id",
                "harvest_system_id",
                "work_required",
                "earliest_start",
                "latest_finish",
                "avg_stem_size_m3",
                "volume_per_ha_m3",
                "stem_density_per_ha",
                "ground_slope_percent",
                "volume_per_ha_m3_sigma",
                "stem_density_per_ha_sigma",
            ],
            block_rows,
        )
        _write_csv(
            data_dir / "machines.csv",
            ["id", "role", "daily_hours", "operating_cost"],
            machines,
        )
        _write_csv(data_dir / "landings.csv", ["id", "daily_capacity"], landings)
        _write_csv(
            data_dir / "calendar.csv",
            ["machine_id", "day", "available"],
            calendar,
        )
        _write_csv(
            data_dir / "prod_rates.csv",
            ["machine_id", "block_id", "rate"],
            prod_rates,
        )
        _write_scenario_yaml(scenario_dir / "scenario.yaml", spec)
        _write_manifest(
            scenario_dir / "manifest.yaml",
            spec,
            blocks_path,
            totals,
        )
        _write_qa_summary(
            scenario_dir / "qa_summary.yaml",
            spec,
            blocks,
            block_rows,
            machines,
            landings,
            calendar,
            prod_rates,
        )
        if load_scenario is not None:
            load_scenario(scenario_dir / "scenario.yaml")
        scenarios_manifest.append(
            {
                "scenario_id": spec.scenario_id,
                "path": str(scenario_dir),
                "num_days": spec.num_days,
                "machine_count": spec.machine_count,
                "block_count": len(blocks),
                "landing_count": len(landings),
            }
        )
        scenario_summaries.append(
            {
                "scenario_id": spec.scenario_id,
                "qa_summary": str((scenario_dir / "qa_summary.yaml").relative_to(out_dir)),
            }
        )

    _write_bundle_manifest(out_dir / "manifest.yaml", scenarios_manifest)
    _write_bundle_qa_summary(out_dir / "qa_summary.yaml", scenario_summaries)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate FHOPS scenario bundles from MASc blocks datasets."
    )
    parser.add_argument(
        "--blocks-dir",
        type=Path,
        default=Path("data/input/blocks"),
        help="Directory containing <AREA>_<SIZE>/blocks.csv inputs.",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("data/input/scenarios"),
        help="Output directory for generated scenario bundles.",
    )
    parser.add_argument(
        "--num-days",
        type=int,
        default=DEFAULT_NUM_DAYS,
        help="Planning horizon length in days (default: 112).",
    )
    parser.add_argument(
        "--landing-capacity",
        type=int,
        default=DEFAULT_LANDING_CAPACITY,
        help="Daily landing capacity to apply to every landing (default: 2).",
    )
    parser.add_argument(
        "--daily-hours",
        type=float,
        default=DEFAULT_DAILY_HOURS,
        help="Daily machine availability hours (default: 24).",
    )
    parser.add_argument(
        "--fhops-root",
        type=str,
        default=None,
        help="Path to the FHOPS repository (defaults to sibling ../fhops).",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate generated scenarios with the FHOPS loader.",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    fhops_root = _resolve_fhops_root(args.fhops_root)
    generate_all(
        blocks_dir=args.blocks_dir,
        out_dir=args.out_dir,
        num_days=args.num_days,
        landing_capacity=args.landing_capacity,
        daily_hours=args.daily_hours,
        fhops_root=fhops_root,
        validate=args.validate,
    )


if __name__ == "__main__":
    main()
