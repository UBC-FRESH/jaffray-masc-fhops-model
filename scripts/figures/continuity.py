import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = PROJECT_ROOT / "data" / "output"
BASE_DIR = OUT_DIR
CONTINUITY_DIR = OUT_DIR / "continuity"
CONTINUITY_DIR.mkdir(parents=True, exist_ok=True)

assign_records = []

# -------------------------------------------------
# 1️⃣ Load ALL assignment files
# -------------------------------------------------

for file in BASE_DIR.rglob("*assignment*.csv"):
    df_temp = pd.read_csv(file)

    df_temp = df_temp[df_temp["assigned"] == 1].drop_duplicates()

    assign_records.append(df_temp)

assign_df = pd.concat(assign_records, ignore_index=True)

# -------------------------------------------------
# 2️⃣ Compute continuity per configuration
# -------------------------------------------------

def continuity_metrics(group):
    group = group.sort_values(["block_id", "day"])

    block_results = []

    for block_id, g in group.groupby("block_id"):
        g = g.sort_values("day")

        machines = g["machine_id"].tolist()

        if len(machines) < 2:
            block_results.append({
                "block_id": block_id,
                "switch_rate": 0.0
            })
            continue

        switches = sum(
            machines[i] != machines[i-1]
            for i in range(1, len(machines))
        )

        transitions = len(machines) - 1
        switch_rate = switches / transitions if transitions > 0 else 0.0

        block_results.append({
            "block_id": block_id,
            "switch_rate": switch_rate
        })

    out = pd.DataFrame(block_results)

    mean_switch_rate = out["switch_rate"].mean()

    return pd.Series({
        "mean_switch_rate": mean_switch_rate,
        "continuity_index": 1 - mean_switch_rate
    })

continuity_df = (
    assign_df.groupby([
        "scenario",
        "solver",
        "subproblem_days",
        "lock_days"
    ])
    .apply(continuity_metrics)
    .reset_index()
)

# Add horizon in weeks
continuity_df["theta_weeks"] = continuity_df["subproblem_days"] / 7
continuity_df["f_roll_days"] = continuity_df["lock_days"]

print("Continuity table created.")
print(continuity_df.head())

print(
    continuity_df.groupby("theta_weeks")["continuity_index"]
    .mean()
    .round(3)
)

print(
    continuity_df.groupby("f_roll_days")["continuity_index"]
    .mean()
    .round(3)
)

print(
    continuity_df.groupby(["solver","theta_weeks"])["continuity_index"]
    .mean()
    .round(3)
)

# Full configuration-level metrics
continuity_df.to_csv(CONTINUITY_DIR / "continuity_metrics_by_configuration.csv", index=False)

# Aggregated summaries
continuity_df.groupby("theta_weeks")["continuity_index"] \
    .mean().reset_index() \
    .to_csv(CONTINUITY_DIR / "continuity_by_theta.csv", index=False)

continuity_df.groupby("f_roll_days")["continuity_index"] \
    .mean().reset_index() \
    .to_csv(CONTINUITY_DIR / "continuity_by_froll.csv", index=False)

continuity_df.groupby(["solver","theta_weeks"])["continuity_index"] \
    .mean().reset_index() \
    .to_csv(CONTINUITY_DIR / "continuity_by_solver_theta.csv", index=False)

print("All continuity outputs saved successfully.")
