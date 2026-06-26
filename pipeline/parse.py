import csv
from rich.progress import track

import fitparse


from pathlib import Path

from pipeline.config import PROCESSED_DIR, RAW_DIR
from pipeline.intervals import RUN_HR_ZONES
from pipeline.pydantic import Labels, Session, ZonesDurations

# Z5 is everything above the Z4 bound, so drop the Z5 max.
z1_threshold, z2_threshold, z3_threshold, z4_threshold = RUN_HR_ZONES[:-1]
EASY_THRESHOLD = 90


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


def parse_zones(fitfile: fitparse.FitFile) -> tuple[ZonesDurations | None, float]:
    zone_durations = ZonesDurations()
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
        interval = (
            (records[i + 1][0] - ts).total_seconds() if i < len(records) - 1 else 1.0
        )
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
    return (
        (None, total_hr_duration)
        if total_hr_duration == 0
        else (zone_durations, total_hr_duration)
    )


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
                setattr(
                    session,
                    f"pct_{zone}",
                    float(f"{duration / total_hr_duration * 100:.2f}"),
                )

        if session.sport == "training" and total_hr_duration == 0:
            label = Labels.EASY.value
        else:
            label = (
                Labels.EASY.value
                if session.pct_z1 + session.pct_z2 > EASY_THRESHOLD
                else Labels.HARD.value
            )
        session.label = label
        sessions.append(session)

    sessions.sort(key=lambda s: s.start_time)

    for i, session in enumerate(sessions):
        next_easy = next(
            (
                s
                for s in sessions[i + 1 : i + 5]
                if s.sport == "running" and s.label == Labels.EASY.value
            ),
            None,
        )
        if next_easy is None:
            continue
        previous_easy = [
            s
            for s in sessions[:i]
            if s.sport == "running" and s.label == Labels.EASY.value
        ][-5:]
        session.reward = calculate_rewards(next_easy, previous_easy)

    write_csv(sessions, output_path)
