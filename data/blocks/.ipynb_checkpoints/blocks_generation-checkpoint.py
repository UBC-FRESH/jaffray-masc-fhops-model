import pandas as pd
from pathlib import Path

DATA_DIR = Path(r"blocks/data")
OUTPUT_BASE_DIR = Path("blocks") 

# Auto-detect datasets
DATASETS = [file.name for file in DATA_DIR.glob("*.csv")]

for dataset_file in DATASETS:

    dataset_name = dataset_file.replace(".csv", "")

    arc_table = pd.read_csv(DATA_DIR / dataset_file)

    volume_per_ha = arc_table["MEAN_LIVE_STAND_VOLUME_125"]
    area_ha = arc_table["SUM_FEATURE_AREA_HA"]
    work_required = volume_per_ha * area_ha

    blocks = pd.DataFrame({
        "id": arc_table["FID_TSA_AuthorizedBlocks"],
        "work_required": work_required,
        "volume_per_ha": volume_per_ha, 
        "stem_density_per_ha": arc_table["MEAN_VRI_LIVE_STEMS_PER_HA"],
        "area_ha": area_ha,
        "ground_slope_percent": arc_table["MEAN_MEAN"],
        "harvest_system_id": "ground_fb_loader_liveheel"
    })

    output_folder = OUTPUT_BASE_DIR / dataset_name
    output_folder.mkdir(parents=True, exist_ok=True)

    output_path = output_folder / "blocks.csv"
    blocks.to_csv(output_path, index=False)

    print(f"Saved: {output_path}")