from pathlib import Path


RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")
ANNOTATIONS_DIR = Path("data/annotations")
OUTPUT_CSV = PROCESSED_DIR / "output.csv"
SAMPLE_CSV = PROCESSED_DIR / "sample.csv"
ANNOTATIONS_CSV = ANNOTATIONS_DIR / "annotations.csv"

SAMPLE_RATIO = 0.20
ZONE_COLS = ["pct_z1", "pct_z2", "pct_z3", "pct_z4", "pct_z5"]
LABEL_MAP = {"e": "easy", "h": "hard", "r": "rest", "t": "training"}


TRAIN_FRAC = 0.60
VAL_FRAC = 0.20
# Reward looks up to 4 sessions ahead (parse.py: sessions[i + 1 : i + 5]),
# so the 4 sessions just before a boundary are contaminated and get dropped.
EMBARGO_SESSIONS = 4
