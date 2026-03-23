"""Tests for the Bundesliga Live Flask app."""
import time
from unittest.mock import MagicMock, patch

import pytest

import app as app_module


# ── Fixtures / helpers ────────────────────────────────────────────────────────

def _mock_match(team1_id, team2_id, t1_goals, t2_goals, finished=True):
    """Return a minimal match dict resembling the OpenLigaDB schema."""
    return {
        "matchID": team1_id * 1000 + team2_id,
        "matchIsFinished": finished,
        "leagueShortcut": "bl1",
        "matchDateTime": "2026-03-20T15:30:00",
        "matchDateTimeUTC": "2026-03-20T14:30:00Z",
        "team1": {"teamId": team1_id, "teamName": f"Team {team1_id}", "shortName": f"T{team1_id}", "teamIconUrl": None},
        "team2": {"teamId": team2_id, "teamName": f"Team {team2_id}", "shortName": f"T{team2_id}", "teamIconUrl": None},
        "matchResults": [
            {"resultTypeID": 1, "pointsTeam1": max(0, t1_goals - 1), "pointsTeam2": max(0, t2_goals - 1)},
            {"resultTypeID": 2, "pointsTeam1": t1_goals, "pointsTeam2": t2_goals},
        ],
        "goals": [],
        "location": None,
        "numberOfViewers": None,
    }


def _mock_group(matchday=27):
    return {"groupOrderID": matchday, "groupName": f"{matchday}. Spieltag", "groupID": matchday}


# ── Route: index ──────────────────────────────────────────────────────────────

def test_index_returns_200(client):
    r = client.get("/")
    assert r.status_code == 200


def test_index_contains_app_title(client):
    r = client.get("/")
    assert b"Bundesliga" in r.data


# ── Route: /api/currentgroup ──────────────────────────────────────────────────

def test_current_group_proxies_data(client):
    with patch("app.api_get", return_value=_mock_group(27)):
        r = client.get("/api/currentgroup/bl1")
    assert r.status_code == 200
    assert r.get_json()["groupOrderID"] == 27


def test_current_group_forwards_error(client):
    with patch("app.api_get", return_value={"error": "timeout"}):
        r = client.get("/api/currentgroup/bl1")
    assert r.status_code == 200
    assert "error" in r.get_json()


# ── Route: /api/matches ───────────────────────────────────────────────────────

def test_matches_by_day_returns_list(client):
    matches = [_mock_match(40, 87, 2, 1)]
    with patch("app.api_get", return_value=matches):
        r = client.get("/api/matches/bl1/27")
    assert r.status_code == 200
    data = r.get_json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["matchID"] == 40_087


def test_matches_empty_matchday(client):
    with patch("app.api_get", return_value=[]):
        r = client.get("/api/matches/bl2/1")
    assert r.status_code == 200
    assert r.get_json() == []


# ── Route: /api/table ─────────────────────────────────────────────────────────

def test_table_returns_18_teams(client):
    mock_table = [
        {"teamName": f"Team {i}", "shortName": f"T{i}", "teamIconUrl": None,
         "points": 50 - i * 2, "matches": 27, "won": 15, "draw": 5, "lost": 7,
         "goals": 40, "opponentGoals": 25, "goalDiff": 15}
        for i in range(18)
    ]
    with patch("app.api_get", return_value=mock_table):
        r = client.get("/api/table/bl1")
    assert r.status_code == 200
    assert len(r.get_json()) == 18


# ── Route: /api/scorers ───────────────────────────────────────────────────────

def test_scorers_returns_list(client):
    mock = [{"goalGetterId": 1, "goalGetterName": "H. Kane", "goalCount": 31}]
    with patch("app.api_get", return_value=mock):
        r = client.get("/api/scorers/bl1")
    assert r.status_code == 200
    data = r.get_json()
    assert data[0]["goalGetterName"] == "H. Kane"
    assert data[0]["goalCount"] == 31


# ── Route: /api/form ─────────────────────────────────────────────────────────

def _form_api_mock(matchday_results):
    """
    Build a side_effect for api_get that returns a specific match
    for each matchday. matchday_results: {md: (t1_goals, t2_goals)}.
    """
    group = _mock_group(max(matchday_results.keys()))

    def _side_effect(path, ttl=60):
        if "getcurrentgroup" in path:
            return group
        for md, (g1, g2) in matchday_results.items():
            if path.endswith(f"/{md}"):
                return [_mock_match(1, 2, g1, g2)]
        return []

    return _side_effect


