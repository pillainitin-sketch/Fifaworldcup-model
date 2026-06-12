"""
Monte Carlo WC2026 projection on FIFA's OFFICIAL bracket.

Real group draw (Dec 5 2025), real Round-of-32 slot map and knockout tree
(matches 73-104), venues per knockout match (so climate + altitude apply in the
knockouts too), and host advantage when Mexico/USA/Canada play at home.

The only approximated piece: which of the 8 qualifying third-placed teams fills
each third-place slot. FIFA's Annex C fixes one permutation among the valid ones;
we solve the same constraints (each slot's allowed group set, no same-group) with
bipartite matching, which is structurally correct though it may differ from the
exact Annex C row. Everything else is the official structure.

Conditions on any entered results passed via wc2026_results.json.
"""
import json, random
import fetch_data as fd
import elo as E
import team_adaptation as TA

N = 10000
random.seed(7)

VEN = {v["stadium_real_name"]: v for v in json.load(open("wc2026_venues.json"))["venues"]}
bases = {t["team"]: t for t in json.load(open("team_climate_baseline.json"))["teams"]}
try: RESULTS = json.load(open("wc2026_results.json"))
except FileNotFoundError: RESULTS = {}
R = E.strength(RESULTS)
fixtures = fd.get_wc2026_fixtures()

GROUPS = {
 'A':['Mexico','South Korea','South Africa','Czech Republic'],
 'B':['Canada','Bosnia and Herzegovina','Qatar','Switzerland'],
 'C':['Brazil','Morocco','Scotland','Haiti'],
 'D':['United States','Paraguay','Australia','Turkey'],
 'E':['Germany','Ecuador','Ivory Coast','Curaçao'],
 'F':['Netherlands','Japan','Tunisia','Sweden'],
 'G':['Belgium','Iran','Egypt','New Zealand'],
 'H':['Spain','Uruguay','Saudi Arabia','Cape Verde'],
 'I':['France','Senegal','Norway','Iraq'],
 'J':['Argentina','Austria','Algeria','Jordan'],
 'K':['Portugal','Colombia','Uzbekistan','DR Congo'],
 'L':['England','Croatia','Panama','Ghana'],
}
TEAM2GROUP = {t:g for g,ts in GROUPS.items() for t in ts}
HOSTS = {'Mexico':'Mexico','United States':'USA','Canada':'Canada'}

# R32: match -> (home_slot, away_slot, venue). slot = ('W',g)|('RU',g)|('3',frozenset)
def S3(*gs): return ('3', frozenset(gs))
R32 = {
 73:(('RU','A'),('RU','B'),"SoFi Stadium"),
 74:(('W','E'),S3('A','B','C','D','F'),"Gillette Stadium"),
 75:(('W','F'),('RU','C'),"Estadio BBVA"),
 76:(('W','C'),('RU','F'),"NRG Stadium"),
 77:(('W','I'),S3('C','D','F','G','H'),"MetLife Stadium"),
 78:(('RU','E'),('RU','I'),"AT&T Stadium"),
 79:(('W','A'),S3('C','E','F','H','I'),"Estadio Azteca"),
 80:(('W','L'),S3('E','H','I','J','K'),"Mercedes-Benz Stadium"),
 81:(('W','D'),S3('B','E','F','I','J'),"Levi's Stadium"),
 82:(('W','G'),S3('A','E','H','I','J'),"Lumen Field"),
 83:(('RU','K'),('RU','L'),"BMO Field"),
 84:(('W','H'),('RU','J'),"SoFi Stadium"),
 85:(('W','B'),S3('E','F','G','I','J'),"BC Place"),
 86:(('W','J'),('RU','H'),"Hard Rock Stadium"),
 87:(('W','K'),S3('D','E','I','J','L'),"Arrowhead Stadium"),
 88:(('RU','D'),('RU','G'),"AT&T Stadium"),
}
# knockout tree: match -> (feeder_a, feeder_b, venue)
TREE = {
 89:(74,77,"Lincoln Financial Field"),90:(73,75,"NRG Stadium"),
 91:(76,78,"MetLife Stadium"),92:(79,80,"Estadio Azteca"),
 93:(83,84,"AT&T Stadium"),94:(81,82,"Lumen Field"),
 95:(86,88,"Mercedes-Benz Stadium"),96:(85,87,"BC Place"),
 97:(89,90,"Gillette Stadium"),98:(93,94,"SoFi Stadium"),
 99:(91,92,"Hard Rock Stadium"),100:(95,96,"Arrowhead Stadium"),
 101:(97,98,"AT&T Stadium"),102:(99,100,"Mercedes-Benz Stadium"),
 104:(101,102,"MetLife Stadium"),
}

