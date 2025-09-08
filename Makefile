.RECIPEPREFIX := >
.PHONY: install-minimal install-audio install-vision install-full verify-deps test test-deterministic train-deterministic bench

SEED ?= 0

install-minimal:
>pip install -e .

install-audio:
>pip install -e .[audio]

install-vision:
>pip install -e .[vision]

install-full:
>pip install -e .[audio,vision,llm,ml,web,network]

verify-deps:
>pip check
>pipdeptree --warn fail

test:
>pytest --maxfail=1 --strict-markers --cov=./

test-deterministic:
>PYTEST_SEED=$(SEED) SEED=$(SEED) pytest --maxfail=1 --strict-markers --cov=./

train-deterministic:
>SEED=$(SEED) python auto_retrain.py --dry-run

bench:
>python benchmarks/run_benchmarks.py

bench-query-memory:
>python benchmarks/query_memory_bench.py

