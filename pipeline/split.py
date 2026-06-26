import datetime
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd

from pipeline.config import (
    EMBARGO_SESSIONS,
    OUTPUT_CSV,
    PROCESSED_DIR,
    TRAIN_FRAC,
    VAL_FRAC,
)
from pipeline.parse import Labels
from pipeline.pydantic import DailyDecision, SessionDate, Split


def load_sessions(csv: Path) -> list[SessionDate]:
    """Read output.csv into chronologically sorted (date, label) sessions."""
    df = pd.read_csv(csv).sort_values("start_time")
    return [
        SessionDate(date=pd.to_datetime(t).date(), label=label)
        for t, label in zip(df["start_time"], df["label"])
    ]


def collapse_day(labels: list[Labels]) -> Labels:
    """no session -> rest, any hard session -> hard, else easy."""
    if not labels:
        return Labels.REST
    if Labels.HARD in labels:
        return Labels.HARD
    return Labels.EASY


def build_daily_decisions(sessions: list[SessionDate]) -> list[DailyDecision]:
    """Collapse sessions per day and fill every empty calendar day as rest."""
    labels_by_day: dict[datetime.date, list[Labels]] = defaultdict(list)
    for session in sessions:
        labels_by_day[session.date].append(session.label)

    day = min(labels_by_day)
    last = max(labels_by_day)
    decisions: list[DailyDecision] = []
    while day <= last:
        decisions.append(
            DailyDecision(date=day, label=collapse_day(labels_by_day.get(day, [])))
        )
        day += datetime.timedelta(days=1)
    return decisions


def contaminated_dates(
    sessions: list[SessionDate], boundary: datetime.date
) -> set[datetime.date]:
    """Dates of the EMBARGO_SESSIONS sessions just before a split boundary."""
    before = [s.date for s in sessions if s.date < boundary]
    return set(before[-EMBARGO_SESSIONS:])


def assign_splits(decisions: list[DailyDecision], sessions: list[SessionDate]) -> None:
    """Tag each day train/val/test in place, dropping the embargo bands."""
    n = len(decisions)
    val_start = decisions[int(n * TRAIN_FRAC)].date
    test_start = decisions[int(n * (TRAIN_FRAC + VAL_FRAC))].date
    embargo = contaminated_dates(sessions, val_start) | contaminated_dates(
        sessions, test_start
    )

    for day in decisions:
        if day.date in embargo:
            day.split = Split.EMBARGO
        elif day.date < val_start:
            day.split = Split.TRAIN
        elif day.date < test_start:
            day.split = Split.VAL
        else:
            day.split = Split.TEST


def summarize(decisions: list[DailyDecision]) -> None:
    by_split: dict[Split, list[DailyDecision]] = defaultdict(list)
    for day in decisions:
        if day.split is not None:
            by_split[day.split].append(day)

    print(f"Total days: {len(decisions)}")
    for split in Split:
        group = by_split.get(split, [])
        dist = Counter(day.label.value for day in group)
        print(f"  {split.value:<8} {len(group):>4}  {dict(dist)}")

    train_max = max(day.date for day in by_split[Split.TRAIN])
    val_min = min(day.date for day in by_split[Split.VAL])
    assert train_max < val_min, "train/val overlap in time"


if __name__ == "__main__":
    sessions = load_sessions(OUTPUT_CSV)
    decisions = build_daily_decisions(sessions)
    assign_splits(decisions, sessions)
    summarize(decisions)

    frame = pd.DataFrame(day.model_dump(mode="json") for day in decisions)
    for split in (Split.TRAIN, Split.VAL, Split.TEST):
        subset = frame[frame["split"] == split.value].drop(columns="split")
        subset.to_csv(PROCESSED_DIR / f"{split.value}.csv", index=False)