def is_home(team, vname):
    c = HOSTS.get(team); return bool(c and VEN[vname]["country"] == c)

def ko_elos(a, b, vname):
    ea, eb = R.get(a,E.START), R.get(b,E.START)
    if a in bases and b in bases:
        e = TA.fixture_edge(bases[a], bases[b], VEN[vname])
        ea += e["heat_edge"]*40 + e["altitude_edge"]*60
    ea += 65 if is_home(a,vname) else 0
    eb += 65 if is_home(b,vname) else 0
    return ea, eb

def ko_winner(a, b, vname):
    ea, eb = ko_elos(a,b,vname)
    pa = 1/(1+10**((eb-ea)/400))
    return a if random.random() < pa else b

# precompute group fixtures with probs (+ fixed results)
GFX = {g: [] for g in GROUPS}
for f in fixtures:
    g = TEAM2GROUP.get(f["home_team"])
    if g is None or TEAM2GROUP.get(f["away_team"]) != g:
        continue
    v = VEN.get(fd.CITY_TO_VENUE.get(f["city"]))
    ea, eb = R.get(f["home_team"],E.START), R.get(f["away_team"],E.START)
    if v and f["home_team"] in bases and f["away_team"] in bases:
        e = TA.fixture_edge(bases[f["home_team"]], bases[f["away_team"]], v)
        ea += e["heat_edge"]*40 + e["altitude_edge"]*60
    pa = 1/(1+10**((eb-ea)/400)); draw = 0.27-0.20*abs(pa-0.5)
    key = f"{f['date']}|{f['home_team']}|{f['away_team']}"
    GFX[g].append((f["home_team"], f["away_team"], pa*(1-draw), draw, key))

# sanity: every group has 6 fixtures
assert all(len(GFX[g])==6 for g in GROUPS), {g:len(GFX[g]) for g in GROUPS}

def match_thirds(third_by_group):
    """Bipartite match: assign qualifying thirds (group->team) to the 8 third
    slots respecting each slot's allowed group set."""
    slots = [(m, R32[m][1][1]) for m in R32 if R32[m][1][0]=='3']
    groups = list(third_by_group)
    adj = {m:[g for g in groups if g in allowed] for m,allowed in slots}
    matchM = {}
    def try_assign(m, seen):
        for g in adj[m]:
            if g in seen: continue
            seen.add(g)
            if g not in matchM.values() or try_assign(
                    [k for k,v in matchM.items() if v==g][0], seen):
                matchM[m]=g; return True
        return False
    for m,_ in slots:
        try_assign(m, set())
    return {m: third_by_group[g] for m,g in matchM.items()}

def sim_once(track):
    W,RU,thirds={}, {}, []
    for g,fxs in GFX.items():
        pts={t:0 for t in GROUPS[g]}
        for h,a,ph,pd,key in fxs:
            fx=RESULTS.get(key)
            if fx: r = "h" if fx[0]>fx[1] else "a" if fx[0]<fx[1] else "d"
            else:
                x=random.random(); r="h" if x<ph else "d" if x<ph+pd else "a"
            if r=="h": pts[h]+=3
            elif r=="a": pts[a]+=3
            else: pts[h]+=1; pts[a]+=1
        rank=sorted(GROUPS[g], key=lambda t:(pts[t], R.get(t,E.START)), reverse=True)
        W[g],RU[g]=rank[0],rank[1]
        thirds.append((pts[rank[2]], R.get(rank[2],E.START), g, rank[2]))
    thirds.sort(reverse=True)
    qual_thirds = {g:t for _,_,g,t in thirds[:8]}
    slot3 = match_thirds(qual_thirds)
    for t in list(W.values())+list(RU.values())+list(qual_thirds.values()):
        track[t]["R32"]+=1

    def resolve(slot, m=None):
        typ=slot[0]
        if typ=='W': return W[slot[1]]
        if typ=='RU': return RU[slot[1]]
        return slot3[m]
    res={}
    for m,(sa,sb,v) in R32.items():
        a=resolve(sa,m); b=resolve(sb,m)
        res[m]=ko_winner(a,b,v)
    rounds={89:"R16",90:"R16",91:"R16",92:"R16",93:"R16",94:"R16",95:"R16",96:"R16",
            97:"QF",98:"QF",99:"QF",100:"QF",101:"SF",102:"SF",104:"F"}
    for m,(fa,fb,v) in TREE.items():
        a,b=res[fa],res[fb]; w=ko_winner(a,b,v); res[m]=w
        track[w][rounds[m]]+=1
        if m==104: track[w]["W"]+=1

