import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path

import seaborn as sns

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = PROJECT_ROOT / "data" / "output"
OUT_DIR.mkdir(parents=True, exist_ok=True)

master = pd.read_csv(OUT_DIR / "rolling_summary_clean.csv")

continuity = pd.read_csv(
    OUT_DIR / "continuity" / "continuity_metrics_by_configuration.csv"
)

continuity["theta_weeks"] = continuity["subproblem_days"] / 7
continuity["f_roll_days"] = continuity["lock_days"]

master = master.merge(
    continuity[[
        "scenario","solver",
        "theta_weeks","f_roll_days",
        "continuity_index"
    ]],
    on=["scenario","solver","theta_weeks","f_roll_days"],
    how="left"
)

print(master.columns)

sns.set_theme(style="whitegrid")
plt.figure(figsize=(8,6))

# Scale marker sizes by f_roll_days
size_mapping = {1: 200, 7: 120, 14: 80}
master["marker_size"] = master["f_roll_days"].map(size_mapping)

sns.scatterplot(
    data=master,
    x="gap_percent",
    y="continuity_index",
    hue="solver",
    style="theta_weeks",
    s=120
)

plt.xlabel("Objective Deviation (%)")
plt.ylabel("Continuity (%)")
plt.title("Quality–Continuity Trade-Off Across Rolling Configurations")

plt.legend(title="Solver / Horizon", bbox_to_anchor=(1.05,1))
plt.tight_layout()
plt.show()
plt.savefig(OUT_DIR / "continuity_quality.png", bbox_inches="tight")
