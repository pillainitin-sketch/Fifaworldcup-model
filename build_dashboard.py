import json

data = json.load(open("predictions.json"))

TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>World Cup 2026 Prediction Model</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Inter:wght@400;500;600&family=Space+Mono:wght@400;700&display=swap" rel="stylesheet">
<style>
:root{
  --bg:#0C151E; --surface:#13202C; --surface2:#192836; --line:rgba(255,255,255,.07);
  --line2:rgba(255,255,255,.14); --text:#EAF1F6; --muted:#90A4B3; --faint:#5F7383;
  --gold:#F4B740; --home:#56A8E2; --away:#EC8159; --draw:#566776; --good:#46CF9C;
  --hot:#E8744F; --warm:#E5A93C; --cool:#3FB6A6; --indoor:#5B9BD6; --alt:#9B8CE0;
  --disp:'Space Grotesk',sans-serif; --body:'Inter',sans-serif; --mono:'Space Mono',monospace;
}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--text);font-family:var(--body);line-height:1.5;
  -webkit-font-smoothing:antialiased;background-image:radial-gradient( at 80% -10%,rgba(86,168,226,.10),transparent 55%),radial-gradient(at 0% 0%,rgba(244,183,64,.06),transparent 40%);}
.wrap{max-width:1080px;margin:0 auto;padding:0 20px 80px}
.num{font-family:var(--mono);font-feature-settings:"tnum"}
a{color:inherit}

/* hero */
header{padding:64px 0 36px;border-bottom:1px solid var(--line)}
.eyebrow{font-family:var(--mono);font-size:12px;letter-spacing:.22em;text-transform:uppercase;
  color:var(--gold);margin-bottom:18px}
h1{font-family:var(--disp);font-weight:700;font-size:clamp(38px,7vw,68px);line-height:.98;
  letter-spacing:-.02em}
h1 .yr{color:var(--faint);font-weight:500}
.lede{color:var(--muted);max-width:54ch;margin-top:18px;font-size:16px}
.chips{display:flex;flex-wrap:wrap;gap:10px;margin-top:28px}
.stat{background:var(--surface);border:1px solid var(--line);border-radius:11px;padding:11px 16px}
.stat b{font-family:var(--mono);font-size:20px;display:block;line-height:1.1}
.stat span{font-size:12px;color:var(--muted)}

/* section headings */
.sec{margin-top:48px}
.sec-h{display:flex;align-items:baseline;justify-content:space-between;gap:12px;margin-bottom:18px;
  border-bottom:1px solid var(--line);padding-bottom:10px}
.sec-h h2{font-family:var(--disp);font-weight:600;font-size:22px;letter-spacing:-.01em}
.sec-h .meta{font-family:var(--mono);font-size:12px;color:var(--faint)}

/* controls */
.controls{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin-bottom:20px}
.filt{font-family:var(--mono);font-size:12px;color:var(--muted);background:transparent;
  border:1px solid var(--line2);border-radius:999px;padding:7px 14px;cursor:pointer;transition:.15s}
.filt:hover{color:var(--text);border-color:var(--muted)}
.filt.on{background:var(--text);color:var(--bg);border-color:var(--text)}
.toggle{margin-left:auto;display:flex;align-items:center;gap:8px;font-size:13px;color:var(--muted);cursor:pointer}
.toggle input{accent-color:var(--gold);width:16px;height:16px}

/* fixture cards */
.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}
@media(max-width:720px){.grid{grid-template-columns:1fr}}
.card{background:var(--surface);border:1px solid var(--line);border-radius:14px;padding:16px 16px 14px;
  cursor:pointer;transition:border-color .15s,transform .15s}
.card:hover{border-color:var(--line2);transform:translateY(-2px)}
.card-top{display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-bottom:13px}
.date{font-family:var(--mono);font-size:11px;color:var(--faint);letter-spacing:.04em}
.dot{width:3px;height:3px;border-radius:50%;background:var(--faint)}
.place{font-size:12px;color:var(--muted)}
.cond{margin-left:auto;display:flex;gap:5px}
.tag{font-family:var(--mono);font-size:10px;letter-spacing:.04em;padding:3px 7px;border-radius:6px;
  border:1px solid transparent;text-transform:uppercase}