ALL=[t for ts in GROUPS.values() for t in ts]
track={t:{k:0 for k in ["R32","R16","QF","SF","F","W"]} for t in ALL}
for _ in range(N): sim_once(track)

print(f"Conditioned on {len(RESULTS)} result(s).\n" if RESULTS else "")
print(f"=== Probabilities ({N} sims) ===")
print(f"{'team':<16}{'R16':>6}{'QF':>6}{'SF':>6}{'Final':>7}{'Win':>6}")
ranked=sorted(track.items(), key=lambda x:-x[1]["W"])
for t,c in ranked[:16]:
    print(f"{t:<16}{c['R16']/N*100:>5.0f}{c['QF']/N*100:>6.0f}{c['SF']/N*100:>6.0f}"
          f"{c['F']/N*100:>7.0f}{c['W']/N*100:>6.1f}")

# deterministic projected bracket: top-2 by Elo per group, best thirds by Elo, favourite advances
def proj():
    W={g:max(ts,key=lambda t:R.get(t,E.START)) for g,ts in GROUPS.items()}
    RU={g:sorted(ts,key=lambda t:R.get(t,E.START),reverse=True)[1] for g,ts in GROUPS.items()}
    thirds=sorted(((R.get(sorted(ts,key=lambda t:R.get(t,E.START),reverse=True)[2],E.START),g,
                    sorted(ts,key=lambda t:R.get(t,E.START),reverse=True)[2]) for g,ts in GROUPS.items()),
                  reverse=True)[:8]
    slot3=match_thirds({g:t for _,g,t in thirds})
    def res(slot,m=None): return W[slot[1]] if slot[0]=='W' else RU[slot[1]] if slot[0]=='RU' else slot3[m]
    out={}; r={}
    for m,(sa,sb,v) in R32.items():
        a,b=res(sa,m),res(sb,m); fav=max(a,b,key=lambda t:ko_elos(a,b,v)[0] if t==a else ko_elos(a,b,v)[1])
        r[m]=fav; out.setdefault("R32",[]).append({"m":m,"home":a,"away":b,"venue":v,"fav":fav})
    for m,(fa,fb,v) in TREE.items():
        a,b=r[fa],r[fb]; fav=max(a,b,key=lambda t:ko_elos(a,b,v)[0] if t==a else ko_elos(a,b,v)[1])
        r[m]=fav
        lbl={89:"R16",97:"QF",101:"SF",104:"Final"}.get(m) or ("R16" if m<97 else "QF" if m<101 else "SF" if m<104 else "Final")
        out.setdefault(lbl,[]).append({"m":m,"home":a,"away":b,"venue":v,"fav":fav})
    out["winner"]=r[104]
    return out

bracket=proj()
print("\n=== Projected bracket (favourite path, official slotting) ===")
print("QF:", " | ".join(f"{x['home']} v {x['away']}" for x in bracket["QF"]))
print("SF:", " | ".join(f"{x['home']} v {x['away']}" for x in bracket["SF"]))
print("Final:", bracket["Final"][0]["home"], "v", bracket["Final"][0]["away"])
print("Projected winner:", bracket["winner"])

json.dump({"n":N,"conditioned":len(RESULTS),
           "probs":[{"team":t,**{k:round(c[k]/N,4) for k in c}} for t,c in ranked],
           "bracket":bracket}, open("tournament.json","w"), indent=1)
print("\nwrote tournament.json")
