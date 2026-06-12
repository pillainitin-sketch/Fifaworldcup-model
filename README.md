# World Cup 2026 Prediction Model

A transparent, calibrated match and tournament forecasting model for the 2026
FIFA World Cup, with a live dashboard. Built from open data, honest about its
limits, and benchmarked against the betting market rather than claiming to beat
it.

**Live dashboard:** https://YOUR-USERNAME.github.io/REPO-NAME/
*(replace with your GitHub Pages link once it is live)*

## What it does

- Predicts every match as a three-way probability (win / draw / loss).
- Projects the full knockout bracket and each team's odds of reaching the
  round of 16, quarter-final, semi-final, final, and lifting the trophy.
- Updates as results come in: entered scores re-rate both teams and sharpen
  every subsequent prediction.
- Scores itself: a calibration panel tracks Brier score and log loss against a
  coin-flip baseline as real results are entered.

## How it works

Quality first, adjustments at the margin.

1. **Team strength** is an Elo rating built from international results since
   2002, then blended with squad market value to correct small-sample quirks.
2. **Heat and altitude** apply a small, declared adjustment per venue, switched
   off entirely in air-conditioned roofed stadiums. Effect is largest in open,
   hot venues and at altitude in Mexico City.
3. **Host advantage** is added when Mexico, the USA, or Canada play at home.
4. **Availability** (injuries, suspensions from red cards or two-yellow
   accumulation) lowers a team's strength for the affected match, weighted by
   how important the missing player is.
5. **The tournament** is simulated 10,000 times on FIFA's official bracket to
   produce advancement and title probabilities.

Per-match player performance (tackles, passes, ratings) is deliberately kept
out of the model. On tournament-size samples it overfits; the result already
carries the signal. That data lives in the match-detail view instead.

## Run it yourself

No third-party packages required (standard library only).

```
python refresh.py
```

This re-rates from any entered results (`wc2026_results.json`) and any flagged
absences (`wc2026_unavailable.json`), regenerates the predictions and the
tournament projection, and rebuilds `index.html`. Open `index.html` in a
browser, or push to GitHub Pages.

## Files

- `index.html` - the live dashboard (the only file the website needs)
- `fetch_data.py` - free data sources (results, weather, etc.)
- `elo.py` - team strength: Elo blended with squad value
- `team_adaptation.py` - heat and altitude adjustment
- `gen_predictions.py` - per-match predictions
- `tournament.py` - Monte Carlo projection on the official bracket
- `suspensions.py` - red/yellow/injury availability tracking
- `match_data.py` - optional API-Football pull (lineups, events, stats)
- `build_dashboard.py` - renders the dashboard from the data
- `refresh.py` - runs the whole pipeline
- `*.json` - venue, squad-value, and generated data files

## Data sources and attribution

- International match results: martj42/international_results (CC0).
- Event data: StatsBomb Open Data (used with attribution to StatsBomb).
- Weather and elevation: Open-Meteo (CC BY 4.0, non-commercial tier).
- Live fixtures, lineups, injuries: API-Football (optional, requires a key).

Squad values and star-player labels are approximate priors, editable in their
JSON files.

## Disclaimers

Not affiliated with, endorsed by, or connected to FIFA. Team and competition
names are used factually. Predictions are for interest and analysis only and
are not betting advice. The model makes no claim to beat the betting market.