.t-hot{color:var(--hot);background:rgba(232,116,79,.12);border-color:rgba(232,116,79,.3)}
.t-warm{color:var(--warm);background:rgba(229,169,60,.12);border-color:rgba(229,169,60,.3)}
.t-cool{color:var(--cool);background:rgba(63,182,166,.12);border-color:rgba(63,182,166,.3)}
.t-indoor{color:var(--indoor);background:rgba(91,155,214,.12);border-color:rgba(91,155,214,.3)}
.t-alt{color:var(--alt);background:rgba(155,140,224,.14);border-color:rgba(155,140,224,.35)}

.teams{display:flex;justify-content:space-between;align-items:flex-start;gap:10px;margin-bottom:12px}
.side{flex:1;min-width:0}
.side.away{text-align:right}
.tname{font-family:var(--disp);font-weight:600;font-size:17px;letter-spacing:-.01em;
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.tname.fav{color:var(--gold)}
.telo{font-family:var(--mono);font-size:11px;color:var(--faint);margin-top:2px}
.vs{font-family:var(--mono);font-size:10px;color:var(--faint);align-self:center;padding-top:4px}

.bar{display:flex;height:8px;border-radius:5px;overflow:hidden;background:var(--surface2);margin-bottom:7px}
.seg-h{background:var(--home)} .seg-d{background:var(--draw)} .seg-a{background:var(--away)}
.pcts{display:flex;justify-content:space-between;font-family:var(--mono);font-size:12px}
.pcts .ph{color:var(--home)} .pcts .pd{color:var(--muted)} .pcts .pa{color:var(--away)}
.read{font-size:12.5px;color:var(--muted);margin-top:11px;line-height:1.45}

.detail{max-height:0;overflow:hidden;transition:max-height .28s ease}
.card.open .detail{max-height:200px}
.detail-in{margin-top:13px;padding-top:13px;border-top:1px solid var(--line);
  font-family:var(--mono);font-size:11.5px;color:var(--muted);display:grid;gap:6px}
.detail-in .row{display:flex;justify-content:space-between}
.detail-in .row b{color:var(--text);font-weight:700}
.swing.pos{color:var(--good)} .swing.neg{color:var(--away)}

.star{font-size:11px;color:var(--faint);margin-top:3px;display:flex;align-items:center;gap:5px}
.star::before{content:"";width:5px;height:5px;border-radius:50%;background:var(--gold);flex:0 0 auto}
.side.away .star{flex-direction:row-reverse}
.score{margin-top:11px;padding-top:11px;border-top:1px solid var(--line);display:flex;align-items:center;gap:8px;flex-wrap:wrap}
.score label{font-family:var(--mono);font-size:11px;color:var(--faint)}
.score input{width:44px;background:var(--surface2);border:1px solid var(--line2);border-radius:6px;
  color:var(--text);font-family:var(--mono);font-size:14px;text-align:center;padding:5px 0}
.score input:focus{outline:none;border-color:var(--gold)}
.score .sv{font-family:var(--mono);font-size:11px;color:var(--bg);background:var(--gold);border:none;
  border-radius:6px;padding:6px 13px;cursor:pointer;font-weight:700}
.result{margin-top:11px;padding-top:11px;border-top:1px solid var(--line);font-family:var(--mono);font-size:12px;
  display:flex;align-items:center;gap:10px;flex-wrap:wrap}
.result .fin{font-weight:700;font-size:14px}
.result .ok{color:var(--good)} .result .no{color:var(--away)}
.result .mp{color:var(--faint)}
.result .clr{font-family:var(--mono);font-size:11px;color:var(--faint);background:none;border:none;cursor:pointer;margin-left:auto}
.card.done{border-color:rgba(70,207,156,.22)}
.scorecard{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:6px}
@media(max-width:720px){.scorecard{grid-template-columns:repeat(2,1fr)}}
.metric{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:14px 16px}
.metric b{font-family:var(--mono);font-size:25px;display:block;line-height:1.05}
.metric span{font-size:11.5px;color:var(--muted)}
.metric small{font-family:var(--mono);font-size:10.5px;color:var(--faint);display:block;margin-top:3px}
.sc-note{font-size:12px;color:var(--faint);margin-top:8px;line-height:1.6}

/* team table */
.tbl{width:100%;border-collapse:collapse;font-size:13.5px}
.tbl th{text-align:left;font-family:var(--mono);font-size:11px;letter-spacing:.06em;text-transform:uppercase;
  color:var(--faint);padding:8px 10px;border-bottom:1px solid var(--line);cursor:pointer;user-select:none}
.tbl th:hover{color:var(--muted)}
.tbl td{padding:9px 10px;border-bottom:1px solid var(--line)}
.tbl tr:hover td{background:var(--surface)}
.tbl .r{text-align:right;font-family:var(--mono)}
.tbl .rk{color:var(--faint);font-family:var(--mono);width:34px}
.tbl .tm{font-family:var(--disp);font-weight:500}
.tbl .elo{color:var(--gold);font-weight:700}
.mini{font-size:11px;color:var(--faint)}

/* venues */
.vgrid{display:grid;grid-template-columns:repeat(2,1fr);gap:10px}
@media(max-width:720px){.vgrid{grid-template-columns:1fr}}
.vrow{display:flex;align-items:center;gap:10px;background:var(--surface);border:1px solid var(--line);
  border-radius:10px;padding:10px 13px}
.vrow .vc{flex:1;min-width:0}
.vrow .vn{font-family:var(--disp);font-weight:500;font-size:14px}
.vrow .vm{font-size:11px;color:var(--faint)}
.vrow .vt{font-family:var(--mono);font-size:11px;color:var(--muted);white-space:nowrap}

footer{margin-top:56px;padding-top:24px;border-top:1px solid var(--line);color:var(--faint);font-size:12.5px;line-height:1.7}
footer b{color:var(--muted);font-weight:600;font-family:var(--disp)}
footer a{color:var(--muted);text-decoration:underline;text-underline-offset:2px}

.proj-tbl{width:100%;border-collapse:collapse;font-size:13px;margin-bottom:22px}
.proj-tbl th{text-align:right;font-family:var(--mono);font-size:10.5px;letter-spacing:.05em;text-transform:uppercase;color:var(--faint);padding:7px 8px;border-bottom:1px solid var(--line)}
.proj-tbl th:nth-child(2){text-align:left}
.proj-tbl td{padding:8px;border-bottom:1px solid var(--line);font-family:var(--mono);text-align:right;color:var(--muted)}
.proj-tbl td.tm{font-family:var(--disp);text-align:left;font-weight:500;color:var(--text)}
.proj-tbl td.rk{color:var(--faint)}
.proj-tbl .wv{color:var(--gold);font-weight:700}
.proj-tbl .winbar{display:inline-block;height:6px;background:var(--gold);border-radius:3px;vertical-align:middle;margin-left:6px;opacity:.5}
.bracket{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;align-items:start}
@media(max-width:720px){.bracket{grid-template-columns:1fr}}
.bcol h4{font-family:var(--mono);font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:var(--faint);margin-bottom:10px}
.bmatch{background:var(--surface);border:1px solid var(--line);border-radius:10px;padding:9px 12px;margin-bottom:8px}
.bmatch .bt{font-family:var(--disp);font-size:13.5px;display:flex;justify-content:space-between;align-items:center;padding:2px 0;color:var(--muted)}
.bmatch .bt.win{color:var(--gold)}
.bmatch .bt .bv{font-family:var(--mono);font-size:9.5px;color:var(--faint);font-weight:400}
.champ{background:linear-gradient(180deg,rgba(244,183,64,.13),transparent);border:1px solid rgba(244,183,64,.35);border-radius:10px;padding:13px;text-align:center;margin-top:8px}
.champ .cl{font-family:var(--mono);font-size:10px;letter-spacing:.12em;text-transform:uppercase;color:var(--faint)}
.champ .cn{font-family:var(--disp);font-weight:700;font-size:20px;color:var(--gold);margin-top:3px}

.res-list{display:flex;flex-direction:column;gap:8px}
.res{background:var(--surface);border:1px solid var(--line);border-radius:11px;padding:11px 14px;
  display:grid;grid-template-columns:1fr auto;gap:7px 12px;align-items:center}
.res.miss{border-color:rgba(236,129,89,.28)}
.res .rm{display:flex;align-items:baseline;gap:9px;flex-wrap:wrap;min-width:0}
.res .rd{font-family:var(--mono);font-size:11px;color:var(--faint)}
.res .rt{font-family:var(--disp);font-weight:600;font-size:15px}
.res .rt .rs{font-family:var(--mono);font-weight:700;color:var(--text);margin:0 3px}
.res .badge{font-family:var(--mono);font-size:11px;padding:3px 9px;border-radius:6px;justify-self:end;white-space:nowrap}
.res .badge.ok{color:var(--good);background:rgba(70,207,156,.12)}
.res .badge.no{color:var(--away);background:rgba(236,129,89,.13)}
.res .rp{grid-column:1/-1;font-family:var(--mono);font-size:11.5px;color:var(--muted);
  display:flex;align-items:center;gap:6px;flex-wrap:wrap}
.res .mini{display:inline-flex;height:6px;width:104px;border-radius:4px;overflow:hidden;background:var(--surface2)}
.reveal{opacity:0;transform:translateY(10px);animation:rise .5s forwards}
@keyframes rise{to{opacity:1;transform:none}}
@media(prefers-reduced-motion:reduce){.reveal{animation:none;opacity:1;transform:none}
  .card,.card .detail{transition:none}}
</style>
</head>
<body>
<div class="wrap">

<header>
  <div class="eyebrow reveal">Transparent prediction model</div>
  <h1 class="reveal" style="animation-delay:.04s">World Cup <span class="yr">2026</span></h1>
  <p class="lede reveal" style="animation-delay:.08s">Match odds built from an open Elo rating of team quality, with a small,
  declared adjustment for venue heat and altitude. Calibrated against the market, not a claim to beat it.</p>
  <div class="chips reveal" style="animation-delay:.12s">
    <div class="stat"><b class="num" id="s-teams">0</b><span>teams</span></div>
    <div class="stat"><b class="num" id="s-fix">0</b><span>group matches scored</span></div>
    <div class="stat"><b class="num" id="s-ven">0</b><span>venues modelled</span></div>
    <div class="stat"><b class="num">Elo+&deg;</b><span>quality plus climate</span></div>
  </div>
</header>

<section class="sec">
  <div class="sec-h"><h2>Model scorecard</h2><span class="meta">graded automatically as matches are played</span></div>
  <div class="scorecard">
    <div class="metric"><b class="num" id="m-n">0</b><span>matches graded</span></div>
    <div class="metric"><b class="num" id="m-hit">&ndash;</b><span>favourite correct</span><small>top pick lands</small></div>
    <div class="metric"><b class="num" id="m-brier">&ndash;</b><span>Brier score</span><small>lower is better</small></div>
    <div class="metric"><b class="num" id="m-ll">&ndash;</b><span>log loss</span><small>lower is better</small></div>
  </div>
  <p class="sc-note">Every played match is scored against the prediction the model would have made using only the data available beforehand, a true walk-forward record. A coin-flip baseline scores about 0.67 Brier and 1.10 log loss, so lower is genuine skill. Early on the sample is small and these swing game to game; they settle as more matches play. The bookmaker line is the bar that matters.</p>
  <div style="display:flex;gap:8px;margin-top:10px;flex-wrap:wrap">
    <button class="filt" id="exp">Export results</button>
    <label class="filt" style="cursor:pointer">Import results<input id="imp" type="file" accept="application/json" hidden></label>
  </div>
</section>

<section class="sec">
  <div class="sec-h"><h2>Track record</h2><span class="meta" id="res-meta"></span></div>
  <div class="res-list" id="results"></div>
  <p class="sc-note" style="margin-top:12px">Every played match with the model's pre-match call and the actual result. A miss is when the model's most likely outcome did not happen. The percentage is what the model gave the outcome that actually occurred; the honest test is whether those stay sensible, not whether every favourite wins.</p>
</section>

<section class="sec">
  <div class="sec-h"><h2>Match predictions</h2><span class="meta" id="fix-count"></span></div>
  <div class="controls" id="day-filters"></div>
  <div class="grid" id="fixtures"></div>
</section>

<section class="sec">
  <div class="sec-h"><h2>Tournament projection</h2><span class="meta" id="tour-meta"></span></div>
  <table class="proj-tbl"><thead><tr>
    <th></th><th>Team</th><th>R16</th><th>QF</th><th>SF</th><th>Final</th><th>Win</th>
  </tr></thead><tbody id="tour-body"></tbody></table>
  <div class="bracket" id="bracket"></div>
  <p class="sc-note" style="margin-top:14px">Ten thousand simulations on FIFA's official bracket: real groups, the round-of-32 slot map, venue heat and altitude in the knockouts, and host advantage. The projected bracket shows the favourite path; trust the distribution above it, not the single line. As you enter group results, re-run the simulation and these sharpen.</p>
</section>

<section class="sec">
  <div class="sec-h"><h2>Team strength</h2><span class="meta">Elo from results since 2002</span></div>
  <table class="tbl"><thead><tr>
    <th data-k="rank">#</th><th data-k="team">Team</th>
    <th data-k="elo" class="r">Elo</th>
    <th data-k="base_c" class="r">Home heat</th>
    <th data-k="base_m" class="r">Home alt</th>
  </tr></thead><tbody id="team-body"></tbody></table>
</section>

<section class="sec">
  <div class="sec-h"><h2>Venue conditions</h2><span class="meta">heat after roof and AC</span></div>
  <div class="vgrid" id="venues"></div>
</section>

<footer>
  <p><b>How it reads.</b> Quality decides every match: the Elo gap sets the base odds. Heat and altitude
  move the line only at the margin, worth at most a few percentage points, and are switched off entirely in
  air-conditioned roofed stadiums. Head to head is deliberately excluded; for national teams the samples are
  tiny and stale.</p>
  <p style="margin-top:10px"><b>Data.</b> International results 1872 to date (open, CC0). Climate baselines from
  June and July city normals; live match-day weather plugs in via Open-Meteo. Strength is a quick transparent Elo,
  not the bookmaker line, which remains the benchmark. Not affiliated with or endorsed by FIFA.</p>
</footer>
</div>

<script>
const DATA = __DATA__;
const TOUR = __TOUR__;
const GRADED = __GRADED__;

let RESULTS = {};
try { const s = localStorage.getItem('wc26_results'); if(s) RESULTS = JSON.parse(s); } catch(e) {}
function persist(){ try { localStorage.setItem('wc26_results', JSON.stringify(RESULTS)); } catch(e) {} }
const resKey=f=>`${f.date}|${f.home}|${f.away}`;
function getResult(f){ const v=RESULTS[resKey(f)]; return v?{hs:v[0],as:v[1]}:null; }
function setResult(f,hs,as){ RESULTS[resKey(f)]=[hs,as]; persist(); }
function delResult(f){ delete RESULTS[resKey(f)]; persist(); }
function outcome(hs,as){return hs>as?'home':hs<as?'away':'draw';}
function bestOutcome(f){const a=[['home',f.p_home],['draw',f.p_draw],['away',f.p_away]];a.sort((x,y)=>y[1]-x[1]);return a[0][0];}

function exportResults(){
  const blob=new Blob([JSON.stringify(RESULTS,null,1)],{type:'application/json'});
  const a=document.createElement('a'); a.href=URL.createObjectURL(blob);
  a.download='wc2026_results.json'; document.body.appendChild(a); a.click(); a.remove();
}
function importResults(file){
  const r=new FileReader();
  r.onload=()=>{ try{ RESULTS=JSON.parse(r.result); persist(); renderFixtures(); }
    catch(e){ alert('Could not read that results file.'); } };
  r.readAsText(file);
}

const heatTag = f => {
  if(f.controlled) return '<span class="tag t-indoor">indoor AC</span>';
  if(f.heat==='high') return '<span class="tag t-hot">'+f.heat+' heat</span>';
  if(f.heat==='moderate') return '<span class="tag t-warm">'+f.heat+' heat</span>';
  return '<span class="tag t-cool">'+f.heat+' heat</span>';
};
const altTag = f => f.altitude_flag==='high' ? '<span class="tag t-alt">altitude</span>'
  : f.altitude_flag==='moderate' ? '<span class="tag t-alt">mild alt</span>' : '';
const fmtDate = d => new Date(d+'T00:00:00').toLocaleDateString('en-GB',{day:'numeric',month:'short'});
const pct = x => Math.round(x*100);

let showClimate = true;
let activeDay = 'all';

function scoreBlock(f){
  const r=getResult(f);
  if(r){
    const o=outcome(r.hs,r.as);
    const mp=o==='home'?f.p_home:o==='away'?f.p_away:f.p_draw;
    const ok=bestOutcome(f)===o;
    const oname=o==='home'?f.home:o==='away'?f.away:'the draw';
    return `<div class="result" onclick="event.stopPropagation()">
      <span class="fin">${r.hs}\u2013${r.as}</span>
      <span class="${ok?'ok':'no'}">${ok?'\u2713 model called it':'\u2717 model missed'}</span>
      <span class="mp">gave ${oname} ${Math.round(mp*100)}%</span>
      <button class="clr">clear</button></div>`;
  }
  return `<div class="score" onclick="event.stopPropagation()">
    <label>Final score</label>
    <input type="number" min="0" inputmode="numeric" data-h placeholder="0">
    <span class="mp" style="color:var(--faint)">\u2013</span>
    <input type="number" min="0" inputmode="numeric" data-a placeholder="0">
    <button class="sv">save</button></div>`;
}

function card(f,i){
  const homeFav = f.favourite===f.home;
  const ph=pct(f.p_home), pd=pct(f.p_draw), pa=pct(f.p_away);
  const swing = Math.round((f.p_home - f.p_home_base)*100);
  const swingTxt = swing===0 ? 'no swing' : (swing>0?'+':'')+swing+' pts to '+f.home;
  return `<div class="card reveal ${getResult(f)?'done':''}" data-key="${resKey(f)}" style="animation-delay:${Math.min(i*0.02,0.4)}s">
    <div class="card-top">
      <span class="date">${fmtDate(f.date)}</span><span class="dot"></span>
      <span class="place">${f.venue}, ${f.city}</span>
      <span class="cond">${altTag(f)}${heatTag(f)}</span>
    </div>
    <div class="teams">
      <div class="side"><div class="tname ${homeFav?'fav':''}">${f.home}</div>
        <div class="telo num">${f.elo_home} Elo${f.neutral?'':' &middot; home'}</div>
        ${f.home_star?`<div class="star">${f.home_star}</div>`:''}</div>
      <div class="vs">v</div>
      <div class="side away"><div class="tname ${!homeFav?'fav':''}">${f.away}</div>
        <div class="telo num">${f.elo_away} Elo</div>
        ${f.away_star?`<div class="star">${f.away_star}</div>`:''}</div>
    </div>
    <div class="bar">
      <span class="seg-h" style="width:${ph}%"></span>
      <span class="seg-d" style="width:${pd}%"></span>
      <span class="seg-a" style="width:${pa}%"></span>
    </div>
    <div class="pcts"><span class="ph num">${ph}%</span><span class="pd num">${pd}% draw</span><span class="pa num">${pa}%</span></div>
    <div class="read">${f.read}</div>
    <div class="detail"><div class="detail-in">
      <div class="row"><span>Quality only (Elo)</span><b>${pct(f.p_home_base)}% / ${pct(f.p_away_base)}%</b></div>
      <div class="row"><span>Climate adjustment</span><b>${f.climate_elo>0?'+':''}${f.climate_elo} Elo to ${f.home}</b></div>
      <div class="row"><span>Net effect</span><b class="swing ${swing>=0?'pos':'neg'}">${swingTxt}</b></div>
    </div></div>
    ${scoreBlock(f)}
  </div>`;
}

function renderScorecard(){
  let n=0,hits=0,brier=0,ll=0;
  (GRADED.graded||[]).forEach(g=>{
    n++; const o=g.outcome;
    const best=[['home',g.p_home],['draw',g.p_draw],['away',g.p_away]].sort((x,y)=>y[1]-x[1])[0][0];
    if(best===o)hits++;
    const yh=o==='home'?1:0,yd=o==='draw'?1:0,ya=o==='away'?1:0;
    brier+=(g.p_home-yh)**2+(g.p_draw-yd)**2+(g.p_away-ya)**2;
    ll+=-Math.log(Math.max(g['p_'+o],1e-6));
  });
  document.getElementById('m-n').textContent=n;
  document.getElementById('m-hit').textContent=n?Math.round(hits/n*100)+'%':'\u2013';
  document.getElementById('m-brier').textContent=n?(brier/n).toFixed(3):'\u2013';
  document.getElementById('m-ll').textContent=n?(ll/n).toFixed(3):'\u2013';
}

function renderResults(){
  const g=[...(GRADED.graded||[])].sort((a,b)=> a.date<b.date?1:a.date>b.date?-1:0);
  const meta=document.getElementById('res-meta');
  if(!g.length){ meta.textContent='none yet';
    document.getElementById('results').innerHTML='<p class="sc-note">No matches played yet. The track record fills in as games are played.</p>'; return; }
  const hitN=g.filter(m=>{const b=[['home',m.p_home],['draw',m.p_draw],['away',m.p_away]].sort((x,y)=>y[1]-x[1])[0][0];return b===m.outcome;}).length;
  meta.textContent=`${g.length} played \u00b7 ${hitN} called`;
  document.getElementById('results').innerHTML=g.map(m=>{
    const arr=[['home',m.p_home],['draw',m.p_draw],['away',m.p_away]].sort((x,y)=>y[1]-x[1]);
    const best=arr[0][0]; const hit=best===m.outcome;
    const pick=best==='home'?m.home:best==='away'?m.away:'a draw';
    const oname=m.outcome==='home'?m.home:m.outcome==='away'?m.away:'the draw';
    const ph=Math.round(m.p_home*100),pd=Math.round(m.p_draw*100),pa=Math.round(m.p_away*100);
    return `<div class="res ${hit?'':'miss'}">
      <div class="rm"><span class="rd">${fmtDate(m.date)}</span>
        <span class="rt">${m.home}<span class="rs">${m.hs}\u2013${m.as}</span>${m.away}</span></div>
      <span class="badge ${hit?'ok':'no'}">${hit?'\u2713 called':'\u2717 missed'}</span>
      <div class="rp">said <b style="color:var(--text)">${pick} ${Math.round(arr[0][1]*100)}%</b>
        <span class="mini"><span class="seg-h" style="width:${ph}%"></span><span class="seg-d" style="width:${pd}%"></span><span class="seg-a" style="width:${pa}%"></span></span>
        gave ${oname} ${Math.round(m['p_'+m.outcome]*100)}%</div>
    </div>`;
  }).join('');
}

function renderFixtures(){
  const list = DATA.fixtures.filter(f=>activeDay==='all'||f.date===activeDay);
  document.getElementById('fixtures').innerHTML = list.map(card).join('');
  document.getElementById('fix-count').textContent = list.length+' shown';
  document.querySelectorAll('#fixtures .card').forEach(c=>c.onclick=e=>{
    if(e.target.closest('.score,.result')) return;
    c.classList.toggle('open');
  });
  document.querySelectorAll('#fixtures .sv').forEach(b=>b.onclick=e=>{
    e.stopPropagation();
    const c=b.closest('.card'); const f=DATA.fixtures.find(x=>resKey(x)===c.dataset.key);
    const hs=parseInt(c.querySelector('[data-h]').value);
    const as=parseInt(c.querySelector('[data-a]').value);
    if(Number.isNaN(hs)||Number.isNaN(as)) return;
    setResult(f,hs,as); renderFixtures();
  });
  document.querySelectorAll('#fixtures .clr').forEach(b=>b.onclick=e=>{
    e.stopPropagation();
    const f=DATA.fixtures.find(x=>resKey(x)===b.closest('.card').dataset.key);
    delResult(f); renderFixtures();
  });
  renderScorecard();
}

function renderDays(){
  const days=['all',...[...new Set(DATA.fixtures.map(f=>f.date))].sort()];
  document.getElementById('day-filters').innerHTML = days.map(d=>
    `<button class="filt ${d===activeDay?'on':''}" data-d="${d}">${d==='all'?'All days':fmtDate(d)}</button>`).join('');
  document.querySelectorAll('#day-filters .filt').forEach(b=>b.onclick=()=>{
    activeDay=b.dataset.d; renderDays(); renderFixtures();
  });
}

let sortK='elo', sortDir=-1;
function renderTeams(){
  const t=[...DATA.teams].sort((a,b)=>{
    const v = a[sortK]>b[sortK]?1:a[sortK]<b[sortK]?-1:0; return v*sortDir;});
  document.getElementById('team-body').innerHTML = t.map(x=>`<tr>
    <td class="rk">${x.rank}</td>
    <td class="tm">${x.team} <span class="mini">${x.hemisphere==='S'?'S':''}</span></td>
    <td class="r elo">${x.elo}</td>
    <td class="r">${x.base_c}&deg;C</td>
    <td class="r">${x.base_m>=1000?(x.base_m+' m'):'\u2013'}</td></tr>`).join('');
}
document.querySelectorAll('.tbl th').forEach(th=>th.onclick=()=>{
  const k=th.dataset.k; sortDir = (k===sortK)? -sortDir : (k==='team'?1:-1); sortK=k; renderTeams();
});

function renderVenues(){
  const heatColor = v => v.controlled?'t-indoor':v.heat==='high'?'t-hot':v.heat==='moderate'?'t-warm':'t-cool';
  document.getElementById('venues').innerHTML = DATA.venues.map(v=>`<div class="vrow">
    <div class="vc"><div class="vn">${v.city}</div><div class="vm">${v.name}</div></div>
    <div class="vt">${v.controlled?'AC':v.high_c+'\u00b0'}${v.altitude_flag==='high'?' &middot; '+v.elev_m+'m':''}</div>
    <span class="tag ${heatColor(v)}">${v.controlled?'indoor':v.heat}</span>
  </div>`).join('');
}

function renderTour(){
  document.getElementById('tour-meta').textContent = TOUR.n.toLocaleString()+' simulations';
  const max = TOUR.probs[0].W || 1;
  document.getElementById('tour-body').innerHTML = TOUR.probs.slice(0,16).map((p,i)=>`<tr>
    <td class="rk">${i+1}</td><td class="tm">${p.team}</td>
    <td>${Math.round(p.R16*100)}%</td><td>${Math.round(p.QF*100)}%</td>
    <td>${Math.round(p.SF*100)}%</td><td>${Math.round(p.F*100)}%</td>
    <td><span class="wv">${(p.W*100).toFixed(1)}%</span><span class="winbar" style="width:${Math.round(p.W/max*40)}px"></span></td>
  </tr>`).join('');
  const b=TOUR.bracket, short=v=>v.replace('Stadium','').replace('Estadio ','').trim().split(' ')[0];
  const mtch=m=>`<div class="bmatch">
    <div class="bt ${m.fav===m.home?'win':''}">${m.home}</div>
    <div class="bt ${m.fav===m.away?'win':''}">${m.away}<span class="bv">${short(m.venue)}</span></div></div>`;
  const col=(t,a)=>`<div class="bcol"><h4>${t}</h4>${a.map(mtch).join('')}</div>`;
  document.getElementById('bracket').innerHTML =
    col('Quarterfinals',b.QF)+col('Semifinals',b.SF)+
    `<div class="bcol"><h4>Final</h4>${mtch(b.Final[0])}
     <div class="champ"><div class="cl">Projected winner</div><div class="cn">${b.winner}</div></div></div>`;
}

document.getElementById('s-teams').textContent=DATA.n_teams;
document.getElementById('s-fix').textContent=DATA.n_fixtures;
document.getElementById('s-ven').textContent=DATA.n_venues;
document.getElementById('exp').onclick=exportResults;
document.getElementById('imp').onchange=e=>{ if(e.target.files[0]) importResults(e.target.files[0]); };
renderDays(); renderFixtures(); renderResults(); renderTeams(); renderVenues(); renderTour();
</script>
</body>
</html>"""

tour = json.load(open("tournament.json"))
try: graded = json.load(open("graded.json"))
except FileNotFoundError: graded = {"n": 0, "graded": []}
html = (TEMPLATE.replace("__DATA__", json.dumps(data))
                .replace("__TOUR__", json.dumps(tour))
                .replace("__GRADED__", json.dumps(graded)))
open("index.html", "w").write(html)
print("index.html written:", len(html), "bytes")
