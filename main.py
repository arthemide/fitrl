import csv
from enum import Enum

import fitparse

import datetime

from pathlib import Path
from pydantic import BaseModel, Field

FC_MAX = 187
z1_threshold = FC_MAX * 0.70
z2_threshold = FC_MAX * 0.80
z3_threshold = FC_MAX * 0.87
z4_threshold = FC_MAX * 0.93

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
    time_in_zone_1_2: float = Field(0, description="The total time spent in heart rate zones 1 and 2")
    reward: float = Field(0, description="The reward for the session")

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

def parse_zones(fitfile: fitparse.FitFile, session: Session) -> None:
    zone_durations = {1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0, 5: 0.0}

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
            zone_durations[1] += interval
        elif hr < z2_threshold:
            zone_durations[2] += interval
        elif hr < z3_threshold:
            zone_durations[3] += interval
        elif hr < z4_threshold:
            zone_durations[4] += interval
        else:
            zone_durations[5] += interval

    total_hr_duration = sum(zone_durations.values())
    if total_hr_duration == 0:
        return None

    for zone, duration in zone_durations.items():
        setattr(session, f"pct_z{zone}", float(f"{duration / total_hr_duration * 100:.2f}"))

def write_csv(sessions: list[Session], file_name: str) -> None:
    csv.DictWriter(open(file_name, "w"), fieldnames=Session.model_fields.keys()).writeheader()
    for session in sessions:
        csv.DictWriter(open(file_name, "a"), fieldnames=session.model_dump().keys()).writerow(session.model_dump())

if __name__ == "__main__":
    files = list(Path("files").glob("*.fit"))
    file_name = "output.csv"
    sessions = []
    for file_path in files:
        file = fitparse.FitFile(str(file_path))
        session = parse_session(file)
        parse_zones(file, session)

        threshold = 90.0
        if session.sport == "training" and (session.pct_z1 == 0 or session.pct_z2 == 0):
            label = Labels.EASY.value
        else:
            label = Labels.EASY.value if session.pct_z1 + session.pct_z2 > threshold else Labels.HARD.value
        session.label = label
        session.time_in_zone_1_2 = session.pct_z1 + session.pct_z2

        reward = round(session.speed / session.avg_heart_rate if session.avg_heart_rate > 0 else 0, 2)
        session.reward = reward

        # print(session.model_dump_json(indent=4))
        sessions.append(session)

    sessions.sort(key=lambda s: s.start_time)
    write_csv(sessions, file_name)
