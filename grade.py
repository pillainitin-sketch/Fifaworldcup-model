"""
Walk-forward grading -> fills the scorecard honestly and automatically.

For every played WC2026 match, in date order, predict it using ONLY the data
available before that match (ratings as of kickoff), record prediction vs actual,
THEN fold the result into the ratings and move to the next match. This is a real
walk-forward backtest: no peeking at a match's own result or any later result.
Output graded.json, which the dashboard scores into Brier / log loss / hit rate.

It uses the same model the dashboard shows (Elo blended with squad value, plus
the per-venue heat/altitude edge and host advantage). Availability is omitted
here because historical line-ups are not in the free data; it is a minor term.
"""
import json
import fetch_data as fd
import elo as E
import team_adaptation as TA

VEN = {v["stadium_real_name"]: v for v in json.load(open("wc2026_venues.json"))["venues"]}
bases = {t["team"]: t for t in json.load(open("team_climate_baseline.json"))["teams"]}


def base_pretournament():
    """Elo from all internationals BEFORE the World Cup, blended with squad value."""
    rows = fd.get_international_results()
    pre = sorted([r for r in rows if r["home_score"] not in ("", "NA", None)
                  and "2002-01-01" <= r["date"] < "2026-06-01"], key=lambda r: r["date"])
    R = {}
    for r in pre:
        try: hs, as_ = int(r["home_score"]), int(r["away_score"])
        except (TypeError, ValueError): continue
        h, a = r["home_team"], r["away_team"]
        Rh, Ra = R.get(h, E.START), R.get(a, E.START)
        neutral = str(r.get("neutral", "")).lower() in ("true", "1")
        adj = 0 if neutral else E.HOME_ADV
        Eh = 1 / (1 + 10 ** ((Ra - (Rh + adj)) / 400))
        Sh = 1.0 if hs > as_ else 0.0 if hs < as_ else 0.5
        d = E.K * E.gd_multiplier(abs(hs - as_)) * (Sh - Eh)
        R[h] = Rh + d; R[a] = Ra - d
    vals = E._load_values()
    return E.blend_value(R, vals) if vals else R


def grade():
    rows = fd.get_international_results()
    wc = sorted([r for r in rows if r.get("tournament") == "FIFA World Cup"
                 and r["date"] >= "2026-06-01" and r["home_score"] not in ("", "NA", None)],
                key=lambda r: r["date"])
    R = base_pretournament()
    out = []
    for r in wc:
        h, a = r["home_team"], r["away_team"]
        try: hs, as_ = int(r["home_score"]), int(r["away_score"])
        except (TypeError, ValueError): continue
        neutral = str(r.get("neutral", "")).lower() in ("true", "1")
        v = VEN.get(fd.CITY_TO_VENUE.get(r["city"]))
        eh, ea = R.get(h, E.START), R.get(a, E.START)
        if v and h in bases and a in bases:
            edge = TA.fixture_edge(bases[h], bases[a], v)
            eh += edge["heat_edge"] * 40 + edge["altitude_edge"] * 60
        p = E.win_prob({h: eh, a: ea}, h, a, neutral=neutral)   # PRE-match prediction
        outcome = "home" if hs > as_ else "away" if hs < as_ else "draw"
        out.append({"date": r["date"], "home": h, "away": a,
                    "p_home": p["P_a"], "p_draw": p["P_draw"], "p_away": p["P_b"],
                    "hs": hs, "as": as_, "outcome": outcome})
        # walk forward: fold the actual result into the ratings for later matches
        Rh, Ra = R.get(h, E.START), R.get(a, E.START)
        adj = 0 if neutral else E.HOME_ADV
        Eh = 1 / (1 + 10 ** ((Ra - (Rh + adj)) / 400))
        Sh = 1.0 if hs > as_ else 0.0 if hs < as_ else 0.5
        d = E.K * E.gd_multiplier(abs(hs - as_)) * (Sh - Eh)
        R[h] = Rh + d; R[a] = Ra - d
    return out


graded = grade()
# headline metrics (also recomputed client-side; handy for the log)
n = len(graded)
if n:
    brier = sum((g["p_home"]-(g["outcome"]=="home"))**2 + (g["p_draw"]-(g["outcome"]=="draw"))**2
                + (g["p_away"]-(g["outcome"]=="away"))**2 for g in graded) / n
    import math
    ll = sum(-math.log(max(g["p_"+g["outcome"]], 1e-6)) for g in graded) / n
    hits = sum(1 for g in graded if max(("home", g["p_home"]), ("draw", g["p_draw"]),
               ("away", g["p_away"]), key=lambda x: x[1])[0] == g["outcome"]) / n
    print(f"graded {n} match(es): Brier {brier:.3f}, log loss {ll:.3f}, hit rate {hits:.0%}")
else:
    print("no played matches to grade yet")

json.dump({"n": n, "graded": graded}, open("graded.json", "w"), indent=1)
print("wrote graded.json")
