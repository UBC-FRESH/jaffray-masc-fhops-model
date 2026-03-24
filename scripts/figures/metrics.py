import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = PROJECT_ROOT / "data" / "output"
FIG_DIR = OUT_DIR / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(OUT_DIR / "parsed_dataset.csv")

df_gap = df[df["benchmark_objective"].notna()].copy()

theta_order = sorted(df["theta_weeks"].dropna().unique())
sub_order = sorted(df["sub_days"].dropna().unique())
size_order = sorted(df["size"].dropna().unique())

fig, axes = plt.subplots(1, len(size_order), figsize=(4 * len(size_order), 3.5), sharey=True)

if len(size_order) == 1:
    axes = [axes]

for j, size in enumerate(size_order):
    ax = axes[j]
    sub = df_gap[df_gap["size"] == size]

    for sub_days in sub_order:
        g = (
            sub[sub["sub_days"] == sub_days]
            .groupby("theta_weeks", as_index=False)["benchmark_gap_pct"]
            .mean()
            .sort_values("theta_weeks")
        )
        if not g.empty:
            ax.plot(g["theta_weeks"], g["benchmark_gap_pct"], marker="o", label=f"sub={sub_days}")

    ax.axhline(0, linewidth=0.8)
    ax.set_xticks(theta_order)
    ax.set_title(f"Size = {size}")
    ax.set_xlabel("Planning horizon (weeks)")

axes[0].set_ylabel("Benchmark gap (%)")
handles, labels = axes[0].get_legend_handles_labels()
fig.legend(handles, labels, loc="upper center", ncol=len(sub_order), frameon=False)

fig.tight_layout(rect=[0, 0, 1, 0.92])
fig.savefig(FIG_DIR / "performance.png", bbox_inches="tight")

fig, axes = plt.subplots(1, len(size_order), figsize=(4 * len(size_order), 3.5), sharey=True)

if len(size_order) == 1:
    axes = [axes]

for j, size in enumerate(size_order):
    ax = axes[j]
    sub = df[df["size"] == size]

    for sub_days in sub_order:
        g = (
            sub[sub["sub_days"] == sub_days]
            .groupby("theta_weeks", as_index=False)["total_locked_assignments"]
            .mean()
            .sort_values("theta_weeks")
        )
        if not g.empty:
            ax.plot(g["theta_weeks"], g["total_locked_assignments"], marker="o", label=f"sub={sub_days}")

    ax.set_xticks(theta_order)
    ax.set_title(f"Size = {size}")
    ax.set_xlabel("Planning horizon (weeks)")

axes[0].set_ylabel("Total locked assignments")
handles, labels = axes[0].get_legend_handles_labels()
fig.legend(handles, labels, loc="upper center", ncol=len(sub_order), frameon=False)

fig.tight_layout(rect=[0, 0, 1, 0.92])
fig.savefig(FIG_DIR / "stability.png", bbox_inches="tight")

df_gap["performance_ratio"] = (
    df_gap["objective_final"] / df_gap["benchmark_objective"]
)
fig, axes = plt.subplots(1, len(size_order), figsize=(4 * len(size_order), 3.8), sharey=True)

if len(size_order) == 1:
    axes = [axes]

for j, size in enumerate(size_order):
    ax = axes[j]
    sub = df_gap[df_gap["size"] == size]

    data = [
        sub.loc[sub["theta_weeks"] == th, "performance_ratio"].dropna().values
        for th in theta_order
    ]

    ax.boxplot(data, positions=np.arange(len(theta_order)) + 1, widths=0.6)
    ax.set_xticks(np.arange(len(theta_order)) + 1)
    ax.set_xticklabels(theta_order)
    ax.axhline(1.0, linewidth=0.8)

    ax.set_title(f"Size = {size}")
    ax.set_xlabel("Planning horizon (weeks)")

axes[0].set_ylabel("Performance ratio to benchmark")

fig.tight_layout()
fig.savefig(FIG_DIR / "convergence.png", bbox_inches="tight")

fig, axes = plt.subplots(2, len(size_order), figsize=(4 * len(size_order), 7), sharex=True)

for j, size in enumerate(size_order):

    # Quality panel
    ax = axes[0, j]
    sub = df_gap[df_gap["size"] == size]

    for th in theta_order:
        g = (
            sub[sub["theta_weeks"] == th]
            .groupby("sub_days", as_index=False)["benchmark_gap_pct"]
            .mean()
            .sort_values("sub_days")
        )
        if not g.empty:
            ax.plot(g["sub_days"], g["benchmark_gap_pct"], marker="o", label=f"θ={th}")

    ax.axhline(0, linewidth=0.8)
    ax.set_title(f"Quality, Size={size}")
    ax.set_ylabel("Benchmark gap (%)")

    # Runtime panel
    ax = axes[1, j]
    for th in theta_order:
        g = (
            df[df["size"] == size]
            .loc[df["theta_weeks"] == th]
            .groupby("sub_days", as_index=False)["runtime_sec"]
            .mean()
            .sort_values("sub_days")
        )
        if not g.empty:
            ax.plot(g["sub_days"], g["runtime_sec"], marker="o", label=f"θ={th}")

    ax.set_yscale("log")
    ax.set_title(f"Runtime, Size={size}")
    ax.set_xlabel("Re-optimization frequency (days)")
    ax.set_ylabel("Runtime (s)")

handles, labels = axes[0, 0].get_legend_handles_labels()
fig.legend(handles, labels, loc="upper center", ncol=min(len(theta_order), 4), frameon=False)

fig.tight_layout(rect=[0, 0, 1, 0.95])
fig.savefig(FIG_DIR / "tradeoff.png", bbox_inches="tight")
