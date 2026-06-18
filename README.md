# fitrl

[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/)

An end-to-end **RL pipeline on an LLM** that recommends the next day's recovery decision - **rest / easy / hard** - from the last N running sessions.

The model learns personal recovery patterns that a generic LLM cannot know: it reads a sliding window of past sessions (pace, HR, zones, duration, elevation) and predicts the decision whose delayed outcome - better pace at equal HR on the following easy run - was historically best.

See [CONTEXT.md](CONTEXT.md) for the full rationale and roadmap.

---

## Install

Requires **Python 3.12+** and [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/arthemide/fitrl.git
cd fitrl
make setup                  # uv sync --frozen
```

Place your `.fit` files under `data/` (gitignored).

---

## Quick start

```bash
make parse                  # parse .fit files → data/processed/output.csv
make annotate               # interactive annotation / validation of a subset
```

Each `.fit` file becomes one row in `output.csv` (one session). Decision classes:

- **rest** - no session that day (day absent from the CSV)
- **easy** - `pct_z1 + pct_z2 > 90%`
- **hard** - everything else
- **training** - strength training; merged with `easy` if no valid HR, else same zone rule

The full CSV schema (columns, zone weighting, reward definition) lives in [CLAUDE.md](CLAUDE.md).

---

## Stack

| Stage | Tooling |
|---|---|
| `.fit` parsing | `fitparse`, `pandas` |
| Typed session model | `pydantic` |
| SFT + RL (GRPO) | `trl`, `peft` |
| Quantization | `llama.cpp` (GGUF) |
| Deployment | CPU - Mac ARM, Raspberry Pi |

---

## Documentation

| File | Audience |
|---|---|
| [CLAUDE.md](CLAUDE.md) | technical reference - domain rules, CSV schema, conventions |
| [CONTEXT.md](CONTEXT.md) | project rationale, RL framing, pipeline roadmap |
| [CONTRIBUTING.md](CONTRIBUTING.md) | dev setup and workflow |
| [SECURITY.md](SECURITY.md) | vulnerability reporting and data handling |

---

## License

Apache 2.0 - see [LICENSE](LICENSE).
