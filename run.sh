#!/usr/bin/env bash
# Football Checker – quick start script
set -e
cd "$(dirname "$0")"

if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
    echo "Installing dependencies..."
    .venv/bin/pip install -q -r requirements.txt
fi

echo "Starting at http://localhost:5000"
exec .venv/bin/python app.py
