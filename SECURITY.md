# Security Policy

## Reporting a Vulnerability

If you discover a security or privacy issue in this project, please report it responsibly:

1. **Do NOT open a public issue.**
2. Use [GitHub's private vulnerability reporting](https://docs.github.com/en/code-security/security-advisories/guidance-on-reporting-and-writing-information-about-vulnerabilities/privately-reporting-a-security-vulnerability), or email the maintainer.
3. Include a description, steps to reproduce, and potential impact.

This is a personal research project - there is no formal SLA, but reports are reviewed on a best-effort basis.

## Scope

In scope:

- Leakage of **personal health data** - `.fit` files contain GPS tracks, heart rate, and timestamps that can identify a person and their home/routes.
- Code paths that would write raw `.fit` contents or precise location into committed artefacts (`data/processed/output.csv`, logs, model prompts/datasets).
- Dependency vulnerabilities (`fitparse`, `pandas`, `trl`, `peft`, …).
- Code injection via crafted `.fit` files during parsing.

Out of scope:

- Vulnerabilities in upstream tooling (`fitparse`, `llama.cpp`, `trl`, …) - report those upstream.
- The trained model's recommendations themselves (this is a learning project, **not medical advice**).

## Handling personal data

- **Never commit `.fit` files or `data/`** - they hold GPS and heart-rate data. Keep them gitignored.
- Before sharing `output.csv`, a dataset, or model prompts, confirm they contain no precise coordinates or identifying timestamps.
- Treat any GGUF model or fine-tuning dataset derived from personal sessions as private - it encodes individual training patterns.
