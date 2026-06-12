"""
Minimal international Elo from the open results dataset.
This is the DOMINANT signal: team quality. Climate is a small nudge on top.

World-Football-style: home advantage when not neutral, goal-difference
multiplier on the K update. Quick and transparent, not a substitute for the
market line, but it puts the quality gap on a real scale.
"""

import math
import json
import fetch_data as fd

START, K, HOME_ADV = 1500.0, 32.0, 65.0


def gd_multiplier(margin):
    if margin <= 1:
        return 1.0
    if margin == 2:
        return 1.5
    return (11 + margin) / 8.0


def build_elo(since="2002-01-01"):
    rows = fd.played_results(since=since)
    rows.sort(key=lambda r: r["date"])
    R = {}
    for r in rows:
        h, a = r["home_team"], r["away_team"]
        try:
            hs, as_ = int(r["home_score"]), int(r["away_score"])
        except ValueError:
            continue
        Rh = R.get(h, START)
        Ra = R.get(a, START)
        neutral = str(r.get("neutral", "")).lower() in ("true", "1")
        adj = 0 if neutral else HOME_ADV
        Eh = 1 / (1 + 10 ** ((Ra - (Rh + adj)) / 400))
        Sh = 1.0 if hs > as_ else 0.0 if hs < as_ else 0.5
        g = gd_multiplier(abs(hs - as_))
        delta = K * g * (Sh - Eh)
        R[h] = Rh + delta
        R[a] = Ra - delta
    return R


def win_prob(R, a, b, neutral=True):
    """P(a beats b), draw split out crudely for a 3-way readout."""
    adj = 0 if neutral else HOME_ADV
    pa = 1 / (1 + 10 ** ((R.get(b, START) - (R.get(a, START) + adj)) / 400))
    # crude draw share: higher near even matchups
    draw = 0.27 - 0.20 * abs(pa - 0.5)
    return {"P_a": round(pa * (1 - draw), 3),
            "P_draw": round(draw, 3),
            "P_b": round((1 - pa) * (1 - draw), 3)}


def _apply_results(R, results):
    fixtures = fd.get_wc2026_fixtures()
    bykey = {f"{f['date']}|{f['home_team']}|{f['away_team']}": f for f in fixtures}
    for key in sorted(results, key=lambda k: bykey.get(k, {}).get("date", "9999")):
        f = bykey.get(key)
        if not f:
            continue
        hs, as_ = results[key]
        h, a = f["home_team"], f["away_team"]
        neutral = str(f.get("neutral", "")).lower() in ("true", "1")
        Rh, Ra = R.get(h, START), R.get(a, START)
        adj = 0 if neutral else HOME_ADV
        Eh = 1 / (1 + 10 ** ((Ra - (Rh + adj)) / 400))
        Sh = 1.0 if hs > as_ else 0.0 if hs < as_ else 0.5
        d = K * gd_multiplier(abs(hs - as_)) * (Sh - Eh)
        R[h] = Rh + d
        R[a] = Ra - d
    return R


def build_elo_with_results(results, since="2002-01-01"):
    R = build_elo(since)
    return _apply_results(R, results) if results else R


def value_rating(values):
    """Map squad market value to a rating-space prior via z-scored log value."""
    import math
    logs = {t: math.log(v) for t, v in values.items() if v > 0}
    mean = sum(logs.values()) / len(logs)
    std = (sum((x - mean) ** 2 for x in logs.values()) / len(logs)) ** 0.5 or 1.0
    return {t: 1500 + ((logs[t] - mean) / std) * 200 for t in logs}


def blend_value(R, values, alpha=0.7):
    """Blend Elo (weight alpha) with the value prior. Pulls over-rated teams down
    and under-rated teams up, correcting small-sample Elo quirks."""
    vr = value_rating(values)
    return {t: (alpha * R.get(t, START) + (1 - alpha) * vr[t]) if t in vr
            else R.get(t, START) for t in set(R) | set(vr)}


def _load_values():
    try:
        return json.load(open("squad_value.json"))["values"]
    except FileNotFoundError:
        return {}


def strength(results=None, alpha=0.7):
    """The model's team strength: Elo blended with squad value, then re-rated
    from any entered results. Use this everywhere instead of build_elo()."""
    R = build_elo()
    values = _load_values()
    if values:
        R = blend_value(R, values, alpha)
    return _apply_results(R, results) if results else R


if __name__ == "__main__":
    R = build_elo()

    print("=== Top 12 by Elo (sanity check) ===")
    for t, r in sorted(R.items(), key=lambda x: -x[1])[:12]:
        print(f"  {t:<16} {r:6.0f}")

    print("\n=== Saudi Arabia vs Uruguay (neutral) ===")
    print(f"  Uruguay Elo:      {R['Uruguay']:.0f}")
    print(f"  Saudi Arabia Elo: {R['Saudi Arabia']:.0f}")
    print(f"  gap:              {R['Uruguay']-R['Saudi Arabia']:.0f} points")
    p = win_prob(R, "Uruguay", "Saudi Arabia")
    print(f"  Elo only -> Uruguay {p['P_a']:.0%} / draw {p['P_draw']:.0%} / Saudi {p['P_b']:.0%}")

    # Climate nudge: heat_edge +0.83 favoured Saudi at Miami. Map edge -> Elo pts.
    CLIMATE_ELO_MAX = 40   # an edge of 1.0 is worth at most 40 Elo (small)
    saudi_climate = 0.83 * CLIMATE_ELO_MAX
    R2 = dict(R); R2["Saudi Arabia"] += saudi_climate
    p2 = win_prob(R2, "Uruguay", "Saudi Arabia")
    print(f"  + climate (+{saudi_climate:.0f} Elo to Saudi for Miami heat):")
    print(f"  combined -> Uruguay {p2['P_a']:.0%} / draw {p2['P_draw']:.0%} / Saudi {p2['P_b']:.0%}")
    print(f"  climate moved Uruguay's win prob by {(p2['P_a']-p['P_a'])*100:+.1f} pts")
