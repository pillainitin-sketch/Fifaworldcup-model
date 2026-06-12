"""
WC2026 prediction tool - free data layer.

One module, every free source. No paid service required to start.

PROVEN LIVE (keyless, GitHub-hosted, run anywhere):
  - international_results : 49,472 internationals 1872..2026 incl. all WC2026 fixtures (CC0)
  - statsbomb_open_data   : event data + xG for WC 2022/2018, Euro 2024, Copa 2024, AFCON 2023

KEYLESS BUT NOT REACHABLE FROM SOME SANDBOXES (run on your own machine):
  - open_meteo            : match-day weather + elevation, no key, non-commercial CC BY 4.0
  - football_data_couk    : historical club results + closing odds (CSV) for odds backtest

FREE TIER, NEEDS YOUR KEY:
  - api_football          : live fixtures/lineups/odds/injuries during the tournament (RapidAPI)

Run:  python fetch_data.py
"""

import csv
import io
import json
import urllib.parse
import urllib.request
from datetime import datetime

UA = {"User-Agent": "wc2026-tool/1.0"}


def _get(url, headers=None):
    req = urllib.request.Request(url, headers={**UA, **(headers or {})})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


# ---------------------------------------------------------------------------
# 0. Venues (the file you already have)
# ---------------------------------------------------------------------------
def load_venues(path="wc2026_venues.json"):
    return json.load(open(path, encoding="utf-8"))["venues"]


# A lookup from the dataset's `city` strings to your venue records.
# The international_results `city` field uses these names for WC2026.
CITY_TO_VENUE = {
    "Mexico City": "Estadio Azteca", "Guadalajara": "Estadio Akron",
    "Monterrey": "Estadio BBVA", "Houston": "NRG Stadium",
    "Arlington": "AT&T Stadium", "Atlanta": "Mercedes-Benz Stadium",
    "Miami Gardens": "Hard Rock Stadium", "Kansas City": "Arrowhead Stadium",
    "Philadelphia": "Lincoln Financial Field", "East Rutherford": "MetLife Stadium",
    "Foxborough": "Gillette Stadium", "Santa Clara": "Levi's Stadium",
    "Inglewood": "SoFi Stadium", "Seattle": "Lumen Field",
    "Toronto": "BMO Field", "Vancouver": "BC Place",
    # the dataset uses precise municipality names for two Mexican metros:
    "Zapopan": "Estadio Akron", "Guadalupe": "Estadio BBVA",
}


# ---------------------------------------------------------------------------
# 1. International results  (PROVEN LIVE - CC0, no key)
#    -> schedule, form, Elo input, backtest set
# ---------------------------------------------------------------------------
RESULTS_URL = "https://raw.githubusercontent.com/martj42/international_results/master/results.csv"

def get_international_results():
    data = _get(RESULTS_URL).decode("utf-8")
    return list(csv.DictReader(io.StringIO(data)))

def get_wc2026_fixtures(rows=None):
    rows = rows or get_international_results()
    # future WC matches have empty scores; the 2026 edition is the upcoming one
    out = []
    for r in rows:
        if r["tournament"] == "FIFA World Cup" and r["date"] >= "2026-06-01" \
           and (r["home_score"] in ("", "NA", None)):
            out.append(r)
    return out

def played_results(rows=None, since="1990-01-01"):
    rows = rows or get_international_results()
    return [r for r in rows
            if r["home_score"] not in ("", "NA", None) and r["date"] >= since]


# ---------------------------------------------------------------------------
# 2. StatsBomb open data  (PROVEN LIVE - attribution required, no key)
#    -> xG and event-level analysis for past tournaments
# ---------------------------------------------------------------------------
SB = "https://raw.githubusercontent.com/statsbomb/open-data/master/data"

def get_statsbomb_competitions():
    return json.loads(_get(f"{SB}/competitions.json"))

def get_statsbomb_matches(competition_id, season_id):
    return json.loads(_get(f"{SB}/matches/{competition_id}/{season_id}.json"))

def get_statsbomb_events(match_id):
    return json.loads(_get(f"{SB}/events/{match_id}.json"))

# Useful ids:  WC 2022 -> comp 43 / season 106 ;  WC 2018 -> 43 / 3
#              Euro 2024 -> 55 / 282 ;  Copa America 2024 -> 223 / 282


