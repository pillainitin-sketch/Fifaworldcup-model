"""
Match-level data ingestion for WC2026 (API-Football, needs your key).

THE SPLIT, enforced here so it doesn't blur:

  MODEL INPUTS (availability only) -> these adjust the win probability:
    - get_lineups()  : is the first-choice XI on the pitch?
    - get_injuries()  : who is unavailable?
    - lineup_strength_delta() turns that into a per-match Elo nudge.

  DISPLAY / CONTENT (everything else) -> match-detail view + video fuel, NOT model:
    - get_events()       : goals, yellow/red cards, substitutions
    - get_player_stats() : tackles, passes, pass %, duels, shots, rating, minutes

Per-match player performance (tackles, passes, ratings) is deliberately kept out
of the model: on tournament-size samples it overfits and is endogenous to the
result. The result already carries the signal; these carry the story.

WC2026 = league 1, season 2026.  Free tier is 100 req/day; lineups/events/player
stats need a paid tier.
"""
import urllib.parse, urllib.request, json

HOST = "v3.football.api-sports.io"

def _af(path, api_key, **params):
    url = f"https://{HOST}/{path}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"x-apisports-key": api_key})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read()).get("response", [])

# ---------------------------------------------------------------------------
# MODEL INPUTS  (availability)
# ---------------------------------------------------------------------------
def get_lineups(api_key, fixture_id):
    """{team_name: {formation, startXI:[names], subs:[names], coach}}"""
    out = {}
    for side in _af("fixtures/lineups", api_key, fixture=fixture_id):
        out[side["team"]["name"]] = {
            "formation": side.get("formation"),
            "startXI": [p["player"]["name"] for p in side.get("startXI", [])],
            "subs": [p["player"]["name"] for p in side.get("substitutes", [])],
            "coach": (side.get("coach") or {}).get("name"),
        }
    return out

def get_injuries(api_key, fixture_id=None, league=1, season=2026):
    p = {"fixture": fixture_id} if fixture_id else {"league": league, "season": season}
    return [{"team": i["team"]["name"], "player": i["player"]["name"],
             "reason": i["player"].get("reason")} for i in _af("injuries", api_key, **p)]

def lineup_strength_delta(announced_xi, key_players, per_missing=18, cap=45):
    """MODEL INPUT. Penalise a team whose first-choice players are NOT starting.
    announced_xi: list of names actually starting.
    key_players : the team's first-choice/high-value names (from market value or
                  rating; pull once from API-Football players, sorted by rating).
    Returns a per-match Elo delta (<= 0)."""
    xi = set(announced_xi)
    missing = sum(1 for p in key_players if p not in xi)
    return -min(missing * per_missing, cap)

# ---------------------------------------------------------------------------
# DISPLAY / CONTENT  (never fed to the model)
# ---------------------------------------------------------------------------
def get_events(api_key, fixture_id):
    """Goals, cards, subs for the match-detail view and video captions."""
    out = []
    for e in _af("fixtures/events", api_key, fixture=fixture_id):
        out.append({
            "minute": e["time"]["elapsed"],
            "team": e["team"]["name"],
            "player": (e.get("player") or {}).get("name"),
            "type": e["type"],          # Goal | Card | subst
            "detail": e["detail"],       # Normal Goal | Yellow Card | Red Card | ...
            "assist": (e.get("assist") or {}).get("name"),
        })
    return out

def get_player_stats(api_key, fixture_id):
    """Per-player tackles, passes, rating, etc. For display and analysis ONLY."""
    out = {}
    for side in _af("fixtures/players", api_key, fixture=fixture_id):
        rows = []
        for p in side.get("players", []):
            s = (p.get("statistics") or [{}])[0]
            rows.append({
                "player": p["player"]["name"],
                "minutes": (s.get("games") or {}).get("minutes"),
                "rating": (s.get("games") or {}).get("rating"),
                "goals": (s.get("goals") or {}).get("total"),
                "shots": (s.get("shots") or {}).get("total"),
                "passes": (s.get("passes") or {}).get("total"),
                "pass_pct": (s.get("passes") or {}).get("accuracy"),
                "tackles": (s.get("tackles") or {}).get("total"),
                "duels_won": (s.get("duels") or {}).get("won"),
                "dribbles": (s.get("dribbles") or {}).get("success"),
            })
        out[side["team"]["name"]] = rows
    return out

def match_detail(api_key, fixture_id):
    """Bundle the DISPLAY data into one object for the dashboard panel / video.
    Note: deliberately excludes the player-stat firehose from the model path."""
    return {
        "fixture_id": fixture_id,
        "lineups": get_lineups(api_key, fixture_id),
        "events": get_events(api_key, fixture_id),
        "player_stats": get_player_stats(api_key, fixture_id),
    }

# ---------------------------------------------------------------------------
# How the model hook plugs in (in update.predict_fixture, alongside injuries):
#
#   xi = get_lineups(KEY, fid)[team]["startXI"]
#   eh += lineup_strength_delta(xi, KEY_PLAYERS[team])
#
# That is the ONLY place this module touches the probabilities. Everything in
# get_events / get_player_stats is for the match-detail view and your videos.
# ---------------------------------------------------------------------------
