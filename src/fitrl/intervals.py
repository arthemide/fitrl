"""Fetch HR zone boundaries from intervals.icu.

Auth is HTTP Basic with the literal username ``API_KEY`` and the personal API
key as password (intervals.icu Settings -> Developer).
"""

import base64
import json
import os
import urllib.request
from dotenv import load_dotenv
from urllib.error import HTTPError

BASE_URL = "https://intervals.icu/api/v1"
RUN_TYPES = {"Run", "VirtualRun", "TrailRun"}

# Z1..Z5 HR zone upper bounds (bpm), from intervals.icu Run settings.
# Single source of truth for the pipeline; refresh with `make zones`.
RUN_HR_ZONES = [146, 155, 169, 182, 200]

load_dotenv()
ATHLETE_ID = os.getenv("INTERVALS_ATHLETE_ID", "i19817")
API_KEY = os.getenv("INTERVALS_API_KEY")


def _auth_header(api_key: str) -> str:
    token = base64.b64encode(f"API_KEY:{api_key}".encode()).decode()
    return f"Basic {token}"


def fetch_athlete(athlete_id: str = ATHLETE_ID) -> dict:
    if not API_KEY:
        raise RuntimeError("INTERVALS_API_KEY env var is not set")
    request = urllib.request.Request(
        f"{BASE_URL}/athlete/{athlete_id}",
        headers={
            "Authorization": _auth_header(API_KEY),
            "Accept": "application/json",
            "User-Agent": "fitrl/0.1",
        },
    )
    try:
        with urllib.request.urlopen(request) as response:
            return json.load(response)
    except HTTPError as error:
        raise RuntimeError(
            f"intervals.icu returned HTTP {error.code}: {error.reason}"
        ) from error


def fetch_run_hr_zones(athlete_id: str = ATHLETE_ID) -> list[int]:
    """Return the running HR zone upper bounds in bpm (5 values, Z1..Z5)."""
    athlete = fetch_athlete(athlete_id)
    for settings in athlete.get("sportSettings", []):
        if RUN_TYPES.intersection(settings.get("types", [])):
            return settings["hr_zones"]
    raise RuntimeError("No Run sport settings found for this athlete")


if __name__ == "__main__":
    from rich import print

    zones = fetch_run_hr_zones()
    print(f"intervals.icu Run HR zones (bpm): {zones}")
    if zones != RUN_HR_ZONES:
        print(
            f"[yellow]RUN_HR_ZONES is {RUN_HR_ZONES}; update it in pipeline/intervals.py.[/yellow]"
        )
