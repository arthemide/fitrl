import json
from datetime import date as Date
from datetime import timedelta
from pathlib import Path

import pandas as pd
from pydantic import BaseModel, Field

from pipeline.config import OUTPUT_CSV, PROCESSED_DIR
from pipeline.pydantic import Labels, Zones
from pipeline.split import Split

WINDOW = 5

PROMPT_TEMPLATE = """\
You are a running coach. Given the athlete's last {window} days, predict tomorrow's optimal decision.

Each day shows: label (what they did), duration in minutes, dominant HR zone.
Rest days have no duration or zone.

## Last {window} days
{days}

## Task

Respond with ONLY a JSON object. No explanation.
Valid decisions: "rest", "easy", "hard"

{{"decision":
"""


class DayFeatures(BaseModel):
    label: Labels = Field(Labels.REST, description="The label for the day")
    duration_min: int = Field(0, description="Total duration in minutes")
    dominant_zone: Zones | None = Field(None, description="The dominant HR zone")

    def format(self) -> str:
        if self.label == Labels.REST:
            return "rest"
        return f"{self.label.value} | {self.duration_min}min | {self.dominant_zone.value if self.dominant_zone else 'N/A'}"


def build_day_features(output_df: pd.DataFrame) -> dict[str, DayFeatures]:
    """Group output.csv by date -> {date_str: DayFeatures} with collapse."""
    output_df = output_df.copy()
    output_df["date"] = pd.to_datetime(output_df["start_time"]).dt.date.astype(str)
    features_by_date: dict[str, DayFeatures] = {}
    for dt, group in output_df.groupby("date"):
        total_duration = int(group["duration"].sum() // 60)
        zone_totals = group[[f"pct_z{z}" for z in range(1, 6)]].sum()
        dominant_zone = f"Z{zone_totals.values.argmax() + 1}"
        label = "hard" if "hard" in group["label"].values else "easy"
        features_by_date[str(dt)] = DayFeatures(
            duration_min=total_duration,
            dominant_zone=Zones(dominant_zone),
            label=Labels(label),
        )
    return features_by_date


def fill_rest_days(features_by_date: dict[str, DayFeatures]) -> None:
    """Fill every missing calendar day with a rest entry."""
    dates = sorted(features_by_date.keys())
    first, last = Date.fromisoformat(dates[0]), Date.fromisoformat(dates[-1])
    day = first
    while day <= last:
        key = day.isoformat()
        if key not in features_by_date:
            features_by_date[key] = DayFeatures()
        day += timedelta(days=1)


def format_prompt(window: list[DayFeatures]) -> str:
    """Format a prompt for the LLM given a window of DayFeatures."""
    lines = [f"Day -{len(window) - i}: {f.format()}" for i, f in enumerate(window)]
    return PROMPT_TEMPLATE.format(window=WINDOW, days="\n".join(lines))


def build_samples(
    features_by_date: dict[str, DayFeatures], split_dates: set[str]
) -> list[dict[str, str]]:
    """Build prompt/completion pairs for dates in split_dates."""
    calendar = sorted(features_by_date.keys())
    samples: list[dict[str, str]] = []
    for idx, dt in enumerate(calendar):
        if dt not in split_dates or idx < WINDOW:
            continue
        window = [features_by_date[calendar[idx - WINDOW + j]] for j in range(WINDOW)]
        prompt = format_prompt(window)
        label = features_by_date[dt].label.value
        samples.append({"prompt": prompt, "completion": f' "{label}"}}'})
    return samples


def write_jsonl(samples: list[dict[str, str]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        for sample in samples:
            f.write(json.dumps(sample) + "\n")


if __name__ == "__main__":
    output_df = pd.read_csv(OUTPUT_CSV)
    features_by_date = build_day_features(output_df)
    fill_rest_days(features_by_date)

    for split in [Split.TRAIN, Split.VAL]:
        split_df = pd.read_csv(PROCESSED_DIR / f"{split.value}.csv")
        samples = build_samples(features_by_date, set(split_df["date"]))
        write_jsonl(samples, PROCESSED_DIR / f"{split.value}.jsonl")
        print(f"{split.value.capitalize()} samples: {len(samples)}")