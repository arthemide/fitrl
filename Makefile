.SILENT:
.DEFAULT_GOAL: help

help:
	echo "Please use \`make \033[36m<target>\033[0m\`"
	echo "\t where \033[36m<target>\033[0m is one of"
	grep -E '^\.PHONY: [a-zA-Z_-]+ .*?## .*$$' $(MAKEFILE_LIST) \
		| sort | awk 'BEGIN {FS = "(: |##)"}; {printf "• \033[36m%-30s\033[0m %s\n", $$2, $$3}'

.PHONY: lint ## 🕵 run lint
lint: setup-dev
	uv run ruff check . --fix
	uv run ruff format .
	make check

.PHONY: check ## 🕵 run check
check: setup-dev
	uv run ruff check .
	uv run ty check

.PHONY: setup ## 🔧 setup
setup:
	uv sync --frozen

.PHONY: setup-dev ## 🔧 setup-dev
setup-dev:
	uv sync --frozen --group dev

.PHONY: parse ## 🏃 Parse .fit files → data/processed/output.csv
parse:
	uv run python -m pipeline.parse

.PHONY: annotate ## ✍️  Interactive session annotation
annotate:
	uv run python -m pipeline.annotate

.PHONY: split ## 🪓 Split data before training
split:
	uv run python -m pipeline.split
