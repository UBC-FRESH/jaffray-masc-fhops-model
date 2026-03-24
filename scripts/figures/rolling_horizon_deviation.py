import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# --------------------------------------------------
# 1. LOAD DATA
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = PROJECT_ROOT / "data" / "output"
FIG_DIR = OUT_DIR / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(OUT_DIR / "log_analysis.csv")

# Clean solver labels
df["solver"] = df["solver"].str.lower()

# --------------------------------------------------
# 2. IDENTIFY FULL-HORIZON BENCHMARKS
# --------------------------------------------------

# Full horizon = maximum theta_weeks per context-size-solver
benchmarks = (
    df.loc[
        df.groupby(["context", "size", "solver"])["theta_weeks"].idxmax()
    ][["context", "size", "solver", "objective_best"]]
    .rename(columns={"objective_best": "benchmark_objective"})
)

# Merge benchmark back into dataset
df = df.merge(
    benchmarks,
    on=["context", "size", "solver"],
    how="left"
)

# --------------------------------------------------
# 3. COMPUTE PERCENT DEVIATION
# --------------------------------------------------

df["percent_deviation"] = (
    (df["objective_best"] - df["benchmark_objective"])
    / np.abs(df["benchmark_objective"])
) * 100

# --------------------------------------------------
# 4. REMOVE FULL-HORIZON ROWS FROM PLOT
# --------------------------------------------------

max_horizon = df["theta_weeks"].max()
plot_df = df[df["theta_weeks"] < max_horizon]

# --------------------------------------------------
# 5. MULTI-PANEL FIGURE BY PROBLEM SIZE
# --------------------------------------------------

sizes = sorted(plot_df["size"].unique())

fig, axes = plt.subplots(
    nrows=1,
    ncols=len(sizes),
    figsize=(5 * len(sizes), 5),
    sharey=True
)

if len(sizes) == 1:
    axes = [axes]

for ax, size in zip(axes, sizes):

    subset = plot_df[
        (plot_df["size"] == size) &
        (plot_df["solver"] == "mip")  # usually compare MIP rolling to MIP benchmark
    ]

    grouped = subset.groupby("theta_weeks")["percent_deviation"].mean()

    ax.plot(
        grouped.index,
        grouped.values,
        marker="o"
    )

    ax.axhline(0, linestyle="--")
    ax.set_title(f"Size = {size}")
    ax.set_xlabel("Planning Horizon (weeks)")

axes[0].set_ylabel("% Deviation from Full-Horizon Benchmark")

plt.tight_layout()
plt.savefig(FIG_DIR / "rh_deviation_vs_horizon.pdf")
plt.show()

# --------------------------------------------------
# 6. PRINT SUMMARY TABLE FOR RESULTS TEXT
# --------------------------------------------------

summary_table = (
    plot_df[plot_df["solver"] == "sa"]
    .groupby(["size", "theta_weeks"])["percent_deviation"]
    .agg(["mean", "std"])
    .reset_index()
)

print("\nDeviation Summary (MIP only):")
print(summary_table)