def test_form_win_recorded_correctly(client):
    with patch("app.api_get", side_effect=_form_api_mock({1: (3, 0)})):
        data = client.get("/api/form/bl1").get_json()
    assert data["1"] == ["W"]
    assert data["2"] == ["L"]


def test_form_loss_recorded_correctly(client):
    with patch("app.api_get", side_effect=_form_api_mock({1: (0, 2)})):
        data = client.get("/api/form/bl1").get_json()
    assert data["1"] == ["L"]
    assert data["2"] == ["W"]


def test_form_draw_recorded_correctly(client):
    with patch("app.api_get", side_effect=_form_api_mock({1: (1, 1)})):
        data = client.get("/api/form/bl1").get_json()
    assert data["1"] == ["D"]
    assert data["2"] == ["D"]


def test_form_sequence_across_matchdays(client):
    # MD1: draw, MD2: team1 wins, MD3: team2 wins
    side = _form_api_mock({1: (1, 1), 2: (2, 0), 3: (0, 1)})
    with patch("app.api_get", side_effect=side):
        data = client.get("/api/form/bl1").get_json()
    assert data["1"] == ["D", "W", "L"]
    assert data["2"] == ["D", "L", "W"]


def test_form_limited_to_last_five(client):
    # 6 matchdays — only last 5 should appear
    results = {md: (1, 0) for md in range(1, 7)}  # team1 always wins
    group = _mock_group(6)

    def _side(path, ttl=60):
        if "getcurrentgroup" in path:
            return group
        for md in range(1, 7):
            if path.endswith(f"/{md}"):
                return [_mock_match(1, 2, 1, 0)]
        return []

    with patch("app.api_get", side_effect=_side):
        data = client.get("/api/form/bl1").get_json()
    assert len(data["1"]) == 5
    assert data["1"] == ["W", "W", "W", "W", "W"]


def test_form_excludes_unfinished_matches(client):
    group = _mock_group(1)

    def _side(path, ttl=60):
        if "getcurrentgroup" in path:
            return group
        if path.endswith("/1"):
            m = _mock_match(1, 2, 2, 0)
            m["matchIsFinished"] = False
            m["matchResults"] = []
            return [m]
        return []

    with patch("app.api_get", side_effect=_side):
        data = client.get("/api/form/bl1").get_json()
    # Unfinished match must not appear in form
    assert data.get("1", []) == []
    assert data.get("2", []) == []


def test_form_cached_on_second_request(client):
    call_count = 0

    def _side(path, ttl=60):
        nonlocal call_count
        call_count += 1
        if "getcurrentgroup" in path:
            return _mock_group(1)
        return [_mock_match(1, 2, 1, 0)]

    with patch("app.api_get", side_effect=_side):
        client.get("/api/form/bl1")
        first_count = call_count
        client.get("/api/form/bl1")  # should hit the route-level cache
        assert call_count == first_count, "api_get was called again despite valid cache"


def test_form_returns_empty_on_api_error(client):
    with patch("app.api_get", return_value={"error": "timeout"}):
        r = client.get("/api/form/bl1")
    assert r.status_code == 200
    assert r.get_json() == {}


# ── api_get: caching and error handling ───────────────────────────────────────

def test_api_get_caches_result():
    mock_resp = MagicMock()
    mock_resp.raise_for_status = lambda: None
    mock_resp.json.return_value = {"cached": True}

    with patch("requests.get", return_value=mock_resp) as mock_get:
        app_module.api_get("/test-cache")
        app_module.api_get("/test-cache")
        assert mock_get.call_count == 1  # second call served from cache


def test_api_get_respects_ttl():
    mock_resp = MagicMock()
    mock_resp.raise_for_status = lambda: None
    mock_resp.json.return_value = {"v": 1}

    with patch("requests.get", return_value=mock_resp) as mock_get:
        app_module.api_get("/test-ttl", ttl=0)
        app_module.api_get("/test-ttl", ttl=0)
        assert mock_get.call_count == 2  # TTL=0 → always re-fetch


def test_api_get_returns_error_dict_on_request_exception():
    import requests as req_lib
    with patch("requests.get", side_effect=req_lib.exceptions.ConnectionError("network down")):
        result = app_module.api_get("/bad-path")
    assert "error" in result
    assert "network down" in result["error"]
