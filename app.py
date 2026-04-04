from flask import Flask, render_template, jsonify
import os
import requests
import logging
import time
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["100 per hour"],
    storage_uri="memory://",
)

BASE_URL = "https://api.openligadb.de"
CURRENT_SEASON = "2025"  # 2025/26 season

# Simple TTL cache: {key: (timestamp, data)}
_cache: dict = {}
CACHE_TTL = 300  # 5 minutes


def api_get(path, ttl=60):
    now = time.time()
    if path in _cache:
        ts, data = _cache[path]
        if now - ts < ttl:
            return data
    try:
        r = requests.get(f"{BASE_URL}{path}", timeout=10)
        r.raise_for_status()
        data = r.json()
    except requests.exceptions.RequestException as e:
        logging.error("API error for %s: %s", path, e)
        return {"error": str(e)}
    _cache[path] = (now, data)
    return data


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/currentgroup/<league>")
def current_group(league):
    return jsonify(api_get(f"/getcurrentgroup/{league}"))


@app.route("/api/matches/<league>/<int:matchday>")
def matches_by_day(league, matchday):
    return jsonify(api_get(f"/getmatchdata/{league}/{CURRENT_SEASON}/{matchday}"))


@app.route("/api/table/<league>")
def table(league):
    return jsonify(api_get(f"/getbltable/{league}/{CURRENT_SEASON}", ttl=CACHE_TTL))


@app.route("/api/table/<league>/prev")
def table_prev(league):
    """Return standings before the current matchday's finished games."""
    current_table = api_get(f"/getbltable/{league}/{CURRENT_SEASON}", ttl=CACHE_TTL)
    if not isinstance(current_table, list):
        return jsonify(current_table)

    group = api_get(f"/getcurrentgroup/{league}")
    if not isinstance(group, dict) or "groupOrderID" not in group:
        return jsonify(current_table)

    current_md = group["groupOrderID"]
    matches = api_get(f"/getmatchdata/{league}/{CURRENT_SEASON}/{current_md}")
    if not isinstance(matches, list):
        return jsonify(current_table)

    finished = [m for m in matches if m.get("matchIsFinished")]
    if not finished:
        return jsonify(current_table)

    teams = {t["teamName"]: dict(t) for t in current_table}

    for match in finished:
        final = next((r for r in match.get("matchResults", []) if r["resultTypeID"] == 2), None)
        if not final:
            continue
        t1 = teams.get(match["team1"]["teamName"])
        t2 = teams.get(match["team2"]["teamName"])
        s1, s2 = final["pointsTeam1"], final["pointsTeam2"]

        for team, goals_for, goals_against in [(t1, s1, s2), (t2, s2, s1)]:
            if team:
                team["matches"] -= 1
                team["goals"] -= goals_for
                team["opponentGoals"] -= goals_against
                team["goalDiff"] = team["goals"] - team["opponentGoals"]

        if s1 > s2:
            if t1: t1["points"] -= 3; t1["won"] -= 1
            if t2: t2["lost"] -= 1
        elif s1 < s2:
            if t2: t2["points"] -= 3; t2["won"] -= 1
            if t1: t1["lost"] -= 1
        else:
            if t1: t1["points"] -= 1; t1["draw"] -= 1
            if t2: t2["points"] -= 1; t2["draw"] -= 1

    prev_table = sorted(teams.values(), key=lambda t: (-t["points"], -t["goalDiff"], -t["goals"]))
    return jsonify(prev_table)


@app.route("/api/scorers/<league>")
def scorers(league):
    return jsonify(api_get(f"/getgoalgetters/{league}/{CURRENT_SEASON}", ttl=CACHE_TTL))


@app.route("/api/form/<league>")
def team_form(league):
    """Compute last-5 form (W/D/L) for every team in the league."""
    cache_key = f"form_{league}"
    now = time.time()
    if cache_key in _cache:
        ts, data = _cache[cache_key]
        if now - ts < CACHE_TTL:
            return jsonify(data)

    group = api_get(f"/getcurrentgroup/{league}")
    if "error" in group:
        return jsonify({})

    current_md = group.get("groupOrderID", 1)
    form: dict = {}  # {str(teamId): [oldest→newest]}

    start_md = max(1, current_md - 5)
    for md in range(start_md, current_md + 1):
        matches = api_get(f"/getmatchdata/{league}/{CURRENT_SEASON}/{md}", ttl=CACHE_TTL)
        if not isinstance(matches, list):
            continue
        for match in matches:
            if not match.get("matchIsFinished"):
                continue
            final = next((r for r in match.get("matchResults", []) if r["resultTypeID"] == 2), None)
            if not final:
                continue
            t1 = str(match["team1"]["teamId"])
            t2 = str(match["team2"]["teamId"])
            s1, s2 = final["pointsTeam1"], final["pointsTeam2"]
            form.setdefault(t1, [])
            form.setdefault(t2, [])
            if s1 > s2:
                form[t1].append("W")
                form[t2].append("L")
            elif s1 < s2:
                form[t1].append("L")
                form[t2].append("W")
            else:
                form[t1].append("D")
                form[t2].append("D")

    result = {k: v[-5:] for k, v in form.items()}
    _cache[cache_key] = (now, result)
    return jsonify(result)


if __name__ == "__main__":
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    host = os.getenv("FLASK_HOST", "127.0.0.1")
    port = int(os.getenv("PORT", 5000))
    app.run(debug=debug, host=host, port=port)
