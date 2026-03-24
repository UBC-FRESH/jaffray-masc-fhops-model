import pandas as pd
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = PROJECT_ROOT / "data" / "output"
BASE_DIR = OUT_DIR

# ------------------------------------------------------------
# 1️⃣ LOAD ALL JSON FILES (OBJECTIVES + METADATA)
# ------------------------------------------------------------

json_records = []

for file in BASE_DIR.rglob("*.json"):
    with open(file, "r") as f:
        data = json.load(f)

    metadata = data["metadata"]
    iterations = data["iterations"]

    final_obj = iterations[-1]["objective"]

    json_records.append({
        "scenario": metadata["scenario"],
        "solver": metadata["solver"],
        "subproblem_days": metadata["subproblem_days"],
        "lock_days": metadata["lock_days"],
        "master_days": metadata["master_days"],
        "final_objective": final_obj
    })

json_df = pd.DataFrame(json_records)

json_df["theta_weeks"] = json_df["subproblem_days"] / 7
json_df["f_roll_days"] = json_df["lock_days"]

# ------------------------------------------------------------
# 2️⃣ LOAD ALL ASSIGNMENT FILES
# ------------------------------------------------------------

assign_records = []

for file in BASE_DIR.rglob("*assignment*.csv"):
    df_temp = pd.read_csv(file)

    # Keep only assigned rows
    df_temp = df_temp[df_temp["assigned"] == 1]

    # Drop duplicates
    df_temp = df_temp.drop_duplicates()

    assign_records.append(df_temp)

assign_df = pd.concat(assign_records, ignore_index=True)

# ------------------------------------------------------------
# 3️⃣ RECONSTRUCT ROLLING ITERATIONS
# ------------------------------------------------------------

assign_df["iteration"] = (
    assign_df.groupby(
        ["scenario","solver","subproblem_days","lock_days"]
    )["start_day"]
    .rank(method="dense")
)

# ------------------------------------------------------------
# 4️⃣ COMPUTE TRUE STABILITY
# ------------------------------------------------------------

def compute_stability(group):
    group = group.sort_values("iteration")
    iterations = sorted(group["iteration"].unique())

    total = 0
    unchanged = 0

    for i in range(len(iterations) - 1):
        it1 = group[group["iteration"] == iterations[i]]
        it2 = group[group["iteration"] == iterations[i+1]]

        start_day = it1["start_day"].iloc[0]
        lock_days = it1["lock_days"].iloc[0]

        locked_days = list(range(start_day, start_day + lock_days))

        it1_locked = it1[it1["day"].isin(locked_days)]
        it2_locked = it2[it2["day"].isin(locked_days)]

        merged = it1_locked.merge(
            it2_locked,
            on=["block_id","day"],
            suffixes=("_old","_new")
        )

        total += len(merged)
        unchanged += (
            merged["machine_id_old"] ==
            merged["machine_id_new"]
        ).sum()

    return unchanged / total if total > 0 else 1

stability_df = (
    assign_df.groupby(
        ["scenario","solver","subproblem_days","lock_days"]
    )
    .apply(compute_stability)
    .reset_index(name="stability")
)

# ------------------------------------------------------------
# 5️⃣ MERGE OBJECTIVES + STABILITY
# ------------------------------------------------------------

summary = json_df.merge(
    stability_df,
    on=["scenario","solver","subproblem_days","lock_days"]
)

# ------------------------------------------------------------
# 6️⃣ EXTRACT DATASET SIZE FROM SCENARIO NAME
# ------------------------------------------------------------

summary["num_blocks"] = (
    summary["scenario"]
    .str.extract(r"(\d+)")
    .astype(int)
)

def size_label(n):
    if n <= 6:
        return "small"
    elif n <= 18:
        return "medium"
    else:
        return "large"

summary["dataset_size"] = summary["num_blocks"].apply(size_label)

# ------------------------------------------------------------
# 7️⃣ IDENTIFY FULL-HORIZON BENCHMARKS
# ------------------------------------------------------------

benchmark_df = (
    summary.groupby(["scenario","solver"])
    ["final_objective"]
    .min()
    .reset_index()
    .rename(columns={"final_objective":"benchmark_objective"})
)

summary = summary.merge(
    benchmark_df,
    on=["scenario","solver"]
)

summary["gap_percent"] = 100 * (
    abs(summary["final_objective"] -
        summary["benchmark_objective"])
    / abs(summary["benchmark_objective"])
)
# ------------------------------------------------------------
# 9️⃣ CLEAN OUTPUT
# ------------------------------------------------------------

summary = summary[
    [
        "scenario",
        "dataset_size",
        "solver",
        "theta_weeks",
        "f_roll_days",
        "final_objective",
        "benchmark_objective",
        "gap_percent",
        "stability"
    ]
]

summary = summary.sort_values(
    ["dataset_size","solver","theta_weeks","f_roll_days"]
)

OUT_DIR.mkdir(parents=True, exist_ok=True)
summary.to_csv(OUT_DIR / "rolling_summary_clean.csv", index=False)

print("Summary table created successfully.")

print(
    summary
    .groupby("theta_weeks")[["gap_percent","stability"]]
    .mean()
)

assign_df.groupby(
    ["scenario","solver","subproblem_days","lock_days"]
)["iteration"].nunique().head(10)


assign_df.groupby(
    ["scenario","solver","subproblem_days","lock_days"]
)["start_day"].unique().head(10)


print(summary[[
    "scenario",
    "solver",
    "theta_weeks",
    "final_objective",
    "benchmark_objective"
]].head(10))
