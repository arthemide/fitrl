# fitrl

RL pipeline on an LLM to recommend the next day's recovery decision (rest / easy / hard) from the last N running sessions.

## Domain

- **HR_MAX**: 187 bpm
- **Heart rate zones**: Z1 < 70% | Z2 70–80% | Z3 80–87% | Z4 87–93% | Z5 > 93%
- **Decision classes**:
  - `rest`: no session that day (day absent from the CSV)
  - `easy`: `pct_z1 + pct_z2 > 90%`
  - `hard`: everything else
  - `training`: strength training - merge with `easy` if no valid HR, otherwise apply the same zone rule
- **Reward**: delayed - `efficiency(next easy run) - mean(efficiency of last 5 easy runs)` where efficiency = `speed / avg_hr`. Window capped at 4 sessions; beyond that, reward is `None`.

## CSV structure (`output.csv`)

One row per `.fit` file (one session).

| Column | Description |
|---|---|
| `sport` | Activity type (running / cycling / training) |
| `start_time` | Session start datetime |
| `duration` | Active duration in seconds (`total_timer_time`) |
| `distance` | Total distance in meters |
| `speed` | Average speed in m/s (`avg_speed` from session message) |
| `avg_heart_rate` | Average HR |
| `max_heart_rate` | Max HR |
| `cadence` | Average cadence (`avg_running_cadence`, 0 for non-running) |
| `total_ascent` | Elevation gain in meters |
| `total_descent` | Elevation loss in meters |
| `training_stress_score` | Garmin TSS |
| `pct_z1` … `pct_z5` | % of time with valid HR spent in each zone |
| `label` | Decision class (easy / hard / training) |
| `reward` | Delayed aerobic efficiency delta (float or None) |

**Notes**:
- `pct_zX`: denominator = seconds with valid HR (not `duration`), intervals weighted by timestamp delta
- `training` sessions: `distance`, `speed`, `cadence` may be 0
- One session per `.fit` file (multisport not supported)

## Stack

- `fitparse` - .fit file parsing
- `pydantic` - typed `Session` model
- `trl` + `peft` - SFT and RL (GRPO)
- `llama.cpp` - GGUF quantization
- CPU deployment (Mac ARM, Raspberry Pi)

## Conventions

- One function per responsibility (`parse_session`, `parse_zones`)
- No `print` in business logic functions
- Zone thresholds derived from `HR_MAX`, never hardcoded
