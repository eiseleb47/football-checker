.PHONY: run setup install

run: .venv
	.venv/bin/python app.py

setup install: .venv

.venv: requirements.txt
	python3 -m venv .venv
	.venv/bin/pip install -q -r requirements.txt
	@touch .venv