# ---------------------------------------------------------------------------
# 3. Open-Meteo  (keyless; run on your own machine - api.open-meteo.com)
#    -> the heat + altitude feature
# ---------------------------------------------------------------------------
def get_venue_weather(lat, lng, date, hour, tz="UTC"):
    """Hourly weather for a venue at kickoff. date='YYYY-MM-DD', hour=int 0-23."""
    q = urllib.parse.urlencode({
        "latitude": lat, "longitude": lng,
        "hourly": "temperature_2m,relative_humidity_2m,apparent_temperature,wind_speed_10m,uv_index",
        "start_date": date, "end_date": date, "timezone": tz,
    })
    js = json.loads(_get(f"https://api.open-meteo.com/v1/forecast?{q}"))
    h = js["hourly"]
    i = hour if hour < len(h["time"]) else 0
    return {
        "elevation_m": js.get("elevation"),
        "temp_c": h["temperature_2m"][i],
        "humidity_pct": h["relative_humidity_2m"][i],
        "feels_like_c": h["apparent_temperature"][i],
        "wind_kmh": h["wind_speed_10m"][i],
        "uv_index": h["uv_index"][i],
    }

def get_elevation(lat, lng):
    q = urllib.parse.urlencode({"latitude": lat, "longitude": lng})
    js = json.loads(_get(f"https://api.open-meteo.com/v1/elevation?{q}"))
    return js["elevation"][0]

# For historical match-day weather (backtest), use the archive endpoint instead:
#   https://archive-api.open-meteo.com/v1/archive?latitude=..&longitude=..&start_date=..&end_date=..&hourly=temperature_2m,...


# ---------------------------------------------------------------------------
# 4. football-data.co.uk  (keyless CSV; club results + closing odds)
#    -> backtest your odds-vs-model methodology where odds are free & abundant
# ---------------------------------------------------------------------------
def get_clubdata_odds(div="E0", season="2425"):
    """div e.g. E0=EPL, SP1=La Liga, D1=Bundesliga. season e.g. '2425'."""
    url = f"https://www.football-data.co.uk/mmz4281/{season}/{div}.csv"
    data = _get(url).decode("latin-1")
    return list(csv.DictReader(io.StringIO(data)))
    # key odds columns: B365H/B365D/B365A (Bet365), PSCH/PSCD/PSCA (Pinnacle closing)


# ---------------------------------------------------------------------------
# 5. API-Football  (free tier, NEEDS your RapidAPI key)
#    -> live tournament layer: fixtures, lineups, odds, injuries
#    WC2026 = league id 1, season 2026.  Free tier: 100 req/day.
# ---------------------------------------------------------------------------
AF_HOST = "v3.football.api-sports.io"   # direct; or api-football-v1.p.rapidapi.com via RapidAPI

def _af(path, api_key, **params):
    q = urllib.parse.urlencode(params)
    url = f"https://{AF_HOST}/{path}?{q}"
    return json.loads(_get(url, headers={"x-apisports-key": api_key}))

def af_fixtures(api_key, league=1, season=2026):
    return _af("fixtures", api_key, league=league, season=season)

def af_lineups(api_key, fixture_id):
    return _af("fixtures/lineups", api_key, fixture=fixture_id)

def af_odds(api_key, fixture_id):
    return _af("odds", api_key, fixture=fixture_id)

def af_injuries(api_key, league=1, season=2026):
    return _af("injuries", api_key, league=league, season=season)


# ---------------------------------------------------------------------------
# Demo: run the keyless sources end to end
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("Pulling international results (CC0)...")
    rows = get_international_results()
    print(f"  {len(rows)} matches, {rows[0]['date']} -> {rows[-1]['date']}")

    fixtures = get_wc2026_fixtures(rows)
    print(f"  {len(fixtures)} WC2026 fixtures found")

    train = played_results(rows, since="2018-01-01")
    print(f"  {len(train)} played internationals since 2018 (Elo/backtest set)")

    print("\nStatsBomb open competitions (attribution: StatsBomb)...")
    comps = get_statsbomb_competitions()
    wc = {(c['competition_name'], c['season_name']) for c in comps
          if 'World Cup' in c['competition_name']}
    print(f"  {len(comps)} comp-seasons; World Cups: {sorted(wc)}")

    print("\nVenue join check (dataset city -> your venue file):")
    venues = load_venues()
    by_real = {v['stadium_real_name']: v for v in venues}
    missing = sorted({f['city'] for f in fixtures} - set(CITY_TO_VENUE))
    print(f"  unmatched cities: {missing if missing else 'none'}")

    print("\nNext (needs network / key):")
    print("  get_venue_weather(lat,lng,date,hour) -> heat feature  [Open-Meteo, no key]")
    print("  af_fixtures(YOUR_KEY) -> live tournament data         [API-Football free tier]")
