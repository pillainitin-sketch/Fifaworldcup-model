"""
Team heat + altitude adaptation feature for the WC2026 model.

Inputs:
  wc2026_venues.json          (venue heat/altitude, climate_controlled flag)
  team_climate_baseline.json  (per-nation June-July baseline + elevation)
  WC2026 fixtures             (from fetch_data.get_wc2026_fixtures)

Output per fixture: a relative heat edge and altitude edge in [-1, 1],
positive = favours the home_team side of the record. These are small,
transparent adjustments meant to nudge a ratings/market model, NOT to
replace it. Calibrate the weights during backtest.
"""

import json
import fetch_data as fd

INDOOR_AC_HEAT_C = 22      # effective on-pitch heat inside a climate-controlled dome
CANOPY_SHADE_C = 2         # degrees shaved off by a roof canopy with open sides
ALT_THRESHOLD_M = 1500     # altitude only bites meaningfully above this
ALT_SHOCK_RANGE_M = 1500   # metres of excess that saturate the altitude penalty
HEAT_SHOCK_RANGE_C = 18    # degrees of excess heat that saturate the heat penalty


def load(path):
    return json.load(open(path, encoding="utf-8"))


def venue_effective_heat(v):
    """On-pitch heat the players actually face, accounting for roof/AC."""
    if v["climate_controlled"]:
        return INDOOR_AC_HEAT_C
    h = v["typical_jun_jul_high_c"]
    if v["roof_type"] == "fixed_canopy_open_sides":
        h -= CANOPY_SHADE_C
    return h


def clamp(x, lo=0.0, hi=1.0):
    return max(lo, min(hi, x))


def heat_penalty(team_base_c, venue_eff_c):
    """0 = fully adapted (venue same/cooler than home). 1 = max heat shock."""
    excess = venue_eff_c - team_base_c
    return clamp(excess / HEAT_SHOCK_RANGE_C)


def altitude_penalty(team_base_m, venue_m):
    """0 below threshold or if already higher-adapted; up to 1 for a sea-level
    team at extreme altitude (Mexico City)."""
    if venue_m < ALT_THRESHOLD_M:
        return 0.0
    reference = max(team_base_m, ALT_THRESHOLD_M)
    excess = venue_m - reference
    return clamp(excess / ALT_SHOCK_RANGE_M)


def team_penalties(team_base, venue):
    return {
        "heat": round(heat_penalty(team_base["base_jun_jul_high_c"],
                                   venue_effective_heat(venue)), 3),
        "altitude": round(altitude_penalty(team_base["base_elevation_m"],
                                           venue["elevation_m"]), 3),
    }


def fixture_edge(home_base, away_base, venue):
    """Relative edge: away_penalty - home_penalty. Positive favours home side."""
    hp = team_penalties(home_base, venue)
    ap = team_penalties(away_base, venue)
    return {
        "heat_edge": round(ap["heat"] - hp["heat"], 3),
        "altitude_edge": round(ap["altitude"] - hp["altitude"], 3),
        "home_pen": hp, "away_pen": ap,
    }


# ---------------------------------------------------------------------------
# Squad-based refinement (run with your API-Football key for higher fidelity)
# ---------------------------------------------------------------------------
def refine_baseline_from_squad(squad_player_clubs, club_climate_lookup):
    """
    squad_player_clubs : list of club names for the called-up squad
    club_climate_lookup: dict club_name -> {"jun_jul_high_c":.., "elevation_m":..}
                         (build from API-Football team/venue endpoints + Open-Meteo
                          on each club's home-city coordinates)
    Returns a squad-weighted baseline replacing the domestic home-city prior.
    """
    temps, elevs = [], []
    for club in squad_player_clubs:
        c = club_climate_lookup.get(club)
        if c:
            temps.append(c["jun_jul_high_c"])
            elevs.append(c["elevation_m"])
    if not temps:
        return None
    return {
        "base_jun_jul_high_c": round(sum(temps) / len(temps), 1),
        "base_elevation_m": round(sum(elevs) / len(elevs)),
        "n_players_matched": len(temps),
    }


# ---------------------------------------------------------------------------
# Demo: score every WC2026 group fixture for heat + altitude edge
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    venues = {v["stadium_real_name"]: v for v in load("wc2026_venues.json")["venues"]}
    bases = {t["team"]: t for t in load("team_climate_baseline.json")["teams"]}

    rows = fd.get_international_results()
    fixtures = fd.get_wc2026_fixtures(rows)

    scored = []
    for f in fixtures:
        venue_name = fd.CITY_TO_VENUE.get(f["city"])
        v = venues.get(venue_name)
        hb, ab = bases.get(f["home_team"]), bases.get(f["away_team"])
        if not (v and hb and ab):
            continue
        e = fixture_edge(hb, ab, v)
        scored.append({
            "date": f["date"], "city": f["city"], "venue": venue_name,
            "home": f["home_team"], "away": f["away_team"], **e,
        })

    print(f"scored {len(scored)} fixtures\n")

    print("=== Biggest HEAT edges (one side far better adapted) ===")
    for s in sorted(scored, key=lambda x: -abs(x["heat_edge"]))[:8]:
        fav = s["home"] if s["heat_edge"] > 0 else s["away"]
        print(f"  {s['date']}  {s['home']:<14} v {s['away']:<14} @ {s['city']:<14} "
              f"heat_edge={s['heat_edge']:+.2f} -> favours {fav}")

    print("\n=== Biggest ALTITUDE edges (Mexico City / Guadalajara) ===")
    alt = [s for s in scored if abs(s["altitude_edge"]) > 0]
    for s in sorted(alt, key=lambda x: -abs(x["altitude_edge"]))[:8]:
        fav = s["home"] if s["altitude_edge"] > 0 else s["away"]
        print(f"  {s['date']}  {s['home']:<14} v {s['away']:<14} @ {s['city']:<14} "
              f"alt_edge={s['altitude_edge']:+.2f} -> favours {fav}")

    print("\n=== Sanity check: hottest open venues neutralised indoors ===")
    for vn in ["NRG Stadium", "Arrowhead Stadium"]:
        v = venues[vn]
        print(f"  {vn:<20} city_high={v['typical_jun_jul_high_c']}C "
              f"controlled={v['climate_controlled']} -> effective={venue_effective_heat(v)}C")
