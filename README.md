# Bundesliga Live — 1. & 2. Bundesliga Scores and Standings

<p align="center">
  <a href="https://github.com/eiseleb47/football-checker/actions/workflows/tests.yml"><img src="https://img.shields.io/github/actions/workflow/status/eiseleb47/football-checker/tests.yml?branch=main&label=tests&style=for-the-badge&labelColor=1e1e2e&color=a6e3a1&logo=github&logoColor=cdd6f4" alt="Tests"></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/python-3.11%2B-89b4fa?style=for-the-badge&labelColor=1e1e2e&logo=python&logoColor=cdd6f4" alt="Python 3.11+"></a>
  <a href="https://github.com/eiseleb47/football-checker/commits/main"><img src="https://img.shields.io/github/last-commit/eiseleb47/football-checker?style=for-the-badge&labelColor=1e1e2e&color=cba6f7&logo=git&logoColor=cdd6f4" alt="Last Commit"></a>
  <a href="https://github.com/eiseleb47/football-checker"><img src="https://img.shields.io/badge/platform-linux-fab387?style=for-the-badge&labelColor=1e1e2e&logo=linux&logoColor=cdd6f4" alt="Platform"></a>
</p>

**Bundesliga Live** is a Flask web app for following the 1. and 2. Bundesliga in real time. It proxies the free [OpenLigaDB](https://openligadb.de) API and presents match cards, league standings, a season goal chart, and team form — all refreshing automatically every 60 seconds.

Default view shows the current matchday. Any previous or upcoming matchday can be browsed via the navigation arrows.

## Features

- **Match cards** — live, finished, and scheduled matches for the current matchday with status badges and halftime scores
- **Goal details** — two-column goal log per match with scorer, minute, score at that point, and special badges (Elfmeter, Eigentor, Verlängerung)
- **Goal timeline** — visual dot-on-bar across the 90 minutes, coloured by team, shown on card expand
- **Match stats** — halftime and second-half score breakdown derived from each match's result set
- **Team form** — last 5 results as colour-coded dots (green / yellow / red) computed server-side from recent matchdays, cached for 5 minutes
- **League standings** — full 18-team table with position indicators for Champions League, Europa League, Conference League, relegation play-off, and direct relegation zones
- **Top scorers** — season goal chart with relative bar lengths for each league
- **Matchday navigation** — browse any matchday via arrows; home button returns to the current one
- **Auto-refresh** — all data updates every 60 seconds with a live countdown in the navbar

Both the **1. Bundesliga** and **2. Bundesliga** are available via separate tabs.

## Prerequisites

Python 3.11 or newer. All dependencies are pure-Python and install via pip.

## Installation

```bash
git clone https://github.com/eiseleb47/football-checker.git
cd football-checker
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

No API keys are required. Match data is fetched from [OpenLigaDB](https://openligadb.de).

## Usage

```bash
python app.py
```

Or use the included launcher, which creates and activates the virtual environment automatically:

```bash
./run.sh
```

Or via Make:

```bash
make run
```

Then open [http://localhost:5000](http://localhost:5000) in your browser.

## Running the Tests

```bash
pip install pytest pytest-cov
pytest tests/
```

The test suite has 19 tests and runs fully offline (all OpenLigaDB calls are mocked).

| File | Tests | What is covered |
|------|-------|-----------------|
| `test_app.py` | 19 | Routes (index, currentgroup, matches, table, scorers), form W/D/L logic across matchdays, last-5 cap, unfinished-match exclusion, route-level cache hit, `api_get` caching, TTL expiry, and request-exception handling |

CI runs on Python 3.11 and 3.12 via GitHub Actions on every push and pull request.

## Repository Layout

```
football_checker/
├── app.py                        # Flask backend and OpenLigaDB proxy with TTL cache
├── templates/
│   └── index.html                # Single-page frontend (Bootstrap 5.3 dark theme, vanilla JS)
├── tests/
│   ├── conftest.py               # Flask test client and cache-clearing fixtures
│   └── test_app.py               # 19 tests: routes, form logic, caching, error handling
├── .github/
│   └── workflows/tests.yml       # CI: pytest + coverage on Python 3.11 + 3.12
├── pyproject.toml                # pytest and coverage configuration
├── requirements.txt              # Runtime dependencies
├── run.sh                        # Quick-start launcher (creates venv on first run)
├── Makefile                      # Convenience targets: make run, make setup
└── README.md
```

## Data Source

| Source | What it provides |
|--------|-----------------|
| [OpenLigaDB](https://openligadb.de) | Match results, goals (minute / scorer / type), halftime and final scores, league tables, season goal scorers — updated after each match, no API key required |
