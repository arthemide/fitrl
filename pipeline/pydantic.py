import datetime
from enum import Enum

from pydantic import BaseModel, Field


class Labels(Enum):
    REST = "rest"
    EASY = "easy"
    HARD = "hard"
    TRAINING = "training"


class Session(BaseModel):
    sport: str = Field(..., description="The type of sport or activity")
    start_time: datetime.datetime = Field(
        ..., description="The start time of the session"
    )
    duration: float = Field(
        0, description="The total duration of the session in seconds"
    )
    cadence: int = Field(0, description="The cadence during the session")
    distance: float = Field(
        0, description="The total distance covered during the session"
    )
    avg_heart_rate: int = Field(
        0, description="The average heart rate during the session"
    )
    max_heart_rate: int = Field(
        0, description="The maximum heart rate during the session"
    )
    speed: float = Field(0, description="The average speed during the session")
    total_ascent: float = Field(0, description="The total ascent during the session")
    total_descent: float = Field(0, description="The total descent during the session")
    training_stress_score: float = Field(
        0, description="The training stress score for the session"
    )
    pct_z1: float = Field(
        0, description="Percentage of time spent in heart rate zone 1"
    )
    pct_z2: float = Field(
        0, description="Percentage of time spent in heart rate zone 2"
    )
    pct_z3: float = Field(
        0, description="Percentage of time spent in heart rate zone 3"
    )
    pct_z4: float = Field(
        0, description="Percentage of time spent in heart rate zone 4"
    )
    pct_z5: float = Field(
        0, description="Percentage of time spent in heart rate zone 5"
    )
    label: str = Field("", description="The label for the session")
    reward: float | None = Field(None, description="The reward for the session")


class ZonesDurations(BaseModel):
    z1: float = Field(0, description="Duration in seconds spent in heart rate zone 1")
    z2: float = Field(0, description="Duration in seconds spent in heart rate zone 2")
    z3: float = Field(0, description="Duration in seconds spent in heart rate zone 3")
    z4: float = Field(0, description="Duration in seconds spent in heart rate zone 4")
    z5: float = Field(0, description="Duration in seconds spent in heart rate zone 5")


class Zones(Enum):
    Z1 = "Z1"
    Z2 = "Z2"
    Z3 = "Z3"
    Z4 = "Z4"
    Z5 = "Z5"


class Split(str, Enum):
    TRAIN = "train"
    VAL = "val"
    TEST = "test"
    EMBARGO = "embargo"


class SessionDate(BaseModel):
    """The only two session fields the split needs."""

    date: datetime.date
    label: Labels


class DailyDecision(BaseModel):
    """One calendar day = one decision sample (the axis we train on)."""

    date: datetime.date
    label: Labels
    split: Split | None = None
