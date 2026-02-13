PYTHON ?= python3

.PHONY: setup plan run run-dev eval test lint clean

setup:
	$(PYTHON) -m pip install -e .[dev]

plan:
	PYTHONPATH=src $(PYTHON) -m regdelta.cli plan --config configs/base.json

run:
	PYTHONPATH=src $(PYTHON) -m regdelta.cli run --config configs/base.json

run-dev:
	PYTHONPATH=src $(PYTHON) -m regdelta.cli run --config configs/base.json --profile dev_cpu

eval:
	@echo "Evaluation harness scaffolded. Implement in eval/ and src/regdelta/stages/verification.py"

test:
	PYTHONPATH=src $(PYTHON) -m unittest discover -s tests -p "test_*.py"

lint:
	@echo "Add ruff/black/mypy in next iteration"

clean:
	rm -rf .pytest_cache __pycache__
