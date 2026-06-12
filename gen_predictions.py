"""Generate predictions.json for the dashboard: every upcoming WC2026 fixture
scored with Elo (quality, dominant) + climate (small nudge), plus a team table."""
import json
import fetch_data as fd
import elo as E
import team_adaptation as TA

HEAT_MAX_ELO = 40
ALT_MAX_ELO = 60

venues = {v["stadium_real_name"]: v for v in
          json.load(open("wc2026_venues.json"))["venues"]}
bases = {t["team"]: t for t in
         json.load(open("team_climate_baseline.json"))["teams"]}

# Best-effort star player per nation as of early 2026. EDIT freely, or replace
# at runtime with API-Football's top-rated squad player. Verify vs announced squads.
STARS = {
    "Algeria": "Riyad Mahrez", "Argentina": "Julian Alvarez", "Australia": "Mathew Ryan",
    "Austria": "David Alaba", "Belgium": "Jeremy Doku", "Bosnia and Herzegovina": "Edin Dzeko",
    "Brazil": "Vinicius Junior", "Canada": "Alphonso Davies", "Cape Verde": "Ryan Mendes",
    "Colombia": "Luis Diaz", "Croatia": "Josko Gvardiol", "Curaçao": "Juninho Bacuna",
    "Czech Republic": "Patrik Schick", "DR Congo": "Yoane Wissa", "Ecuador": "Moises Caicedo",
    "Egypt": "Mohamed Salah", "England": "Jude Bellingham", "France": "Kylian Mbappe",
    "Germany": "Jamal Musiala", "Ghana": "Mohammed Kudus", "Haiti": "Frantzdy Pierrot",
    "Iran": "Mehdi Taremi", "Iraq": "Aymen Hussein", "Ivory Coast": "Simon Adingra",
    "Japan": "Takefusa Kubo", "Jordan": "Mousa Al-Tamari", "Mexico": "Santiago Gimenez",
    "Morocco": "Achraf Hakimi", "Netherlands": "Cody Gakpo", "New Zealand": "Chris Wood",
    "Norway": "Erling Haaland", "Panama": "Adalberto Carrasquilla", "Paraguay": "Miguel Almiron",
    "Portugal": "Rafael Leao", "Qatar": "Akram Afif", "Saudi Arabia": "Salem Al-Dawsari",
    "Scotland": "Scott McTominay", "Senegal": "Nicolas Jackson", "South Africa": "Lyle Foster",
    "South Korea": "Son Heung-min", "Spain": "Lamine Yamal", "Sweden": "Alexander Isak",
    "Switzerland": "Granit Xhaka", "Tunisia": "Hannibal Mejbri", "Turkey": "Arda Guler",
    "United States": "Christian Pulisic", "Uruguay": "Federico Valverde",
    "Uzbekistan": "Eldor Shomurodov",
}

try:
    RESULTS = json.load(open("wc2026_results.json"))
except FileNotFoundError:
    RESULTS = {}
R = E.strength(RESULTS)

import suspensions as SUS
try:
    UNAVAIL = json.load(open("wc2026_unavailable.json"))
except FileNotFoundError:
    UNAVAIL = []
# importance: a team's star (from STARS) ~1.0, else the entry's value or 0.3
def _importance(team):
    imp = {STARS.get(team, ""): 1.0}
    for u in UNAVAIL:
        if u.get("team") == team and "importance" in u:
            imp[u["player"]] = u["importance"]
    return imp
UNAVAIL_SET = {(u["team"], u["player"]) for u in UNAVAIL}
def avail_pen(team):
    return SUS.availability_penalty(team, UNAVAIL_SET, _importance(team))
rows = fd.get_international_results()
fixtures = fd.get_wc2026_fixtures(rows)


def favourite(p):
    m = max(("home", p["P_a"]), ("draw", p["P_draw"]), ("away", p["P_b"]),
            key=lambda x: x[1])
    return m[0]


