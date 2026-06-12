"""
Daily live update for the WC2026 model.

THE LOOP (run once each morning during the tournament):
  1. refresh results            -> yesterday's matches flow into the data
  2. re-rate Elo on all played  -> ratings move with what actually happened
  3. injury / lineup adjustment -> per-MATCH only, never the rating itself
  4. regenerate remaining odds   -> dashboard updates
  5. log pre-kickoff predictions -> immutable, for calibration + accountability

THE RULE YOU CANNOT BREAK:
  Update the DATA, never the METHOD. K-factor, climate weights, the blend are
  FROZEN before kickoff. Re-tuning them mid-tournament is overfitting to noise:
  you would be fitting the model to the very results you are trying to predict.
"""

import csv
import datetime
import json
import fetch_data as fd
import elo as E
import team_adaptation as TA

# ---- FROZEN before the tournament. Do not touch these during the event. ----
FROZEN = {"K": 32, "HOME_ADV": 65, "HEAT_MAX_ELO": 40, "ALT_MAX_ELO": 60,
          "INJURY_KEY_PLAYER_ELO": 18, "INJURY_CAP_ELO": 45}


def refresh_and_rate():
    """Re-pull results and rebuild Elo. Because build_elo consumes ALL played
    matches chronologically, tournament results already played are automatically
    included. The model is 'live' simply by re-running this each day."""
    rows = fd.get_international_results()
    return E.strength(), rows


def remaining_fixtures(rows):
    return fd.get_wc2026_fixtures(rows)   # unplayed only (empty scores)


def injury_adjustment(team, injury_list):
    """Per-MATCH Elo delta for a team given its OUT players for THIS game.
    Availability is real signal. A single bad performance is NOT - we never
    re-rate a player off one game. injury_list: [{'player':..,'key':bool}, ...]
    Pull live from API-Football injuries endpoint; pass [] when none."""
    keys = sum(1 for p in injury_list if p.get("key"))
    return -min(keys * FROZEN["INJURY_KEY_PLAYER_ELO"], FROZEN["INJURY_CAP_ELO"])


def predict_fixture(R, f, venues, bases, injuries=None):
    v = venues.get(fd.CITY_TO_VENUE.get(f["city"]))
    hb, ab = bases.get(f["home_team"]), bases.get(f["away_team"])
    if not (v and hb and ab):
        return None
    neutral = str(f.get("neutral", "")).lower() in ("true", "1")

    eh = R.get(f["home_team"], E.START)
    ea = R.get(f["away_team"], E.START)
    edge = TA.fixture_edge(hb, ab, v)
    eh += edge["heat_edge"] * FROZEN["HEAT_MAX_ELO"] + edge["altitude_edge"] * FROZEN["ALT_MAX_ELO"]

    inj = injuries or {}
    eh += injury_adjustment(f["home_team"], inj.get(f["home_team"], []))
    ea += injury_adjustment(f["away_team"], inj.get(f["away_team"], []))

    Rtmp = {f["home_team"]: eh, f["away_team"]: ea}
    p = E.win_prob(Rtmp, f["home_team"], f["away_team"], neutral=neutral)
    return {"date": f["date"], "home": f["home_team"], "away": f["away_team"],
            "city": f["city"], "p_home": p["P_a"], "p_draw": p["P_draw"],
            "p_away": p["P_b"]}


LOG = "predictions_log.csv"

def log_predictions(preds, run_ts):
    """Append-only. Once a prediction is logged before kickoff it is never
    edited. This file IS your calibration record and your public accountability."""
    new = not _exists(LOG)
    with open(LOG, "a", newline="") as fh:
        w = csv.writer(fh)
        if new:
            w.writerow(["run_ts", "date", "home", "away", "p_home", "p_draw", "p_away"])
        for p in preds:
            w.writerow([run_ts, p["date"], p["home"], p["away"],
                        p["p_home"], p["p_draw"], p["p_away"]])

def _exists(path):
    try:
        open(path).close(); return True
    except FileNotFoundError:
        return False


def run_daily_update(injuries=None):
    venues = {v["stadium_real_name"]: v for v in
              json.load(open("wc2026_venues.json"))["venues"]}
    bases = {t["team"]: t for t in
             json.load(open("team_climate_baseline.json"))["teams"]}
    R, rows = refresh_and_rate()
    fixtures = remaining_fixtures(rows)
    preds = [p for f in fixtures if (p := predict_fixture(R, f, venues, bases, injuries))]
    run_ts = datetime.datetime.now(datetime.UTC).isoformat(timespec="seconds")
    log_predictions(preds, run_ts)        # immutable record for calibration
    return R, preds


if __name__ == "__main__":
    R, preds = run_daily_update()
    print(f"remaining fixtures predicted & logged: {len(preds)}")

    # --- demonstrate the live loop: simulate an upset and re-rate ---
    print("\n=== LIVE UPDATE DEMO: simulate a result, watch ratings move ===")
    h, a = "Saudi Arabia", "Uruguay"
    before = E.win_prob(R, a, h)
    print(f"  before: Uruguay {R[a]:.0f} Elo, Saudi {R[h]:.0f} Elo "
          f"-> Uruguay {before['P_a']:.0%}")
    # pretend Saudi pull off a 2-0 shock
    Eh, Ea = R[h], R[a]
    exp_h = 1/(1+10**((Ea-Eh)/400))
    g = TA.__dict__  # noqa (unused)
    delta = FROZEN["K"] * 1.5 * (1.0 - exp_h)   # win, 2-goal margin
    R[h] += delta; R[a] -= delta
    after = E.win_prob(R, a, h)
    print(f"  Saudi Arabia beat Uruguay 2-0 ->")
    print(f"  after:  Uruguay {R[a]:.0f} Elo, Saudi {R[h]:.0f} Elo "
          f"-> Uruguay {after['P_a']:.0%}  (moved {(after['P_a']-before['P_a'])*100:+.1f} pts)")
    print("  note: ratings shifted measurably, not violently - one game is one game.")
