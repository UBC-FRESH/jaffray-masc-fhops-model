import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = PROJECT_ROOT / "data" / "output"
OUT_DIR.mkdir(parents=True, exist_ok=True)

runtime = pd.read_csv(
    OUT_DIR / "experiments_short.csv",
    header=None,
    on_bad_lines="skip",
    engine="python"
)

# Assign only the columns that exist in the file
runtime.columns = [
    "context","size","theta_weeks","sub_days","lock_days",
    "solver","success","returncode","runtime_sec",
    "col10","col11","col12","col13","col14","col15",
    "col16","col17","col18","timestamp"
]

# Keep only relevant columns
runtime = runtime[[
    "context","size","theta_weeks","sub_days","lock_days",
    "solver","success","returncode","runtime_sec"
]]

# Ensure numeric types
runtime["theta_weeks"] = pd.to_numeric(runtime["theta_weeks"])
runtime["size"] = pd.to_numeric(runtime["size"])
runtime["runtime_sec"] = pd.to_numeric(runtime["runtime_sec"])

print(runtime.head())
print(runtime.dtypes)

import matplotlib.pyplot as plt
import seaborn as sns

sns.set_theme(style="whitegrid")

plt.figure(figsize=(7,5))

sns.lineplot(
    data=runtime,
    x="theta_weeks",
    y="runtime_sec",
    hue="solver",
    marker="o",
    errorbar=None
)

plt.xlabel("Planning Horizon (weeks)")
plt.ylabel("Runtime (seconds)")
plt.title("Runtime vs Planning Horizon")

plt.tight_layout()
plt.savefig(OUT_DIR / "runtime_horizon.png", bbox_inches="tight")

plt.show()

sns.set_theme(style="whitegrid")
plt.rcParams.update({"font.size": 11})

g = sns.FacetGrid(
    runtime,
    col="theta_weeks",
    hue="solver",
    height=4,
    aspect=1.1,
    sharey=True
)

g.map_dataframe(
    sns.lineplot,
    x="lock_days",
    y="runtime_sec",
    marker="o"
)

g.add_legend(title="Solver")
g.set_axis_labels(
    "Re-Optimization Frequency (days)",
    "Runtime (seconds)"
)

for ax in g.axes.flat:
    ax.set_yscale("log")

plt.savefig(OUT_DIR / "runtime_froll.png", bbox_inches="tight", dpi=300)
plt.show()
