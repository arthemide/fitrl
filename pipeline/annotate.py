import csv
import random
from collections import defaultdict
from pathlib import Path

import pandas as pd
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

PROCESSED_DIR = Path("data/processed")
ANNOTATIONS_DIR = Path("data/annotations")
OUTPUT_CSV = PROCESSED_DIR / "output.csv"
SAMPLE_CSV = PROCESSED_DIR / "sample.csv"
ANNOTATIONS_CSV = ANNOTATIONS_DIR / "annotations.csv"

SAMPLE_RATIO = 0.20
ZONE_COLS = ["pct_z1", "pct_z2", "pct_z3", "pct_z4", "pct_z5"]
LABEL_MAP = {"e": "easy", "h": "hard", "r": "rest", "t": "training"}

console = Console()


def session_key(row: pd.Series) -> str:
    return f"{row['start_time']}|{row['sport']}"


def build_sample(df: pd.DataFrame) -> list[str]:
    by_label: dict[str, list[str]] = defaultdict(list)
    for _, row in df.iterrows():
        by_label[row["label"]].append(session_key(row))

    sample: list[str] = []
    for keys in by_label.values():
        n = max(1, round(len(keys) * SAMPLE_RATIO))
        sample.extend(random.sample(keys, min(n, len(keys))))

    random.shuffle(sample)
    return sample


def load_sample(df: pd.DataFrame) -> list[str]:
    if SAMPLE_CSV.exists():
        with open(SAMPLE_CSV) as f:
            return [r["key"] for r in csv.DictReader(f)]

    sample = build_sample(df)
    SAMPLE_CSV.parent.mkdir(parents=True, exist_ok=True)
    with open(SAMPLE_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["key"])
        writer.writeheader()
        for key in sample:
            writer.writerow({"key": key})
    return sample


def load_annotations() -> dict[str, str]:
    if not ANNOTATIONS_CSV.exists():
        return {}
    with open(ANNOTATIONS_CSV) as f:
        return {r["key"]: r["label_manual"] for r in csv.DictReader(f)}


def save_annotations(annotations: dict[str, str]) -> None:
    ANNOTATIONS_CSV.parent.mkdir(parents=True, exist_ok=True)
    with open(ANNOTATIONS_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["key", "label_manual"])
        writer.writeheader()
        for key, label in annotations.items():
            writer.writerow({"key": key, "label_manual": label})


def render_zones(row: pd.Series) -> str:
    lines = []
    for i, col in enumerate(ZONE_COLS, 1):
        pct = row[col]
        bar = "█" * int(pct / 2)
        lines.append(f"Z{i} [{bar:<50}] {pct:5.1f}%")
    return "\n".join(lines)

def format_duration(seconds: float) -> str:
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    if hours > 0:
        return f"{hours}h {minutes}m {secs}s"
    elif minutes > 0:
        return f"{minutes}m {secs}s"
    else:
        return f"{secs}s"
    
def format_distance(meters: float) -> str:
    if meters >= 1000:
        return f"{meters / 1000:.1f} km"
    else:
        return f"{meters:.0f} m"

def speed_in_min_per_km(speed: float) -> str:
    if speed <= 0:
        return "N/A"
    pace = 1000 / speed
    minutes = int(pace // 60)
    seconds = int(pace % 60)
    return f"{minutes}:{seconds:02d} min/km"

def speed_in_km_per_h(speed: float) -> str:
    return f"{speed * 3.6:.1f} km/h"

def format_speed(sport: str, speed: float) -> str:
    if sport == "running":
        return speed_in_min_per_km(speed)
    elif sport == "cycling":
        return speed_in_km_per_h(speed)
    else:
        return f"{speed:.1f} m/s"

def render_session(row: pd.Series, prev: pd.DataFrame, position: int, total: int) -> None:
    console.rule(f"[bold cyan]{position}/{total}[/bold cyan]")

    content = (
        f"[bold]{row['start_time']}[/bold]  •  {row['sport']}"
        f"  •  {format_duration(row['duration'])}  •  {format_distance(row['distance'])}\n"
        f"Avg/max HR : [yellow]{row['avg_heart_rate']} / {row['max_heart_rate']} bpm[/yellow]"
        f"   Speed : {format_speed(row['sport'], row['speed'])}\n"
        f"Label : [green]{row['label']}[/green]   Reward : [magenta]{row['reward']}[/magenta]\n\n"
        + render_zones(row)
    )
    console.print(Panel(content, expand=False))

    if not prev.empty:
        table = Table(show_header=True, header_style="bold", box=None)
        for col in ["start_time", "sport", "duration", "avg_heart_rate", "label", "reward"]:
            table.add_column(col)
        for _, p in prev.iterrows():
            table.add_row(
                str(p["start_time"]), p["sport"], format_duration(p["duration"]),
                str(p["avg_heart_rate"]), p["label"], str(p["reward"]),
            )
        console.print(table)


def main() -> None:
    df = pd.read_csv(OUTPUT_CSV)
    df["start_time"] = pd.to_datetime(df["start_time"])
    df["_key"] = df.apply(session_key, axis=1)
    key_to_row = {row["_key"]: row for _, row in df.iterrows()}

    sample = load_sample(df)
    annotations = load_annotations()
    unannotated = [k for k in sample if k not in annotations]

    total = len(sample)
    console.print(f"\n[bold]Annotation CLI[/bold] — {len(annotations)}/{total} annotated\n")

    if not unannotated:
        console.print("[green]All sessions annotated.[/green]")
        return

    for key in unannotated:
        if key not in key_to_row:
            continue

        row = key_to_row[key]
        prev = (
            df[(df["sport"] == row["sport"]) & (df["start_time"] < row["start_time"])]
            .sort_values("start_time")
            .tail(5)
        )

        render_session(row, prev, len(annotations) + 1, total)

        label_calc = row["label"]
        raw = console.input(
            f"\n[dim]Enter=confirm '{label_calc}' / e·h·r·t / q to quit[/dim] > "
        ).strip().lower()

        if raw == "q":
            break

        new_label = LABEL_MAP.get(raw, label_calc)
        annotations[key] = new_label
        save_annotations(annotations)

        marker = " [yellow](corrected)[/yellow]" if new_label != label_calc else ""
        console.print(f"  → [green]{new_label}[/green]{marker}\n")

    done = len(annotations)
    console.print(f"\n[bold green]{done}/{total} annotated[/bold green]")


if __name__ == "__main__":
    main()
