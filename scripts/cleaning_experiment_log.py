import csv
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = PROJECT_ROOT / "data" / "output"

INPUT = OUT_DIR / "experiment_log_rolling.csv"
FULL_ROWS = OUT_DIR / "experiments_full.csv"
SHORT_ROWS = OUT_DIR / "experiments_short.csv"

OUT_DIR.mkdir(parents=True, exist_ok=True)

with INPUT.open("r", encoding="utf-8") as infile, \
     FULL_ROWS.open("w", newline="", encoding="utf-8") as full_out, \
     SHORT_ROWS.open("w", newline="", encoding="utf-8") as short_out:

    reader = csv.reader(infile)
    full_writer = csv.writer(full_out)
    short_writer = csv.writer(short_out)

    header = next(reader)
    full_writer.writerow(header)

    expected_len = len(header)

    for row in reader:
        if len(row) == expected_len:
            full_writer.writerow(row)
        else:
            short_writer.writerow(row)

print("Split complete.")
