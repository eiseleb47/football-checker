.PHONY: run test setup install

run: .venv
	.venv/bin/python app.py

test: .venv
	.venv/bin/pip install -q pytest pytest-cov
	.venv/bin/pytest tests/

setup install: .venv

.venv: requirements.txt
	python3 -m venv .venv
	.venv/bin/pip install -q -r requirements.txt
	@touch .venv
