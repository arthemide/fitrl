import csv
from enum import Enum
from rich.progress import track

import fitparse

import datetime

from pathlib import Path
from pydantic import BaseModel, Field

FC_MAX = 187
z1_threshold = FC_MAX * 0.70
z2_threshold = FC_MAX * 0.80
z3_threshold = FC_MAX * 0.87
z4_threshold = FC_MAX * 0.93
EASY_THRESHOLD = 90

RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")


class Labels(Enum):
    REST = "rest"
    EASY = "easy"
    HARD = "hard"
    TRAINING = "training"


class Session(BaseModel):
    sport: str = Field(..., description="The type of sport or activity")
    start_time: datetime.datetime = Field(..., description="The start time of the session")
    duration: float = Field(0, description="The total duration of the session in seconds")
    cadence: int = Field(0, description="The cadence during the session")
    distance: float = Field(0, description="The total distance covered during the session")
    avg_heart_rate: int = Field(0, description="The average heart rate during the session")
    max_heart_rate: int = Field(0, description="The maximum heart rate during the session")
    speed: float = Field(0, description="The average speed during the session")
    total_ascent: float = Field(0, description="The total ascent during the session")
    total_descent: float = Field(0, description="The total descent during the session")
    training_stress_score: float = Field(0, description="The training stress score for the session")
    pct_z1: float = Field(0, description="Percentage of time spent in heart rate zone 1")
    pct_z2: float = Field(0, description="Percentage of time spent in heart rate zone 2")
    pct_z3: float = Field(0, description="Percentage of time spent in heart rate zone 3")
    pct_z4: float = Field(0, description="Percentage of time spent in heart rate zone 4")
    pct_z5: float = Field(0, description="Percentage of time spent in heart rate zone 5")
    label: str = Field("", description="The label for the session")
    reward: float | None = Field(None, description="The reward for the session")


class Zones(BaseModel):
    z1: float = Field(0, description="Duration in seconds spent in heart rate zone 1")
    z2: float = Field(0, description="Duration in seconds spent in heart rate zone 2")
    z3: float = Field(0, description="Duration in seconds spent in heart rate zone 3")
    z4: float = Field(0, description="Duration in seconds spent in heart rate zone 4")
    z5: float = Field(0, description="Duration in seconds spent in heart rate zone 5")


def parse_session(fitfile: fitparse.FitFile) -> Session:
    session_data = {}
    for session in fitfile.get_messages("session"):
        for data in session:
            if data.name == "sport":
                session_data["sport"] = data.value
            elif data.name == "start_time":
                session_data["start_time"] = data.value
            elif data.name == "total_timer_time":
                session_data["duration"] = data.value
            elif data.name == "total_distance":
                session_data["distance"] = data.value
            elif data.name == "avg_heart_rate":
                session_data["avg_heart_rate"] = data.value
            elif data.name == "max_heart_rate":
                session_data["max_heart_rate"] = data.value
            elif data.name == "avg_speed":
                session_data["speed"] = data.value
            elif data.name == "total_ascent":
                session_data["total_ascent"] = data.value
            elif data.name == "total_descent":
                session_data["total_descent"] = data.value
            elif data.name == "avg_running_cadence":
                session_data["cadence"] = data.value
            elif data.name == "training_stress_score":
                session_data["training_stress_score"] = data.value
    return Session(**session_data)


def parse_zones(fitfile: fitparse.FitFile) -> tuple[Zones | None, float]:
    zone_durations = Zones()
    records = []
    for record in fitfile.get_messages("record"):
        ts, hr = None, None
        for data in record:
            if data.name == "timestamp":
                ts = data.value
            elif data.name == "heart_rate":
                hr = data.value
        if ts is not None and hr is not None:
            records.append((ts, hr))

    for i, (ts, hr) in enumerate(records):
        interval = (records[i + 1][0] - ts).total_seconds() if i < len(records) - 1 else 1.0
        if hr < z1_threshold:
            zone_durations.z1 += interval
        elif hr < z2_threshold:
            zone_durations.z2 += interval
        elif hr < z3_threshold:
            zone_durations.z3 += interval
        elif hr < z4_threshold:
            zone_durations.z4 += interval
        else:
            zone_durations.z5 += interval

    total_hr_duration = sum(zone_durations.model_dump().values())
    return (None, total_hr_duration) if total_hr_duration == 0 else (zone_durations, total_hr_duration)


def calculate_rewards(next_easy: Session, previous_easy: list[Session]) -> float | None:
    if not previous_easy or next_easy.avg_heart_rate == 0:
        return None
    ratios = [s.speed / s.avg_heart_rate for s in previous_easy if s.avg_heart_rate > 0]
    if not ratios:
        return None
    baseline = sum(ratios) / len(ratios)
    return round(next_easy.speed / next_easy.avg_heart_rate - baseline, 4)


def write_csv(sessions: list[Session], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=Session.model_fields.keys())
        writer.writeheader()
        for session in sessions:
            writer.writerow(session.model_dump())


if __name__ == "__main__":
    files: list[Path] = list(RAW_DIR.glob("*.fit"))
    output_path = PROCESSED_DIR / "output.csv"
    sessions: list[Session] = []

    for file_path in track(files, description="Processing FIT files"):
        file = fitparse.FitFile(str(file_path))
        session = parse_session(file)
        zone_durations, total_hr_duration = parse_zones(file)
        if zone_durations is not None:
            for zone, duration in zone_durations.model_dump().items():
                setattr(session, f"pct_{zone}", float(f"{duration / total_hr_duration * 100:.2f}"))

        if session.sport == "training" and total_hr_duration == 0:
            label = Labels.EASY.value
        else:
            label = Labels.EASY.value if session.pct_z1 + session.pct_z2 > EASY_THRESHOLD else Labels.HARD.value
        session.label = label
        sessions.append(session)

    sessions.sort(key=lambda s: s.start_time)

    for i, session in enumerate(sessions):
        next_easy = next(
            (s for s in sessions[i + 1:i + 5] if s.sport == "running" and s.label == Labels.EASY.value),
            None,
        )
        if next_easy is None:
            continue
        previous_easy = [s for s in sessions[:i] if s.sport == "running" and s.label == Labels.EASY.value][-5:]
        session.reward = calculate_rewards(next_easy, previous_easy)

    write_csv(sessions, output_path)
