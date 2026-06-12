"""
Suspension / availability tracker -> feeds the NEXT match prediction.

A red card is content for the match it happened in. Its FORWARD value to the
model is the ban it triggers: the player misses the next match, so that team is
genuinely weaker for it. This is the AVAILABILITY channel (a legitimate model
input), not performance data. The size of the hit depends on WHO is out: a star
red is a big next-match problem, a fringe red is barely a blip.

FIFA rules applied:
  - direct red                       -> banned the next 1 match
  - 2 yellows in different matches    -> banned the next match
  - single yellows wiped after the QF -> an early booking can't cost the final
  - injury                            -> out until cleared (injuries feed/manual)
Confirm the exact 2026 yellow-wipe stage against FIFA's regulations.
"""

STAGES = ["group", "R32", "R16", "QF", "SF", "F"]


def build_unavailable(card_log, injuries=None, yellow_wipe_after="QF"):
    """
    card_log: chronological list of {team, player, type:'red'|'yellow', stage}
    injuries: optional list of {team, player}
    Returns: set of (team, player) unavailable for THEIR next match.
    """
    yellows = {}            # (team,player) -> running count of yellow matches
    banned = set()          # serving a ban next match
    wipe_idx = STAGES.index(yellow_wipe_after)

    for c in card_log:
        kp = (c["team"], c["player"])
        if c["type"] == "red":
            banned.add(kp)
        elif c["type"] == "yellow":
            yellows[kp] = yellows.get(kp, 0) + 1
            if yellows[kp] >= 2:
                banned.add(kp)
                yellows[kp] = 0          # reset once the ban is incurred
        # clear single yellows once we pass the wipe stage
        if STAGES.index(c["stage"]) > wipe_idx:
            yellows = {k: v for k, v in yellows.items() if v >= 2}

    for inj in (injuries or []):
        banned.add((inj["team"], inj["player"]))
    return banned


def availability_penalty(team, unavailable, importance, max_star_elo=40):
    """
    MODEL INPUT. Elo delta for `team`'s next match given who is out.
    importance: name -> 0..1 (first-choice star ~1.0, regular ~0.6, squad ~0.2).
    A star out costs ~max_star_elo; a fringe player costs little.
    """
    pen = sum(importance.get(p, 0.3) * max_star_elo
              for (t, p) in unavailable if t == team)
    return -round(pen, 1)


if __name__ == "__main__":
    # demo: importance map (from market value / API-Football rating in practice)
    importance = {"Lamine Yamal": 1.0, "Pedri": 0.9, "Rodri": 0.95,
                  "Dani Olmo": 0.6, "Fringe Back": 0.2}

    # Spain's next match base odds vs Saudi Arabia
    import elo as E
    R = E.build_elo()
    def wp(Rh, Ra):
        pa = 1 / (1 + 10 ** ((Ra - Rh) / 400)); d = 0.27 - 0.20 * abs(pa - 0.5)
        return pa * (1 - d)
    base = R["Spain"]; saudi = R["Saudi Arabia"]
    print(f"Spain base Elo {base:.0f}; next-match win prob {wp(base, saudi):.0%}\n")

    for who in ["Lamine Yamal", "Fringe Back"]:
        cards = [{"team": "Spain", "player": who, "type": "red", "stage": "group"}]
        out = build_unavailable(cards)
        pen = availability_penalty("Spain", out, importance)
        print(f"{who} sees red -> banned next match. penalty {pen:+.0f} Elo "
              f"-> win prob {wp(base + pen, saudi):.0%}")

    # two-yellow accumulation example
    yc = [{"team": "Spain", "player": "Rodri", "type": "yellow", "stage": "group"},
          {"team": "Spain", "player": "Rodri", "type": "yellow", "stage": "group"}]
    out = build_unavailable(yc)
    print(f"\nRodri picks up a 2nd yellow -> {('Spain','Rodri') in out and 'banned next match'}"
          f"; penalty {availability_penalty('Spain', out, importance):+.0f} Elo")