preds = []
for f in fixtures:
    vname = fd.CITY_TO_VENUE.get(f["city"])
    v = venues.get(vname)
    hb, ab = bases.get(f["home_team"]), bases.get(f["away_team"])
    if not (v and hb and ab):
        continue
    neutral = str(f.get("neutral", "")).lower() in ("true", "1")

    base = E.win_prob(R, f["home_team"], f["away_team"], neutral=neutral)

    edge = TA.fixture_edge(hb, ab, v)
    climate_home_elo = edge["heat_edge"] * HEAT_MAX_ELO + edge["altitude_edge"] * ALT_MAX_ELO
    hp, ap = avail_pen(f["home_team"]), avail_pen(f["away_team"])
    R2 = dict(R)
    R2[f["home_team"]] = R2.get(f["home_team"], E.START) + climate_home_elo + hp
    R2[f["away_team"]] = R2.get(f["away_team"], E.START) + ap
    comb = E.win_prob(R2, f["home_team"], f["away_team"], neutral=neutral)

    eh, ea = R.get(f["home_team"], E.START), R.get(f["away_team"], E.START)
    gap = abs(eh - ea)
    fav_team = f["home_team"] if comb["P_a"] >= comb["P_b"] else f["away_team"]

    # human read
    rating_fav = f["home_team"] if eh >= ea else f["away_team"]
    read = f"{rating_fav} favoured on a {gap:.0f}-point rating edge."
    climate_note = ""
    if abs(edge["altitude_edge"]) >= 0.1:
        who = f["home_team"] if edge["altitude_edge"] > 0 else f["away_team"]
        climate_note = f" Altitude at {f['city']} leans to {who}."
    elif abs(edge["heat_edge"]) >= 0.3:
        who = f["home_team"] if edge["heat_edge"] > 0 else f["away_team"]
        climate_note = f" {v['heat_exposure'].title()} heat leans to {who}."
    read += climate_note
    out_h = [u["player"] for u in UNAVAIL if u["team"] == f["home_team"]]
    out_a = [u["player"] for u in UNAVAIL if u["team"] == f["away_team"]]
    if out_h:
        read += f" {f['home_team']} without {', '.join(out_h)}."
    if out_a:
        read += f" {f['away_team']} without {', '.join(out_a)}."

    preds.append({
        "date": f["date"], "city": f["city"], "country": f["country"],
        "venue": vname, "heat": v["heat_exposure"],
        "controlled": v["climate_controlled"], "altitude_flag": v["altitude_flag"],
        "elev_m": v["elevation_m"],
        "home": f["home_team"], "away": f["away_team"],
        "home_star": STARS.get(f["home_team"], ""), "away_star": STARS.get(f["away_team"], ""),
        "elo_home": round(eh), "elo_away": round(ea), "gap": round(gap),
        "p_home": comb["P_a"], "p_draw": comb["P_draw"], "p_away": comb["P_b"],
        "p_home_base": base["P_a"], "p_away_base": base["P_b"],
        "heat_edge": edge["heat_edge"], "alt_edge": edge["altitude_edge"],
        "climate_elo": round(climate_home_elo, 1),
        "favourite": fav_team, "neutral": neutral, "read": read,
    })

preds.sort(key=lambda x: (x["date"], x["city"]))

teams = []
for name, b in bases.items():
    teams.append({
        "team": name, "elo": round(R.get(name, E.START)),
        "star": STARS.get(name, ""),
        "base_c": b["base_jun_jul_high_c"], "base_m": b["base_elevation_m"],
        "hemisphere": b["hemisphere"], "europe": b["squad_europe_based"],
    })
teams.sort(key=lambda x: -x["elo"])
for i, t in enumerate(teams, 1):
    t["rank"] = i

out = {
    "generated": "2026-06-11",
    "n_fixtures": len(preds), "n_teams": len(teams), "n_venues": len(venues),
    "fixtures": preds, "teams": teams,
    "venues": [{"name": v["stadium_real_name"], "city": v["city"],
                "country": v["country"], "heat": v["heat_exposure"],
                "controlled": v["climate_controlled"],
                "altitude_flag": v["altitude_flag"], "elev_m": v["elevation_m"],
                "high_c": v["typical_jun_jul_high_c"], "roof": v["roof_type"]}
               for v in venues.values()],
}
json.dump(out, open("predictions.json", "w"), indent=1)
print("fixtures:", len(preds), "| teams:", len(teams), "| venues:", len(venues))
print("sample:", preds[0]["home"], "v", preds[0]["away"],
      "->", preds[0]["p_home"], preds[0]["p_draw"], preds[0]["p_away"])
