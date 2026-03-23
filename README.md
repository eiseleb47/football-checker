# Bundesliga Live

A Flask web app for tracking live scores, standings, and match statistics for the 1. and 2. Bundesliga.

## Features

- **Live / finished / scheduled match cards** with real-time status badges
- **Goal details** — two-column log with scorer, minute, score at that point, and special badges (Elfmeter, Eigentor, Verlängerung)
- **Goal timeline** — visual dot-on-bar across the 90 minutes, coloured by team
- **Match stats** — halftime / second-half score breakdown per match
- **Team form** — last 5 results as colour-coded dots next to each team name
- **League standings** — full 18-team table with Champions League / Europa League / relegation zone colour coding
- **Top scorers** — season goal chart for each league
- **Matchday navigation** — browse any matchday; home button returns to the current one
- **Auto-refresh** — data updates every 60 seconds with a live countdown

Both the **1. Bundesliga** and **2. Bundesliga** are covered via separate tabs.

## Quick Start

```bash
./run.sh        # creates a venv on first run, installs deps, then starts the server
```

or

```bash
make run
```

Then open **http://localhost:5000** in your browser.

## Manual Setup

```bash
python3 -m venv .venv
source .venv/bin/activate        # on Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

## Development

Install dev dependencies (pytest + flake8) into the existing venv:

```bash
.venv/bin/pip install -r requirements-dev.txt
```

Run the test suite:

```bash
.venv/bin/pytest -v
```

Run the linter:

```bash
.venv/bin/flake8 app.py --max-line-length=120
```

## Data Source

Powered by [OpenLigaDB](https://openligadb.de) — a free, community-maintained German football API that requires no API key or account.

Available data per match: goals (minute, scorer, type), half-time and final scores, stadium, attendance. Detailed statistics such as shots, possession, or cards are not available through this API.

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11+ / Flask |
| Data | OpenLigaDB REST API |
| Frontend | Bootstrap 5.3 (dark theme), vanilla JS |
| Icons | Bootstrap Icons |

## Project Structure

```
football_checker/
├── app.py                  # Flask backend + OpenLigaDB proxy
├── templates/
│   └── index.html          # Single-page frontend
├── tests/
│   ├── conftest.py         # Shared pytest fixtures
│   └── test_app.py         # Route and logic tests
├── requirements.txt        # Runtime dependencies
├── requirements-dev.txt    # Dev/test dependencies
├── run.sh                  # Quick-start script
└── Makefile                # Convenience targets
```

## License

MIT
