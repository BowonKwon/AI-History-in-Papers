"""Build the static site (ko/en) into site/ from data/derived/*.csv and src/content.py.

  python src/build_site.py

Inputs
  data/derived/papers.csv      one row per selected paper (see method/data-schema.md)
  data/derived/edges.csv       src,dst,kind (OA | original | notion), evidence
  data/derived/awards.csv      year,award,laureates,named_key,note
  data/derived/winter_*.csv    title-phrase counts, attendance, NeurIPS accepted
  src/content.py               chapter narratives, boxes, method text (ko/en)
No external JS/CSS libraries; charts are SVG written here; a small vanilla script adds the theme toggle,
table sort/filter, timeline popovers and lineage highlighting.
"""
import csv, html, json, math, re, shutil, sys
from collections import defaultdict
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import content as C  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / "data/derived"
SITE = ROOT / "site"
VERSION = "1.1.7"
BUILD_DATE = date.today().isoformat()
REPO = "https://github.com/BowonKwon/AI-History-in-Papers"
import site_nav  # 1.1.7: section ids, section lists, a chapter list on the era pages, full contents on the Eras page

ERAS = ["E1", "E2", "E3", "E4", "E5", "E6", "E7"]
THEMES = ["FOUND", "SYM", "KR", "SEARCH", "EXP", "NN", "VISION", "SPEECH", "LANG", "STAT", "THEORY", "RL", "GEN", "SCALE", "ALIGN", "SAFETY", "AGENT", "HW", "DATA", "SCI", "CYB", "PERC", "EVO", "ROBOT", "IR"]
# lineage pages group themes into lanes
LANES = [("neural", ["NN", "THEORY", "HW"]), ("rl", ["RL"]), ("lang", ["LANG", "SPEECH", "IR"]), ("vision", ["VISION", "GEN", "DATA"]),
         ("search", ["SEARCH", "SYM", "KR", "EXP", "ROBOT"]), ("stat", ["STAT", "CYB", "FOUND", "PERC", "EVO", "SCI"]), ("align", ["ALIGN", "SAFETY", "SCALE"]), ("agent", ["AGENT"])]
LANE_OF = {t: lane for lane, ts in LANES for t in ts}

T = {
    "ko": dict(site="논문으로 읽는 인공지능의 역사", lang_other="English", tagline="1943년부터 지금까지, 원 논문으로 따라가는 인공지능 연구의 역사",
               nav_home="홈", nav_chapters="시대", nav_lineage="계보", nav_winters="겨울과 붐", nav_papers="논문 목록", nav_method="방법·한계",
               key="핵심", version="판", built="생성일", hub="공개 자료 전체", first_public="첫 공개", venue="게재", pages="쪽", original="원문",
               quote="원문에서", what_changed="무엇을 바꿨나", cites="이 목록의 논문 중 인용한 것", cited_by="이 목록의 논문 중 이 논문을 인용한 것",
               oa_cited="피인용(OpenAlex)", checked="조회", none="없음", edge_oa="OpenAlex 인용 확인", edge_orig="원문 참고문헌 확인", edge_notion="통념(인용 미확인)",
               download="CSV 내려받기", filter="찾기", year="연도", author="첫 저자", title="제목", chapter="장", theme="주제", papers="편",
               timeline_cap="점 하나가 논문 한 편이다. 가로축은 첫 공개 연도(2012년을 경계로 앞 70년과 뒤 14년이 비슷한 너비를 차지한다), 세로줄은 주제 묶음. 점 위에 마우스를 올리면 카드가 뜬다.",
               hub_link="공개 자료 허브", axis_year="첫 공개 연도", axis_rows="주제 묶음",
               cap_dot="점 하나가 논문 한 편이다. 가로축은 첫 공개 연도다.",
               cap_rows_multi="세로줄은 주제 묶음이다. 한 줄 안의 위아래 위치에는 뜻이 없다(첫 공개 시점을 반년 단위로 반올림한 값이 같은 논문을 덜 겹치게 엇갈려 놓았을 뿐이다).",
               cap_rows_single="이 그림에는 주제 묶음이 하나뿐이라 줄도 하나다. 위아래 위치에는 뜻이 없다(시간 순서대로 여섯 높이를 돌아가며 놓아 점과 선이 덜 겹치게 했을 뿐이다).",
               cap_lines="선 하나는 확인된 인용 하나다(OpenAlex 또는 인용한 논문의 참고문헌 목록에서 확인). 선은 인용된 논문과 인용한 논문을 잇고, 대개 왼쪽 끝이 먼저 나온 인용된 논문이다.",
               cap_notion="점선은 교과서가 말하는 영향이지만 인용이 확인되지 않은 선이다.",
               cap_hover="점에 마우스를 올리면 그 논문의 카드가 뜨고 그 논문에 이어진 선만 진하게 남는다(나머지 선은 흐려진다). 점을 누르면 그 논문의 카드로 간다.",
               cap_scope_era="조심할 것: 선은 이 장의 논문끼리만 그었다. 다른 장 논문과의 인용은 아래 논문 카드의 「이 목록의 논문 중 인용한 것」에 있다. 선은 확인된 인용을 나타낼 뿐 영향의 크기를 재지 않는다.",
               cap_scope_lane="조심할 것: 선은 이 묶음의 논문끼리만 그었다. 다른 묶음 논문과의 인용은 장 면의 논문 카드에 있다. 선은 확인된 인용을 나타낼 뿐 영향의 크기를 재지 않는다.",
               rows_gloss="줄(주제 묶음) 이름 풀이",
               theme_names={"neural": "신경망 학습", "rl": "강화학습·게임", "lang": "언어·음성", "vision": "시각·생성", "search": "탐색·계획·지식", "stat": "확률·통계·기원", "align": "규모·정렬·안전", "agent": "에이전트"}),
    "en": dict(site="AI History in Papers", lang_other="한국어", tagline="The history of AI research from 1943 to today, followed through its original papers",
               nav_home="Home", nav_chapters="Eras", nav_lineage="Lineage", nav_winters="Winters and booms", nav_papers="Paper list", nav_method="Method and limits",
               key="Key point", version="Version", built="Built", hub="All public materials", first_public="First public", venue="Venue", pages="Pages", original="Original",
               quote="From the paper", what_changed="What changed", cites="Cites (within this list)", cited_by="Cited by (within this list)",
               oa_cited="Citations (OpenAlex)", checked="checked", none="none", edge_oa="Citation confirmed in OpenAlex", edge_orig="Citation confirmed in the paper's reference list", edge_notion="Textbook attribution, citation not confirmed",
               download="Download CSV", filter="Filter", year="Year", author="First author", title="Title", chapter="Era", theme="Theme", papers="papers",
               timeline_cap="One dot per paper. Horizontal position is the first public year (the axis gives the 70 years before 2012 and the 14 years after it similar widths); rows are theme groups. Hover a dot for its card.",
               hub_link="All public materials", axis_year="First public year", axis_rows="Theme group",
               cap_dot="One dot per paper. The horizontal axis is the first public year.",
               cap_rows_multi="Rows are theme groups. The up-and-down position within a row means nothing: papers whose first public dates round to the same half-year step are staggered so that they overlap less.",
               cap_rows_single="This diagram has a single theme group, so there is one row. The up-and-down position means nothing: in time order, papers take six heights in turn so that dots and lines overlap less.",
               cap_lines="Each line is one confirmed citation (OpenAlex or the citing paper's own reference list). A line joins a cited paper and the paper citing it; usually the left end is the cited, earlier paper.",
               cap_notion="Dotted lines are influences stated in textbooks without a confirmed citation.",
               cap_hover="Hover over a dot to see its card; only the lines joined to that paper stay dark and the rest fade. Click a dot to go to its card.",
               cap_scope_era="Caution: lines are drawn only between papers of this era. Citations to papers of other eras are listed on the cards below, under “Cites (within this list)”. A line shows a confirmed citation; it does not measure how much influence there was.",
               cap_scope_lane="Caution: lines are drawn only between papers of this theme group. Citations to papers of other groups are listed on the cards in the era pages. A line shows a confirmed citation; it does not measure how much influence there was.",
               rows_gloss="What the row (theme group) names cover",
               theme_names={"neural": "Neural network learning", "rl": "Reinforcement learning and games", "lang": "Language and speech", "vision": "Vision and generative models", "search": "Search, planning and knowledge", "stat": "Probability, statistics and origins", "align": "Scale, alignment and safety", "agent": "Agents"}),
}

CSS = """
:root{color-scheme:light;--bg:#f8f7f4;--bg2:#efede8;--card:#ffffff;--line:#dedbd3;--line2:#ebe8e1;--fg:#1d1f24;--fg2:#5a5e68;--fg3:#8a8e98;
  --accent:#3f6a9e;--accent2:#b5833f;--s1:#3a6fb0;--s2:#b5833f;--s3:#7f63ad;--s4:#4f8a6b;--grid:#e6e3dc;
  --shadow:0 1px 2px rgba(30,32,40,.05),0 6px 18px rgba(30,32,40,.05);
  --display:"Noto Serif KR","Source Serif 4",Georgia,"Times New Roman",serif;--body:"Noto Sans KR",-apple-system,"Segoe UI","Apple SD Gothic Neo",Roboto,sans-serif}
@media(prefers-color-scheme:dark){:root:not([data-theme="light"]){color-scheme:dark;--bg:#1b1c1f;--bg2:#222326;--card:#232428;--line:#34363c;--line2:#2b2d32;--fg:#ebe9e4;--fg2:#b3b1aa;--fg3:#80827f;--accent:#7ea4d6;--accent2:#d1a35f;--s1:#5a8ccf;--s2:#b5863a;--s3:#9078c4;--s4:#5f9f7d;--grid:#2e3035;--shadow:0 1px 2px rgba(0,0,0,.3),0 8px 20px rgba(0,0,0,.25)}}
:root[data-theme="dark"]{color-scheme:dark;--bg:#1b1c1f;--bg2:#222326;--card:#232428;--line:#34363c;--line2:#2b2d32;--fg:#ebe9e4;--fg2:#b3b1aa;--fg3:#80827f;--accent:#7ea4d6;--accent2:#d1a35f;--s1:#5a8ccf;--s2:#b5863a;--s3:#9078c4;--s4:#5f9f7d;--grid:#2e3035;--shadow:0 1px 2px rgba(0,0,0,.3),0 8px 20px rgba(0,0,0,.25)}
*{box-sizing:border-box}html,body{max-width:100%;overflow-x:hidden}
body{margin:0;font:16px/1.7 var(--body);background:var(--bg);color:var(--fg);overflow-wrap:anywhere;-webkit-font-smoothing:antialiased}
a{color:var(--accent);text-decoration:none}a:hover{text-decoration:underline;text-underline-offset:3px}:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
header{position:sticky;top:0;z-index:5;background:color-mix(in srgb,var(--bg) 88%,transparent);backdrop-filter:blur(8px);border-bottom:1px solid var(--line);padding:.55rem 1.1rem;display:flex;gap:1.4rem;align-items:center;flex-wrap:wrap}
header .brand{font-family:var(--display);font-weight:600;font-size:1.05rem;color:var(--fg);letter-spacing:-.01em}
header nav{display:flex;gap:1rem;flex-wrap:wrap}header nav a{color:var(--fg2);font-size:.92rem;padding:.2rem 0;border-bottom:2px solid transparent}
header nav a:hover{text-decoration:none;color:var(--fg)}header nav a.on{color:var(--fg);border-bottom-color:var(--accent2)}
header .right{margin-left:auto;display:flex;gap:.6rem;align-items:center}
header .hub{display:inline-flex;align-items:center;gap:.42rem;height:30px;padding:0 .8rem;border:1px solid var(--line);border-radius:999px;background:var(--card);color:var(--fg);font-size:.84rem;font-weight:600;white-space:nowrap;text-decoration:none;transition:border-color .15s,color .15s,background .15s}header .hub::before{content:"";width:.72em;height:.72em;flex:none;background:linear-gradient(var(--accent),var(--accent)) 0 0/42% 42% no-repeat,linear-gradient(var(--accent),var(--accent)) 100% 0/42% 42% no-repeat,linear-gradient(var(--accent),var(--accent)) 0 100%/42% 42% no-repeat,linear-gradient(var(--accent),var(--accent)) 100% 100%/42% 42% no-repeat}header .hub:hover{border-color:var(--accent);color:var(--accent);background:var(--bg2)}
header .lang{font-size:.88rem;color:var(--fg2);border:1px solid var(--line);border-radius:999px;padding:.15rem .7rem}header .lang:hover{text-decoration:none;color:var(--fg);border-color:var(--fg3)}
.theme{border:1px solid var(--line);background:transparent;color:var(--fg2);border-radius:999px;width:30px;height:30px;cursor:pointer;font-size:.9rem;line-height:1;padding:0}.theme:hover{color:var(--fg);border-color:var(--fg3)}
main{max-width:1060px;margin:0 auto;padding:1.6rem 1.1rem 4rem;min-width:0}
h1{font-family:var(--display);font-weight:600;font-size:clamp(1.6rem,3.2vw,2.2rem);line-height:1.25;letter-spacing:-.015em;margin:.3rem 0 .5rem;text-wrap:balance}
h2{font-family:var(--display);font-weight:600;font-size:1.3rem;line-height:1.3;margin:2.4rem 0 .8rem;padding-bottom:.35rem;border-bottom:1px solid var(--line);text-wrap:balance}
h3{font-size:1.02rem;margin:1.4rem 0 .4rem}
.eyebrow{display:flex;gap:.5rem;flex-wrap:wrap;margin-bottom:.4rem}
.tag{display:inline-block;font-size:.74rem;letter-spacing:.04em;padding:.1rem .55rem;border-radius:999px;color:var(--fg2);background:var(--bg2);border:1px solid var(--line2)}
.lead{color:var(--fg2);font-size:1.05rem;max-width:70ch;margin:0 0 1.2rem}
.hero{padding:.6rem 0 1.4rem;border-bottom:1px solid var(--line);margin-bottom:1.4rem}.hero h1{font-size:clamp(1.9rem,4vw,2.7rem)}.hero .lead{font-size:1.12rem}
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(235px,1fr));gap:.8rem;margin:.9rem 0 1.4rem}
.card{display:block;background:var(--card);border:1px solid var(--line);border-radius:10px;padding:.85rem 1rem .9rem;box-shadow:var(--shadow);color:var(--fg);transition:transform .15s,border-color .15s}
a.card:hover{text-decoration:none;transform:translateY(-2px);border-color:var(--fg3)}
.card b{display:block;margin-bottom:.25rem;font-size:.98rem;color:var(--accent)}.card small{color:var(--fg2);font-size:.86rem;line-height:1.5;display:block}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(175px,1fr));gap:.8rem;margin:1.2rem 0 1.6rem}
.stat{display:block;background:var(--card);border:1px solid var(--line);border-radius:10px;padding:1rem 1.1rem;box-shadow:var(--shadow);color:var(--fg)}
.stat .n{font-family:var(--display);font-size:2rem;font-weight:600;line-height:1.1;letter-spacing:-.02em;font-variant-numeric:tabular-nums}.stat small{display:block;color:var(--fg2);margin-top:.35rem;font-size:.86rem;line-height:1.45}
:lang(ko) p,:lang(ko) li,:lang(ko) .lead,:lang(ko) .glance dd,:lang(ko) .card small,:lang(ko) figcaption,:lang(ko) .paper,:lang(ko) .box{word-break:keep-all;overflow-wrap:anywhere}
.glance{border-left:4px solid var(--accent);background:var(--bg2);border-radius:0 10px 10px 0;padding:.8rem 1.1rem;margin:.6rem 0 1.1rem;max-width:78ch}.glance-h{margin:0 0 .4rem;font-size:.82rem;font-weight:600;letter-spacing:.04em;color:var(--fg2)}.glance ul{margin:0;padding-left:1.1rem}.glance li{margin:.2rem 0}
.box{background:color-mix(in srgb,var(--accent2) 8%,var(--card));border:1px solid color-mix(in srgb,var(--accent2) 30%,var(--line));border-left:4px solid var(--accent2);border-radius:8px;padding:.8rem 1.1rem;margin:1.4rem 0;font-size:.95rem;max-width:78ch}.box h3{margin:.1rem 0 .5rem;font-size:.98rem}
.box table{font-size:.88rem}.box .wrap{background:transparent;border:none;padding:0;margin:.4rem 0}.box .wrap p{margin:.6rem 0}.box thead th{white-space:normal}
.paper{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:1rem 1.2rem;margin:1rem 0;box-shadow:var(--shadow);scroll-margin-top:4rem}
.paper h3{margin:0 0 .25rem;font-size:1.05rem;font-family:var(--display)}.paper .meta{color:var(--fg2);font-size:.88rem;margin:0 0 .5rem}.paper .meta a{margin-right:.6rem}
.paper blockquote{margin:.6rem 0;padding:.5rem .9rem;border-left:3px solid var(--accent2);background:var(--bg2);border-radius:0 8px 8px 0;font-size:.93rem;color:var(--fg)}.paper blockquote cite{display:block;color:var(--fg3);font-size:.8rem;font-style:normal;margin-top:.2rem}
.paper .wc{margin:.4rem 0}.paper .rel{font-size:.84rem;color:var(--fg2);margin-top:.5rem}.paper .rel a{margin-right:.5rem}
dl{display:grid;grid-template-columns:max-content 1fr;gap:.55rem 1.4rem;margin:0}dt{color:var(--fg3);font-size:.82rem;letter-spacing:.04em;text-transform:uppercase;padding-top:.15rem}dd{margin:0;min-width:0}
@media(max-width:640px){dl{grid-template-columns:1fr}dt{margin-top:.5rem}}
table{border-collapse:collapse;width:100%;font-size:.9rem;margin:.6rem 0}th,td{border-bottom:1px solid var(--line2);padding:.42rem .6rem;text-align:left;vertical-align:top}
thead th{color:var(--fg2);font-weight:600;font-size:.82rem;letter-spacing:.02em;cursor:pointer;white-space:nowrap;border-bottom:1px solid var(--line)}thead th:hover{color:var(--fg)}
tbody tr:nth-child(even){background:color-mix(in srgb,var(--bg2) 55%,transparent)}tbody tr:hover{background:var(--bg2)}
td.num,th.num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}td.nw{white-space:nowrap}
.wrap{overflow-x:auto;border:1px solid var(--line);border-radius:10px;background:var(--card);padding:0 .3rem;margin:.6rem 0 1rem}.wrap table{margin:0}
figure{margin:1.2rem 0;background:var(--card);border:1px solid var(--line);border-radius:10px;padding:1rem 1rem .8rem;box-shadow:var(--shadow);min-width:0}figcaption{font-size:.86rem;color:var(--fg2);margin-top:.5rem;line-height:1.5}
figcaption p{margin:.35rem 0}figcaption details{margin:.35rem 0}figcaption summary{cursor:pointer}figcaption dl{grid-template-columns:max-content 1fr;gap:.2rem 1rem;margin:.3rem 0}figcaption dt{text-transform:none;letter-spacing:0;font-size:.84rem;color:var(--fg2)}
@media(max-width:640px){.sx{overflow-x:auto;-webkit-overflow-scrolling:touch}.sx>svg{min-width:calc(var(--vw)*1px);max-width:none}}
svg{max-width:100%;height:auto;display:block}svg text{font-family:var(--body);fill:var(--fg2);font-size:11px}svg .ax{stroke:var(--line)}svg .grid{stroke:var(--grid)}
svg .dot{cursor:pointer}svg .dot:hover circle,svg .dot.on circle{stroke:var(--fg);stroke-width:2}
svg .edge{fill:none;stroke:var(--fg3);stroke-width:1.1;opacity:.55}svg.dense .edge{opacity:.3}svg .edge.notion{stroke-dasharray:3 3;opacity:.5}svg .edge.late{stroke:var(--s4);stroke-width:2;opacity:.95}svg .edge.hi{stroke:var(--accent);stroke-width:2;opacity:1}svg .edge.late.hi{stroke:var(--s4);stroke-width:3}svg .edge.dim{opacity:.12}
svg .band{fill:var(--s1);opacity:.07}svg .band.alt{fill:var(--s2)}
.legend{display:flex;gap:1.1rem;font-size:.86rem;color:var(--fg2);flex-wrap:wrap;margin:.2rem 0 .4rem}.legend span::before{content:"";display:inline-block;width:11px;height:11px;border-radius:3px;margin-right:.4rem;vertical-align:-1px;background:var(--c)}.legend.lg-line span::before{width:20px;height:2px;border-radius:0;vertical-align:4px;opacity:.8}.legend.lg-line span.late::before{height:3px;opacity:1}
.pop{position:absolute;z-index:9;max-width:320px;background:var(--card);border:1px solid var(--line);border-radius:10px;box-shadow:var(--shadow);padding:.6rem .8rem;font-size:.85rem;line-height:1.45;pointer-events:none;display:none}.pop b{display:block;color:var(--accent)}
.note{background:color-mix(in srgb,var(--accent) 7%,var(--card));border:1px solid color-mix(in srgb,var(--accent) 25%,var(--line));border-left:4px solid var(--accent);border-radius:8px;padding:.7rem 1rem;margin:1.2rem 0;font-size:.95rem}
.prose p,.prose ul,.prose .note,.prose .lead{max-width:72ch}.prose p{margin:.8rem 0}.prose ul{padding-left:1.2rem}.prose li{margin:.3rem 0}
.src{color:var(--fg2);font-size:.92rem}.files a{display:inline-block;font-size:.85rem;background:var(--bg2);border:1px solid var(--line2);border-radius:6px;padding:.15rem .55rem;margin:.2rem .3rem .2rem 0;color:var(--fg2)}.files a:hover{color:var(--fg);text-decoration:none;border-color:var(--fg3)}
footer{border-top:1px solid var(--line);color:var(--fg3);font-size:.82rem;padding:1.2rem;text-align:center}
.filter{margin:.5rem 0}.filter input{padding:.4rem .7rem;border:1px solid var(--line);border-radius:8px;background:var(--card);color:var(--fg);width:min(100%,340px);font:inherit;font-size:.9rem}
.filter input:focus{border-color:var(--accent);outline:none;box-shadow:0 0 0 3px color-mix(in srgb,var(--accent) 20%,transparent)}
.eras{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:.8rem;margin:1rem 0}
@media(max-width:640px){.tl-wide{display:none}.tl-list{display:block}}@media(min-width:641px){.tl-list{display:none}}
@media(prefers-reduced-motion:reduce){.card,a.card:hover{transition:none;transform:none}}
"""

JS = r"""
(function(){var k="ahp-theme",r=document.documentElement,b=document.getElementById("theme");function ap(v){if(v)r.setAttribute("data-theme",v);else r.removeAttribute("data-theme");if(b)b.textContent=v==="dark"?"☾":v==="light"?"☀":"◑"}var cur=localStorage.getItem(k)||"";ap(cur);if(b)b.addEventListener("click",function(){cur=cur===""?"light":cur==="light"?"dark":"";if(cur)localStorage.setItem(k,cur);else localStorage.removeItem(k);ap(cur)})})();
document.querySelectorAll('table.sort').forEach(function(t){var ths=t.querySelectorAll('th');ths.forEach(function(th,i){th.addEventListener('click',function(){
 var rows=Array.from(t.tBodies[0].rows),asc=th.dataset.asc!=='1';th.dataset.asc=asc?'1':'0';
 rows.sort(function(a,b){var x=a.cells[i].dataset.v||a.cells[i].textContent,y=b.cells[i].dataset.v||b.cells[i].textContent;var nx=parseFloat(x),ny=parseFloat(y);if(!isNaN(nx)&&!isNaN(ny))return asc?nx-ny:ny-nx;return asc?x.localeCompare(y):y.localeCompare(x)});
 rows.forEach(function(r){t.tBodies[0].appendChild(r)})})})});
document.querySelectorAll('.filter input').forEach(function(inp){inp.addEventListener('input',function(){var q=inp.value.toLowerCase(),t=document.getElementById(inp.dataset.target);Array.from(t.tBodies[0].rows).forEach(function(r){r.style.display=r.textContent.toLowerCase().indexOf(q)>=0?'':'none'})})});
(function(){var pop=document.createElement('div');pop.className='pop';document.body.appendChild(pop);
 document.querySelectorAll('svg .dot').forEach(function(g){
  g.addEventListener('mouseenter',function(e){pop.innerHTML='<b>'+g.dataset.t+'</b>'+g.dataset.m+(g.dataset.w?'<br>'+g.dataset.w:'');pop.style.display='block';
   var svg=g.ownerSVGElement;svg.querySelectorAll('.edge').forEach(function(p){var on=p.dataset.s===g.dataset.k||p.dataset.d===g.dataset.k;p.classList.toggle('hi',on);p.classList.toggle('dim',!on)});g.classList.add('on')});
  g.addEventListener('mousemove',function(e){var x=e.pageX+14,y=e.pageY+14;if(x+330>window.scrollX+window.innerWidth)x=e.pageX-334;pop.style.left=x+'px';pop.style.top=y+'px'});
  g.addEventListener('mouseleave',function(){pop.style.display='none';var svg=g.ownerSVGElement;svg.querySelectorAll('.edge').forEach(function(p){p.classList.remove('hi');p.classList.remove('dim')});g.classList.remove('on')});
  g.addEventListener('click',function(){if(g.dataset.href)location.href=g.dataset.href})});
 var q=new URLSearchParams(location.search).get('theme');if(q==='light'||q==='dark'){localStorage.setItem('ahp-theme',q)}else if(q==='auto'){localStorage.removeItem('ahp-theme')}})();
"""


def esc(s):
    return html.escape("" if s is None else str(s))


def read_csv(name):
    p = D / name
    return list(csv.DictReader(open(p, encoding="utf-8-sig"))) if p.exists() else []


# ----------------------------------------------------------------- ko glossary
# 한국어로 옮긴 용어는 쪽마다 처음 나올 때 원어를 괄호로 붙인다(2026-11-08 — 「생각의 사슬」만
# 보고는 무엇인지 따로 떠올려야 한다). 사전은 method/glossary_ko.csv. 뜻이 갈리는 낱말(정렬·정규화 등)은
# 사전에 넣지 않고, 뜻이 하나로 정해지는 복합어나 문맥 구절만 넣는다. 태그 속성·svg·script·style·제목(h1–h3)은
# 건드리지 않는다. 바로 뒤에 괄호가 이미 있으면(「(2022년 1월)」「(RNN)」) 그 괄호 안 앞에 원어를 넣는다.
GLOSS = [(r["ko"], r["en"]) for r in csv.DictReader(open(ROOT / "method/glossary_ko.csv", encoding="utf-8"))] \
    if (ROOT / "method/glossary_ko.csv").exists() else []
GLOSS.sort(key=lambda kv: -len(kv[0]))
GLOSS_RE = re.compile("|".join(re.escape(k) for k, _ in GLOSS)) if GLOSS else None
GLOSS_EN = dict(GLOSS)
SKIP_TAGS = ("svg", "script", "style", "h1", "h2", "h3", "code")


def gloss_ko(body):
    if not GLOSS_RE:
        return body
    done = set()
    out, i, skip = [], 0, []
    for m in re.finditer(r"<[^>]+>", body):
        text = body[i:m.start()]
        out.append(text if skip else _gloss_text(text, done))
        tag = m.group(0)
        name = re.match(r"</?\s*([a-zA-Z0-9]+)", tag)
        if name:
            n = name.group(1).lower()
            if n == "span" and 'class="tag"' in tag:
                n = "span.tag"          # 장 머리의 장 이름 꼬리표
            elif n == "span" and tag.startswith("</") and skip and skip[-1] == "span.tag":
                n = "span.tag"
            if (n in SKIP_TAGS or n == "span.tag") and not tag.endswith("/>"):
                if tag.startswith("</"):
                    if skip and skip[-1] == n:
                        skip.pop()
                else:
                    skip.append(n)
        out.append(tag)
        i = m.end()
    out.append(_gloss_text(body[i:], done) if not skip else body[i:])
    return "".join(out)


def _gloss_text(text, done):
    out, i = [], 0
    for m in GLOSS_RE.finditer(text):
        ko = m.group(0)
        out.append(text[i:m.end()])
        i = m.end()
        if ko in done:
            continue
        done.add(ko)
        en = GLOSS_EN[ko]
        if text.startswith("(", i):
            close = text.find(")", i)
            inner = text[i + 1:close] if close > 0 else ""
            if en.lower() not in inner.lower():
                out.append(f"({en}, ")
                i += 1                      # 원래 「(」는 위에서 새로 연 괄호가 대신한다
        else:
            out.append(f"({en})")
    out.append(text[i:])
    return "".join(out)


# ----------------------------------------------------------------- abbreviations and terms
# 1.1.6: abbreviations and terms a general reader may not know get a short explanation in parentheses at their first
# appearance on each page (both languages). Only running text: not inside svg/script/style/code, headings, links,
# quotations (blockquote) or the translation of a quotation (p.src), and never inside tag attributes (popovers).
TERMS = {
    "ko": [("DARPA", "미국 국방부 고등연구계획국"),
           ("LISP 기계", "LISP 언어를 빠르게 돌리도록 만든 인공지능 연구용 전용 컴퓨터"),
           ("TIMIT", "음성 인식 연구에 널리 쓰는 영어 낭독 음성 자료"),
           ("GMM-HMM", "가우스 혼합 모델과 은닉 마르코프 모델을 묶은 음향 모델. 그때까지 음성 인식에서 널리 쓰던 방식"),
           ("BLEU", "기계 번역 점수. 기계 번역이 사람이 한 번역과 낱말 묶음이 얼마나 겹치는지를 재며 너무 짧은 번역에는 감점한다. 같은 시험 자료에서 높을수록 사람 번역에 가깝다는 뜻이지, 뜻이 맞는지까지 보장하지는 않는다"),
           ("mAP", "물체 검출 점수. 찾아낸 것 가운데 맞은 비율(정밀도)과 실제 물체 가운데 찾아낸 비율(재현율)을 한데 묶은 값을 물체 종류마다 내어 평균한 것으로, 높을수록 좋다. 정답으로 치는 조건과 시험 자료에 따라 값이 달라진다. mean average precision"),
           ("SGVB", "계산하기 어려운 확률 모델을 학습하려고, 무작위 표본으로 학습 목표(변분 하한)와 그 기울기를 어림하는 방법. stochastic gradient variational Bayes"),
           ("AEVB", "그 어림값으로 데이터를 만드는 모델과 데이터에서 숨은 원인을 추정하는 모델을 함께 학습하는 알고리듬. auto-encoding variational Bayes")],
    "en": [("DARPA", "the US Defense Advanced Research Projects Agency"),
           ("Lisp-machine", "computers built to run the Lisp language fast, used for AI work"),
           ("TIMIT", "a widely used corpus of read English speech for speech recognition"),
           ("GMM-HMMs?", "acoustic models combining Gaussian mixture models and hidden Markov models, the usual approach in speech recognition until then"),
           ("BLEU", "a machine-translation score: how far word sequences overlap with human translations, with a penalty for translations that are too short; on the same test set higher means closer to the human translations, not that the meaning is right"),
           ("mAP", "mean average precision, a detection score: for each object class it combines the share of detections that are right (precision) and the share of objects found (recall), then averages over classes; higher is better, and the value depends on what counts as a correct detection and on the test set"),
           ("SGVB", "stochastic gradient variational Bayes, a way to train probability models that are hard to compute, by estimating the training objective (the variational lower bound) and its gradient from random samples"),
           ("AEVB", "auto-encoding variational Bayes, an algorithm that uses those estimates to train together a model that generates data and a model that infers the hidden causes of the data")],
}
TERM_RE = {l: re.compile("|".join(rf"(?<![A-Za-z0-9-])(?:{k})(?![A-Za-z0-9-])" for k, _ in v)) for l, v in TERMS.items()}
TERM_SKIP = ("svg", "script", "style", "code", "h1", "h2", "h3", "a", "blockquote", "p.src", "summary", "span.ng")


def explain_terms(body, lang):
    rx, pats = TERM_RE[lang], [(re.compile(rf"(?:{k})$"), v) for k, v in TERMS[lang]]
    done = set()

    def sub(text):
        def one(m):
            w = m.group(0)
            i = next(j for j, (pr, _) in enumerate(pats) if pr.match(w))
            if i in done:
                return w
            done.add(i)
            return f"{w}({pats[i][1]})" if lang == "ko" else f"{w} ({pats[i][1]})"
        return rx.sub(one, text)

    out, i, skip = [], 0, []
    for m in re.finditer(r"<[^>]+>", body):
        out.append(body[i:m.start()] if skip else sub(body[i:m.start()]))
        tag = m.group(0)
        name = re.match(r"</?\s*([a-zA-Z0-9]+)", tag)
        if name:
            n = name.group(1).lower()
            if n == "p" and 'class="src"' in tag:
                n = "p.src"
            elif n == "p" and tag.startswith("</") and skip and skip[-1] == "p.src":
                n = "p.src"
            elif n == "span" and 'class="ng"' in tag:
                n = "span.ng"           # a list that names the terms themselves (revision notes)
            elif n == "span" and tag.startswith("</") and skip and skip[-1] == "span.ng":
                n = "span.ng"
            if n in TERM_SKIP and not tag.endswith("/>"):
                if tag.startswith("</"):
                    if skip and skip[-1] == n:
                        skip.pop()
                else:
                    skip.append(n)
        out.append(tag)
        i = m.end()
    out.append(body[i:] if skip else sub(body[i:]))
    return "".join(out)


# ----------------------------------------------------------------- page shell

def page(lang, title, body, depth=1, desc="", active="", head="", chapter=False):
    if lang == "ko":
        body = gloss_ko(body)
    body = explain_terms(body, lang)
    # 1.1.7: after the glosses, so that a term's first gloss stays in the text and does not move into a list
    body, _items = site_nav.anchor_html(body, lang, title, with_h3=True)
    body = site_nav.with_toc(body, site_nav.page_toc(lang, _items, chapter=chapter), lang)
    if head:
        body = body.replace("</h1>", "</h1>" + head, 1)
    t = T[lang]
    root = "../" * depth
    other = "en" if lang == "ko" else "ko"
    hub_path = "" if lang == "ko" else "en/"
    nav = [("home", f"{root}{lang}/index.html", t["nav_home"]), ("chapters", f"{root}{lang}/chapters/index.html", t["nav_chapters"]),
           ("lineage", f"{root}{lang}/lineage/index.html", t["nav_lineage"]), ("winters", f"{root}{lang}/winters.html", t["nav_winters"]),
           ("papers", f"{root}{lang}/papers.html", t["nav_papers"]), ("method", f"{root}{lang}/method.html", t["nav_method"])]
    navh = "".join(f'<a href="{h}"{" class=\"on\"" if k == active else ""}>{n}</a>' for k, h, n in nav)
    return f"""<!DOCTYPE html>
<html lang="{lang}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} — {t['site']}</title><meta name="description" content="{esc(desc or t['tagline'])}">
<script>(function(){{var v=localStorage.getItem("ahp-theme");if(v)document.documentElement.setAttribute("data-theme",v)}})();</script>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700&family=Noto+Serif+KR:wght@600&display=swap" rel="stylesheet">
<style>{CSS}{site_nav.NAV_CSS}</style></head><body>
<header><a class="brand" href="{root}{lang}/index.html">{t['site']}</a><nav>{navh}</nav>
<div class="right"><a class="hub" href="https://bowonkwon.github.io/{hub_path}">{t['hub_link']}</a><button id="theme" class="theme" type="button" aria-label="theme">◑</button><a class="lang" href="{root}{other}/index.html">{t['lang_other']}</a></div></header>
<main>{body}</main>
<footer>{t['site']} · {t['version']} {VERSION} · {t['built']} {BUILD_DATE} · <a href="{REPO}">GitHub</a> · {t['hub']} <a href="https://bowonkwon.github.io/{hub_path}">bowonkwon.github.io</a></footer>
<script>{JS}{site_nav.NAV_JS}</script></body></html>"""


def glance(lang, items):
    return f'<div class="glance"><p class="glance-h">{T[lang]["key"]}</p><ul>' + "".join(f"<li>{i}</li>" for i in items) + "</ul></div>"


# ----------------------------------------------------------------- data

def date_span(s):
    """Earliest and latest day a first-public date can stand for: a full date is one day, YYYY-MM a month, YYYY a year."""
    import calendar
    import datetime
    y = int(s[:4])
    if len(s) >= 10:
        d = datetime.date(y, int(s[5:7]), int(s[8:10]))
        return d, d
    if len(s) >= 7:
        m = int(s[5:7])
        return datetime.date(y, m, 1), datetime.date(y, m, calendar.monthrange(y, m)[1])
    return datetime.date(y, 1, 1), datetime.date(y, 12, 31)


def load():
    papers = read_csv("papers.csv")
    for p in papers:
        p["dlo"], p["dhi"] = date_span(p["first_public_date"])
        p["yearf"] = float(p["first_public_date"][:4]) + (float(p["first_public_date"][5:7]) - 1) / 12 if len(p["first_public_date"]) >= 7 else float(p["first_public_date"][:4]) + 0.5
        p["lane"] = LANE_OF.get(p["theme"], "stat")
    papers.sort(key=lambda p: (p["yearf"], p["key"]))
    edges = [e for e in read_csv("edges.csv") if e["kind"] in ("OA", "original", "notion")]
    keys = {p["key"] for p in papers}
    edges = [e for e in edges if e["src"] in keys and e["dst"] in keys]
    return papers, edges


def primary_link(p):
    if p.get("doi"):
        return f"https://doi.org/{p['doi']}", "DOI"
    if p.get("arxiv"):
        return f"https://arxiv.org/abs/{p['arxiv']}", "arXiv"
    return p.get("url") or "", "URL"


def card_text(p, lang):
    return p["what_changed_ko"] if lang == "ko" else p["what_changed_en"]


# ----------------------------------------------------------------- SVG

def x_of(y, y0, y1, left, right, knee=None):
    """Linear map; with knee=(year, share) the years before `year` take `share` of the width (piecewise linear)."""
    if knee and y0 < knee[0] < y1:
        ky, sh = knee
        mid = left + sh * (right - left)
        if y <= ky:
            return left + (y - y0) / (ky - y0) * (mid - left)
        return mid + (y - ky) / (y1 - ky) * (right - mid)
    return left + (y - y0) / (y1 - y0) * (right - left)


KNEE = (2012, 0.55)  # home timeline: 1943–2012 on 55% of the width, 2012–2026 on 45%


def _label_w(text):
    """Rough width of a label at the chart font size (CJK glyphs are about twice as wide as Latin ones)."""
    return sum(12.5 if ord(ch) > 0x2E80 else 6.6 for ch in text)


def timeline_svg(papers, lang, y0=1942, y1=2026, width=1000, lane_h=42, chapter_links=True):
    lanes = [l for l, _ in LANES]
    left, right, top = max(150, int(max(_label_w(T[lang]["theme_names"][l]) for l in lanes)) + 18), width - 20, 40
    h = top + lane_h * len(lanes) + 30 + 18   # 1.1.5: +18 for the axis name under the year ticks
    out = [f'<svg viewBox="0 0 {width} {h}" role="img" aria-label="timeline">']
    out.append(f'<text x="{(left + right) / 2:.1f}" y="{h - 4}" text-anchor="middle" fill="var(--fg3)">{esc(T[lang]["axis_year"])}</text>')
    out.append(f'<text x="{left - 8}" y="{top - 23}" text-anchor="end" fill="var(--fg3)">{esc(T[lang]["axis_rows"])}</text>')  # 1.1.6: what the rows are
    # era bands
    # 1.1.6: a band runs to the end of its last year, except where the next chapter begins in that same year (the
    # titles share it, e.g. 1956), where it stops at the start of that year
    for i, e in enumerate(ERAS):
        a, b = C.ERA_SPAN[e]
        nxt = C.ERA_SPAN[ERAS[i + 1]][0] if i + 1 < len(ERAS) else None
        end = b if nxt == b else b + 1
        xa, xb = x_of(a, y0, y1, left, right, KNEE), x_of(min(end, y1), y0, y1, left, right, KNEE)
        out.append(f'<rect class="band{" alt" if i % 2 else ""}" x="{xa:.1f}" y="{top}" width="{xb - xa:.1f}" height="{lane_h * len(lanes)}"/>')
        out.append(f'<text x="{(xa + xb) / 2:.1f}" y="{top - (6 if i % 2 == 0 else 23)}" text-anchor="middle" font-size="10">{esc(C.ERA_SHORT[lang][e])}</text>')
    for i, lane in enumerate(lanes):
        y = top + i * lane_h
        out.append(f'<line class="grid" x1="{left}" x2="{right}" y1="{y + lane_h}" y2="{y + lane_h}"/>')
        out.append(f'<text x="{left - 8}" y="{y + lane_h / 2 + 4}" text-anchor="end">{esc(T[lang]["theme_names"][lane])}</text>')
    for yr in list(range(1950, 2001, 10)) + list(range(2010, 2027, 4)):
        x = x_of(yr, y0, y1, left, right, KNEE)
        out.append(f'<line class="ax" x1="{x:.1f}" x2="{x:.1f}" y1="{top}" y2="{top + lane_h * len(lanes)}"/><text x="{x:.1f}" y="{h - 26}" text-anchor="middle">{yr}</text>')
    # dots with slight vertical jitter by index within lane-year
    seen = defaultdict(int)
    for p in papers:
        li = lanes.index(p["lane"])
        slot = seen[(p["lane"], int(p["yearf"]))]; seen[(p["lane"], int(p["yearf"]))] += 1
        x = x_of(p["yearf"], y0, y1, left, right, KNEE)
        y = top + li * lane_h + lane_h / 2 + ((slot % 3) - 1) * 9
        href = f"chapters/{p['era']}.html#{p['key']}" if chapter_links else f"#{p['key']}"
        meta = f"{esc(p['authors_short'])} · {esc(p['first_public_date'][:4])}"
        out.append(f'<g class="dot" data-k="{p["key"]}" data-t="{esc(p["title"])}" data-m="{meta}" data-w="{esc(card_text(p, lang))}" data-href="{href}"><circle cx="{x:.1f}" cy="{y:.1f}" r="4.2" fill="var(--s1)" stroke="var(--card)" stroke-width="1"/></g>')  # 1.1.5: one colour; the four colours cycled over rows meant nothing
    out.append("</svg>")
    return "\n".join(out)


def cited_later(e, by_key):
    """True when the cited paper (dst) was first made public later than the citing one (src) for certain: its earliest
    possible day is after the citing paper's latest (dates given only to the year or month cover a span; see date_span)."""
    return by_key[e["dst"]]["dlo"] > by_key[e["src"]]["dhi"]


def lineage_knee(papers):
    """1.1.6: a diagram that runs from before 2000 to after 2014 bends its year axis at 2012 like the home timeline
    (KNEE), so that the many papers after 2010 are not packed into the right edge. Returns KNEE or None."""
    lo = min(p["yearf"] for p in papers); hi = max(p["yearf"] for p in papers)
    return KNEE if lo < 2000 and hi > 2014 else None


DENSE = 120  # 1.1.6: a diagram with more confirmed lines than this draws them fainter (hover still darkens one paper's lines)


def lineage_svg(papers, edges, lang, width=1000, href_prefix=""):
    if not papers:
        return ""
    by_key = {p["key"]: p for p in papers}
    lanes = [l for l, _ in LANES if any(p["lane"] == l for p in papers)]
    y0 = math.floor(min(p["yearf"] for p in papers)) - 1
    y1 = math.ceil(max(p["yearf"] for p in papers)) + 1
    knee = lineage_knee(papers)
    # 1.1.6: as many vertical positions as the fullest half-year slot needs (at least four, as before), so that papers
    # of the same slot no longer share a position; the rows grow with it
    occ = defaultdict(int)
    for p in papers:
        occ[(p["lane"], round(p["yearf"] * 2))] += 1
    single = len(lanes) == 1
    # a diagram with a single row (the theme-group pages and chapter 7) has room to spread: six heights taken in turn
    # in time order (0, 3, 1, 4, 2, 5), so that papers close in time do not sit on one line
    npos = max(6 if single else 4, max(occ.values()))
    order = [0, 3, 1, 4, 2, 5] + list(range(6, npos))
    lane_h = max(70, 13 * npos + 18)   # 70 for four positions, as before
    left, right, top = max(150, int(max(_label_w(T[lang]["theme_names"][l]) for l in lanes)) + 18), width - 20, (16 if single else 30)   # 1.1.6: room for the row name above multi-row diagrams
    h = top + lane_h * len(lanes) + 30 + 18   # 1.1.5: +18 for the axis name under the year ticks
    pos = {}
    seen = defaultdict(int)
    rank = {p["key"]: i for i, p in enumerate(sorted(papers, key=lambda p: (p["dlo"], p["key"])))}  # heights taken by first public day
    for p in papers:
        i = rank[p["key"]]
        li = lanes.index(p["lane"])
        slot = seen[(p["lane"], round(p["yearf"] * 2))]; seen[(p["lane"], round(p["yearf"] * 2))] += 1
        x = x_of(p["yearf"], y0, y1, left, right, knee)
        k = order[i % npos] if single else slot % npos
        y = top + li * lane_h + lane_h / 2 + (k - (npos - 1) / 2) * 13
        pos[p["key"]] = (x, y)
    solid = [e for e in edges if e["src"] in pos and e["dst"] in pos and e["kind"] != "notion"]
    dense = len(solid) > DENSE
    dense_attr = ' class="dense"' if dense else ""
    out = [f'<svg viewBox="0 0 {width} {h}" role="img" aria-label="lineage"{dense_attr}>']
    out.append(f'<text x="{(left + right) / 2:.1f}" y="{h - 4}" text-anchor="middle" fill="var(--fg3)">{esc(T[lang]["axis_year"])}</text>')
    if not single:   # 1.1.6: what the rows are, inside the diagram
        out.append(f'<text x="{left - 8}" y="{top - 4}" text-anchor="end" fill="var(--fg3)">{esc(T[lang]["axis_rows"])}</text>')
    for i, lane in enumerate(lanes):
        y = top + i * lane_h
        out.append(f'<line class="grid" x1="{left}" x2="{right}" y1="{y + lane_h}" y2="{y + lane_h}"/>')
        out.append(f'<text x="{left - 8}" y="{y + lane_h / 2 + 4}" text-anchor="end">{esc(T[lang]["theme_names"][lane])}</text>')
    if knee:
        ticks = list(range(int(math.ceil(y0 / 10) * 10), knee[0], 10)) + list(range(knee[0] + 2, int(y1) + 1, 4))
    else:
        step = 1 if y1 - y0 <= 12 else (5 if y1 - y0 <= 50 else 10)
        ticks = list(range(int(math.ceil(y0 / step) * step), int(y1) + 1, step))
    for yr in ticks:
        x = x_of(yr, y0, y1, left, right, knee)
        out.append(f'<line class="ax" x1="{x:.1f}" x2="{x:.1f}" y1="{top}" y2="{top + lane_h * len(lanes)}"/><text x="{x:.1f}" y="{h - 26}" text-anchor="middle">{yr}</text>')
    # lines whose cited paper is the later one are drawn last, in their own color, so that they can be told apart
    drawn = [e for e in edges if e["src"] in pos and e["dst"] in pos]
    drawn.sort(key=lambda e: e["kind"] != "notion" and cited_later(e, by_key))
    for e in drawn:
        (x2, y2), (x1, y1_) = pos[e["src"]], pos[e["dst"]]  # dst (cited) -> src (citing)
        cx = (x1 + x2) / 2
        cls = "edge" + (" notion" if e["kind"] == "notion" else " late" if cited_later(e, by_key) else "")
        out.append(f'<path class="{cls}" data-s="{e["src"]}" data-d="{e["dst"]}" d="M{x1:.1f},{y1_:.1f} C{cx:.1f},{y1_:.1f} {cx:.1f},{y2:.1f} {x2:.1f},{y2:.1f}"/>')
    for p in papers:
        x, y = pos[p["key"]]
        meta = f"{esc(p['authors_short'])} · {esc(p['first_public_date'][:4])}"
        out.append(f'<g class="dot" data-k="{p["key"]}" data-t="{esc(p["title"])}" data-m="{meta}" data-w="{esc(card_text(p, lang))}" data-href="{href_prefix}{p["era"]}.html#{p["key"]}"><circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="var(--s1)" stroke="var(--card)" stroke-width="1"/></g>')  # 1.1.5: one colour (see timeline_svg)
    out.append("</svg>")
    n_late = sum(1 for e in solid if cited_later(e, by_key))
    legend = ""
    if n_late:
        lab = (f"인용된 논문의 첫 공개일이 더 늦은 선({n_late}개)" if lang == "ko" else f"Line whose cited paper was made public later ({n_late})")
        base = "그 밖의 확인된 인용선" if lang == "ko" else "Other confirmed citation lines"
        legend = f'<div class="legend lg-line"><span style="--c:var(--fg3)">{esc(base)}</span><span class="late" style="--c:var(--s4)">{esc(lab)}</span></div>'
    return legend + sx("\n".join(out), width)


def sx(svg, width):
    """1.1.5: on narrow screens (<=640px) the chart keeps 92% of its drawn width and its box scrolls sideways, so the
    text stays at 10px or more instead of shrinking to about 4px."""
    return f'<div class="sx" style="--vw:{int(width * 0.92)}">{svg}</div>'


def _fmt(n, lang):
    return f"{n:,}"


def _who(p):
    return f"{p['authors_short']} {p['first_public_date'][:4]}"


def home_key(lang, edges):
    """HOME_KEY, with the dotted-line item told how many such lines this version has (1.1.5)."""
    items = list(C.HOME_KEY[lang])
    n = sum(1 for e in edges if e["kind"] == "notion")
    if n == 0:
        items[1] += " 현재 판에는 이런 점선이 없다(0건)." if lang == "ko" else " This version has none."
    return items


def timeline_caption(lang, papers):
    """Home timeline caption (1.1.5): the reviewed sentence, then rows, bands and click; one computed sentence."""
    t = T[lang]
    spans = [C.ERA_SPAN[e] for e in ERAS]
    over = [(ERAS[i], ERAS[i + 1], spans[i + 1][0], spans[i][1]) for i in range(len(ERAS) - 1) if spans[i + 1][0] < spans[i][1]]
    n = len(papers); late = sum(1 for p in papers if p["yearf"] >= KNEE[0])
    cnt = {l: sum(1 for p in papers if p["lane"] == l) for l, _ in LANES}
    hi = max(cnt, key=lambda l: cnt[l]); lo = min(cnt, key=lambda l: cnt[l])
    if lang == "ko":
        ov = "".join(f" {a[1]}장과 {b[1]}장은 {y0}–{y1}년이 겹친다." for a, b, y0, y1 in over)
        how = (t["timeline_cap"] + " 한 줄 안의 위아래 위치에는 뜻이 없다(같은 해 논문을 세 자리에 엇갈려 놓았다). 점을 누르면 그 논문이 실린 장으로 간다. "
               "옅은 띠는 장(1~7장)이 다루는 시기이고 띠 위에 장 이름을 적었다. 띠 색이 번갈아 바뀌는 것은 이웃한 장을 가르려는 것일 뿐이다." + ov)
        seen = (f"<b>보이는 것:</b> {n}편 가운데 {late}편({late / n:.0%})이 {KNEE[0]}년 이후에 처음 공개되었다. "
                f"줄별로는 「{t['theme_names'][hi]}」 줄이 {cnt[hi]}편으로 가장 많고 「{t['theme_names'][lo]}」 줄이 {cnt[lo]}편으로 가장 적다.")
    else:
        ov = "".join(f" Chapters {a[1]} and {b[1]} overlap in {y0}–{y1}." for a, b, y0, y1 in over)
        how = (t["timeline_cap"] + " The up-and-down position within a row means nothing (papers of the same year are staggered over three positions). Click a dot to go to its chapter. "
               "The pale bands are the periods the chapters (1–7) cover, with the chapter name above each band; the band color alternates only to separate neighboring chapters." + ov)
        seen = (f"<b>What it shows:</b> {late} of the {n} papers ({late / n:.0%}) were first made public in {KNEE[0]} or later. "
                f"By row, “{t['theme_names'][hi]}” has the most papers ({cnt[hi]}) and “{t['theme_names'][lo]}” the fewest ({cnt[lo]}).")
    return f"<p>{esc(how)}</p><p>{seen}</p>"


def lineage_caption(lang, ps, es, by_key, scope):
    """Caption of a lineage diagram (1.1.5). Template sentences from T, then one sentence computed from this diagram's
    papers and edges: number of papers and lines, the paper cited by the most other papers in the diagram (ties named),
    papers without any line, lines whose cited paper was first public later than the citing one."""
    t = T[lang]
    lanes = [l for l, _ in LANES if any(p["lane"] == l for p in ps)]
    drawn = [e for e in es if e["src"] in by_key and e["dst"] in by_key]
    solid = [e for e in drawn if e["kind"] != "notion"]
    parts = [t["cap_dot"], t["cap_rows_multi"] if len(lanes) > 1 else t["cap_rows_single"], t["cap_lines"]]
    if any(e["kind"] == "notion" for e in drawn):
        parts.append(t["cap_notion"])
    parts.append(t["cap_hover"])
    how = " ".join(parts)
    inc = defaultdict(int)
    for e in solid:
        inc[e["dst"]] += 1
    keys = {p["key"] for p in ps}
    lonely = sum(1 for k in keys if not any(e["src"] == k or e["dst"] == k for e in drawn))
    # 1.1.5: the cited paper is later for certain when its earliest possible day is after the citing paper's latest;
    # where the written dates overlap (year or month only) the order cannot be told and is counted apart
    later = sum(1 for e in solid if cited_later(e, by_key))
    unsure = sum(1 for e in solid if not cited_later(e, by_key)
                 and by_key[e["dst"]]["dhi"] > by_key[e["src"]]["dlo"])
    knee = lineage_knee(ps)
    dense = len(solid) > DENSE
    if knee:   # 1.1.6: the bent year axis, with the year spans that share the width computed from this diagram
        ya = math.floor(min(p["yearf"] for p in ps)) - 1; yb = math.ceil(max(p["yearf"] for p in ps)) + 1
        parts.insert(1, (f"가로축은 {knee[0]}년에서 꺾인다: 그 앞 {knee[0] - ya}년이 연도 구간 너비의 {knee[1]:.0%}, 뒤 {yb - knee[0]}년이 {1 - knee[1]:.0%}를 차지해서, {knee[0]}년 뒤에는 같은 1년이 더 넓다(눈금 간격도 10년에서 4년으로 바뀐다)."
                         if lang == "ko" else
                         f"The year axis bends at {knee[0]}: the {knee[0] - ya} years before it take {knee[1]:.0%} of the width of the year range and the {yb - knee[0]} years after it {1 - knee[1]:.0%}, so a year after {knee[0]} is wider (the ticks change from every 10 years to every 4)."))
        how = " ".join(parts)
    if dense:
        how += (" 선이 많은 그림이라 선을 옅게 그렸다." if lang == "ko" else " With this many lines, the lines are drawn faint.")
    seen = []
    if lang == "ko":
        seen.append(f"이 그림에는 논문 {len(ps)}편과 확인된 인용선 {_fmt(len(solid), lang)}개가 있다.")
        if inc:
            m = max(inc.values()); top = [k for k in sorted(keys, key=lambda k: by_key[k]["yearf"]) if inc.get(k) == m]
            names = " · ".join(_who(by_key[k]) for k in top[:3])
            seen.append(f"이 그림 안의 다른 논문에게 가장 많이 인용된 것은 {names}({'각각 ' if len(top) > 1 else ''}선 {m}개)이다." if len(top) <= 3
                        else f"이 그림 안에서 가장 많이 인용된 논문은 선 {m}개씩으로 {len(top)}편이 같다.")
        seen.append(f"선이 하나도 없는 논문은 {lonely}편이다." if lonely else "선이 하나도 없는 논문은 없다.")
        seen.append(f"선 {later}개는 인용된 논문의 첫 공개일이 인용한 논문보다 늦다(논문 카드에 적은 날짜 기준). 이 선들은 초록색으로 굵게 그렸고, 인용된 논문이 더 오른쪽이나 같은 자리에 놓인다. 왜 그런지는 하나씩 확인하지 않았다." if later
                    else "인용된 논문의 첫 공개일이 인용한 논문보다 늦은 것으로 확인되는 선은 없다(논문 카드에 적은 날짜 기준).")
        if unsure:
            seen.append(f"이 밖에 선 {unsure}개는 날짜가 연도나 달까지만 적혀 있어 어느 쪽이 먼저인지 가릴 수 없다.")
        head = "보이는 것: "
    else:
        seen.append(f"This diagram has {len(ps)} papers and {_fmt(len(solid), lang)} confirmed citation lines.")
        if inc:
            m = max(inc.values()); top = [k for k in sorted(keys, key=lambda k: by_key[k]["yearf"]) if inc.get(k) == m]
            names = ", ".join(_who(by_key[k]) for k in top[:3])
            seen.append((f"The papers cited by the most other papers in the diagram are {names} ({m} lines each)." if len(top) > 1
                         else f"The paper cited by the most other papers in the diagram is {names} ({m} lines).") if len(top) <= 3
                        else f"{len(top)} papers tie as the most cited within the diagram, with {m} lines each.")
        seen.append(f"{lonely} {'paper has' if lonely == 1 else 'papers have'} no line at all." if lonely else "No paper is without a line.")
        seen.append(f"In {later} {'line' if later == 1 else 'lines'} the cited paper's first public date is later than the citing paper's (dates as given on the paper cards). {'This line is' if later == 1 else 'These lines are'} drawn thicker in green, and the cited paper sits further right or at the same position; the reasons were not checked case by case." if later
                    else "No line has a cited paper whose first public date is confirmed to be later than the citing paper's (dates as given on the paper cards).")
        if unsure:
            seen.append(f"For {unsure} more {'line' if unsure == 1 else 'lines'} the dates are given only to the year or the month, so the order cannot be told.")
        head = "What it shows: "
    gloss = ""
    if len(lanes) > 1:
        rows = "".join(f'<dt><a href="../lineage/{l}.html">{esc(t["theme_names"][l])}</a></dt><dd>{esc(C.LANE_LEAD[lang].get(l, ""))}</dd>' for l in lanes)
        gloss = f'<details><summary>{esc(t["rows_gloss"])}</summary><dl>{rows}</dl></details>'
    return (f'<p>{esc(how)}</p><p><b>{head}</b>{esc(" ".join(seen))}</p>'
            f'<p>{esc(t["cap_scope_era"] if scope == "era" else t["cap_scope_lane"])}</p>{gloss}')


def _nice(ya, yb, n=4):
    """Round ticks from ya up to the first round value at or above yb (0, 10, 20 … rather than 0, 11.9556, 23.9111 …)."""
    span = yb - ya
    step = 10 ** math.floor(math.log10(span / n))
    for m in (1, 2, 2.5, 5, 10):
        if span / (step * m) <= n:
            step *= m
            break
    top = ya + math.ceil((yb - ya) / step - 1e-9) * step
    return [ya + step * i for i in range(int(round((top - ya) / step)) + 1)], top


def line_svg(series, lang, ylabel="", width=900, height=300, y0=None, y1=None, logy=False, xr=None, breaks=(), xlabel="", names=None):
    """series: list of (label, [(x,y)], color_idx, dashed). xlabel (1.1.5): name of the horizontal axis, written under
    the year ticks; the chart grows by 18 units to make room, so the plotting area keeps its size."""
    if xlabel:
        height += 18
    pts = [p for _, ps, _, _ in series for p in ps]
    if not pts:
        return ""
    xa = xr[0] if xr else min(p[0] for p in pts); xb = xr[1] if xr else max(p[0] for p in pts)
    ya = y0 if y0 is not None else 0; yb = y1 if y1 is not None else max(p[1] for p in pts) * 1.05
    lin_ticks = None
    if not logy:
        lin_ticks, top = _nice(ya, y1 if y1 is not None else max(p[1] for p in pts))
        if y1 is None:
            yb = top
        else:
            lin_ticks = [v for v in lin_ticks if v <= y1 + 1e-9]
    left, right, top, bot = 60, width - 20, 24, height - 30 - (18 if xlabel else 0)
    def X(x): return left + (x - xa) / (xb - xa) * (right - left)
    def Y(y):
        if logy:
            return bot - (math.log10(max(y, 1)) - math.log10(max(ya, 1))) / (math.log10(yb) - math.log10(max(ya, 1))) * (bot - top)
        return bot - (y - ya) / (yb - ya) * (bot - top)
    out = [f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="line chart">']
    # 1.1.6: a log axis gets the 1-2-5 steps of every power of ten in range (it had only 100 and 1000)
    ticks = [m * 10 ** k for k in range(int(math.log10(max(ya, 1))), int(math.log10(yb)) + 1) for m in (1, 2, 5) if ya <= m * 10 ** k <= yb] if logy else lin_ticks
    for tv in ticks:
        lab = f"{tv:,.0f}" if logy else f"{tv:g}"
        out.append(f'<line class="grid" x1="{left}" x2="{right}" y1="{Y(tv):.1f}" y2="{Y(tv):.1f}"/><text x="{left - 6}" y="{Y(tv) + 4:.1f}" text-anchor="end">{lab}</text>')
    step = 5 if xb - xa <= 50 else 10
    for xv in range(int(math.ceil(xa / step) * step), int(xb) + 1, step):
        out.append(f'<text x="{X(xv):.1f}" y="{bot + 22}" text-anchor="middle">{xv}</text>')
    if xlabel:
        out.append(f'<text x="{(left + right) / 2:.1f}" y="{height - 4}" text-anchor="middle" fill="var(--fg3)">{esc(xlabel)}</text>')
    out.append(f'<line class="ax" x1="{left}" x2="{right}" y1="{bot}" y2="{bot}"/>')
    for label, ps, ci, dashed in series:
        ps = sorted(ps)
        # a year named in `breaks` was left out on purpose; the line stops there instead of joining its neighbors
        cut = lambda i: i == 0 or any(ps[i - 1][0] < b < ps[i][0] for b in breaks)  # noqa: E731
        d = " ".join(f"{'M' if cut(i) else 'L'}{X(x):.1f},{Y(y):.1f}" for i, (x, y) in enumerate(ps))
        out.append(f'<path d="{d}" fill="none" stroke="var(--s{ci})" stroke-width="2"{" stroke-dasharray=\"4 3\"" if dashed else ""}/>')
        for x, y in ps:
            out.append(f'<circle cx="{X(x):.1f}" cy="{Y(y):.1f}" r="2.2" fill="var(--s{ci})"><title>{esc((names or {}).get(label, label))} {x}: {y:g}</title></circle>')
    if ylabel:
        out.append(f'<text x="{left}" y="{top - 8}">{esc(ylabel)}</text>')
    out.append("</svg>")
    names = names or {}   # legend and tooltip text (1.1.6: Korean meaning beside the searched phrase); values unchanged
    legend = '<div class="legend">' + "".join(f'<span style="--c:var(--s{ci})">{esc(names.get(l, l))}</span>' for l, _, ci, _ in series) + "</div>"
    return legend + sx("\n".join(out), width)


# ----------------------------------------------------------------- pages

def paper_block(p, lang, edges, by_key, depth_prefix=""):
    t = T[lang]
    url, kind = primary_link(p)
    links = []
    if url:
        links.append(f'<a href="{esc(url)}">{kind}</a>')
    if p.get("arxiv") and kind != "arXiv":
        links.append(f'<a href="https://arxiv.org/abs/{esc(p["arxiv"])}">arXiv</a>')
    if p.get("url") and kind != "URL":
        links.append(f'<a href="{esc(p["url"])}">{t["original"]}</a>')
    cites = sorted({e["dst"] for e in edges if e["src"] == p["key"] and e["kind"] != "notion"})
    cited = sorted({e["src"] for e in edges if e["dst"] == p["key"] and e["kind"] != "notion"})
    def rel(ks):
        return ", ".join(f'<a href="{depth_prefix}{by_key[k]["era"]}.html#{k}">{esc(by_key[k]["authors_short"])} {by_key[k]["first_public_date"][:4]}</a>' for k in ks if k in by_key) or t["none"]
    quote = ""
    if p.get("key_sentence"):
        quote = f'<blockquote>{esc(p["key_sentence"])}<cite>{esc(p.get("key_sentence_cite", ""))}</cite></blockquote>'
        if lang == "ko" and p.get("key_sentence_ko"):
            quote += f'<p class="src">{esc(p["key_sentence_ko"])}</p>'
    oa = f' · {t["oa_cited"]} {int(p["oa_cited_by"]):,} ({t["checked"]} {esc(p["oa_checked"])})' if p.get("oa_cited_by") else ""
    return f"""<article class="paper" id="{p['key']}">
<h3>{esc(p['title'])}</h3>
<p class="meta">{esc(p['authors'])} · <b>{t['first_public']}</b> {esc(p['first_public_date'])} ({esc(p['first_public_type'])}) · {t['venue']}: {esc(p['venue'])}{(' · ' + t['pages'] + ' ' + esc(p['pages'])) if p.get('pages') else ''}{oa}</p>
<p class="meta">{' '.join(links)}{(' · ' + esc(p['other_dates'])) if p.get('other_dates') else ''}</p>
{quote}
<p class="wc"><b>{t['what_changed']}.</b> {esc(card_text(p, lang))}</p>
<p class="rel">{t['cites']}: {rel(cites)}<br>{t['cited_by']}: {rel(cited)}</p>
</article>"""


def build_lang(lang, papers, edges):
    t = T[lang]
    by_key = {p["key"]: p for p in papers}
    out = SITE / lang
    (out / "chapters").mkdir(parents=True, exist_ok=True)
    (out / "lineage").mkdir(parents=True, exist_ok=True)
    n_edges = sum(1 for e in edges if e["kind"] != "notion")
    # home
    eras_html = "".join(f'<a class="card" href="chapters/{e}.html"><b>{esc(C.ERA_TITLE[lang][e])}</b><small>{esc(C.ERA_LEAD[lang][e])}</small><small>{sum(1 for p in papers if p["era"] == e)} {t["papers"]}</small></a>' for e in ERAS)
    tl_list = "".join(f'<li><a href="chapters/{p["era"]}.html#{p["key"]}">{esc(p["first_public_date"][:4])} — {esc(p["authors_short"])}, {esc(p["title"])}</a></li>' for p in papers)
    body = f"""<div class="hero"><h1>{t['site']}</h1><p class="lead">{esc(t['tagline'])}</p>{glance(lang, home_key(lang, edges))}</div>
<div class="stats"><span class="stat"><span class="n">{len(papers)}</span><small>{esc(C.STAT[lang]['papers'])}</small></span><span class="stat"><span class="n">{n_edges}</span><small>{esc(C.STAT[lang]['edges'])}</small></span><span class="stat"><span class="n">{papers[0]['first_public_date'][:4]}–{papers[-1]['first_public_date'][:4]}</span><small>{esc(C.STAT[lang]['span'])}</small></span></div>
<figure class="tl-wide">{timeline_svg(papers, lang)}<figcaption>{timeline_caption(lang, papers)}</figcaption></figure>
<div class="tl-list"><ol>{tl_list}</ol></div>
<h2 id="eras">{t['nav_chapters']}</h2><div class="cards">{eras_html}</div>
<div class="prose">{C.HOME_INTRO[lang]}</div>"""
    (out / "index.html").write_text(page(lang, t["site"], body, 1, active="home"), encoding="utf-8")
    # chapters index + pages
    ch_lead = (f"일곱 장의 목록이다. 장마다 그 시기의 서술, 계보도, 논문 카드가 있다(모두 {len(papers)}편)." if lang == "ko"
               else f"The seven eras. Each has a narrative of the period, a lineage diagram and the paper cards ({len(papers)} papers in all).")
    body = f"<h1>{t['nav_chapters']}</h1><p class=\"lead\">{esc(ch_lead)}</p><div class=\"cards\">{eras_html.replace('href=\"chapters/', 'href=\"')}</div>"
    ch_name = (lambda k, e: f"{k}장. {C.ERA_TITLE[lang][e]}") if lang == "ko" else (lambda k, e: f"Chapter {k}. {C.ERA_TITLE[lang][e]}")
    ch_list = [(f"{e}.html", esc(ch_name(k, e))) for k, e in enumerate(ERAS, 1)]
    ch_secs = [(f"{e}.html", esc(ch_name(k, e)),
                [(m.group(1), m.group(2)) for m in re.finditer(r'<h3 id="([^"]+)">(.*?)</h3>', C.ERA_TEXT[lang][e], re.S)]
                + [("lineage", esc(t["nav_lineage"])), ("papers", esc(t["nav_papers"]))]) for k, e in enumerate(ERAS, 1)]
    (out / "chapters/index.html").write_text(page(lang, t["nav_chapters"], body, 2, active="chapters",
                                                  head=site_nav.full_contents(lang, ch_secs, [])), encoding="utf-8")
    for e in ERAS:
        ps = [p for p in papers if p["era"] == e]
        es = [x for x in edges if x["src"] in {p["key"] for p in ps} and x["dst"] in {p["key"] for p in ps}]
        boxes = "".join(C.BOXES[lang].get(e, []))
        body = f"""<div class="eyebrow"><span class="tag">{esc(C.ERA_SHORT[lang][e])}</span></div><h1>{esc(C.ERA_TITLE[lang][e])}</h1><p class="lead">{esc(C.ERA_LEAD[lang][e])}</p>
{glance(lang, [k.replace("{N_PAPERS}", str(len(ps))).replace("{N_ARXIV_V1}", str(sum(p["first_public_type"] == "arXiv v1" for p in ps))) for k in C.ERA_KEY[lang][e]])}
{site_nav.TOC_MARK}<div class="prose">{C.ERA_TEXT[lang][e]}</div>
{boxes}
<h2 id="lineage">{t['nav_lineage']}</h2><figure>{lineage_svg(ps, es, lang)}<figcaption>{lineage_caption(lang, ps, es, by_key, "era")}</figcaption></figure>
<h2 id="papers">{t['nav_papers']} ({len(ps)})</h2>{''.join(paper_block(p, lang, edges, by_key) for p in ps)}"""
        (out / f"chapters/{e}.html").write_text(page(lang, C.ERA_TITLE[lang][e], body, 2, active="chapters", chapter=True,
                                                    head=site_nav.chapter_list(lang, ch_list, ERAS.index(e), "index.html")), encoding="utf-8")
    # lineage pages by lane
    lane_cards = "".join(f'<a class="card" href="{l}.html"><b>{esc(t["theme_names"][l])}</b><small>{sum(1 for p in papers if p["lane"] == l)} {t["papers"]}</small></a>' for l, _ in LANES)
    # 1.1.5: head summary of the lineage list, computed
    lane_n = {l: sum(1 for p in papers if p["lane"] == l) for l, _ in LANES}
    lane_e = {l: sum(1 for x in edges if x["kind"] != "notion" and by_key[x["src"]]["lane"] == l and by_key[x["dst"]]["lane"] == l) for l, _ in LANES}
    big = max(lane_n, key=lambda l: lane_n[l]); small = min(lane_n, key=lambda l: lane_n[l]); within = sum(lane_e.values())
    if lang == "ko":
        idx_sum = [f"주제 묶음 {len(LANES)}개마다 논문과 그 사이의 확인된 인용선을 그린 면의 목록이다.",
                   f"가장 큰 묶음은 「{t['theme_names'][big]}」({lane_n[big]}편), 가장 작은 묶음은 「{t['theme_names'][small]}」({lane_n[small]}편)이다.",
                   f"묶음 면에는 같은 묶음 안의 인용선만 그린다. 여덟 면의 선을 모두 합하면 {within:,}개로, 확인된 인용선 전체 {n_edges:,}개 가운데 나머지는 서로 다른 묶음 사이의 선이다."]
    else:
        idx_sum = [f"A list of pages, one for each of the {len(LANES)} theme groups, each drawing the group's papers and the confirmed citations among them.",
                   f"The largest group is “{t['theme_names'][big]}” ({lane_n[big]} papers), the smallest “{t['theme_names'][small]}” ({lane_n[small]}).",
                   f"A group page draws only lines within the group. The eight pages together show {within:,} lines; the rest of the {n_edges:,} confirmed citation lines join papers of different groups."]
    body = f"<h1>{t['nav_lineage']}</h1><p class=\"lead\">{esc(C.LINEAGE_LEAD[lang])}</p>{glance(lang, [esc(x) for x in idx_sum])}<div class=\"cards\">{lane_cards}</div>"
    (out / "lineage/index.html").write_text(page(lang, t["nav_lineage"], body, 2, active="lineage"), encoding="utf-8")
    for l, _ in LANES:
        ps = [p for p in papers if p["lane"] == l]
        ks = {p["key"] for p in ps}
        es = [x for x in edges if x["src"] in ks and x["dst"] in ks]
        rows = "".join(f'<tr><td class="nw">{esc(p["first_public_date"][:4])}</td><td>{esc(p["authors_short"])}</td><td><a href="../chapters/{p["era"]}.html#{p["key"]}">{esc(p["title"])}</a></td><td>{esc(C.ERA_SHORT[lang][p["era"]])}</td></tr>' for p in ps)
        late = sum(1 for p in ps if p["yearf"] >= KNEE[0])
        y_a, y_b = ps[0]["first_public_date"][:4], ps[-1]["first_public_date"][:4]
        n_es = sum(1 for x in es if x["kind"] != "notion")
        if lang == "ko":
            lsum = [f"「{t['theme_names'][l]}」 묶음의 논문을 첫 공개 연도 순으로 놓고, 그 사이의 확인된 인용을 선으로 이은 면이다.",
                    f"논문 {len(ps)}편(첫 공개 {y_a}–{y_b}년), 묶음 안의 인용선 {n_es}개. " + (f"모두 {KNEE[0]}년 이후에 처음 공개되었다." if late == len(ps) else f"{KNEE[0]}년 이후에 처음 공개된 논문은 없다." if late == 0 else f"{len(ps)}편 가운데 {late}편이 {KNEE[0]}년 이후에 처음 공개되었다."),
                    "다른 묶음 논문과의 인용은 이 면에 그리지 않는다."]
        else:
            lsum = [f"The papers of the “{t['theme_names'][l]}” group in order of first public year, with the confirmed citations among them drawn as lines.",
                    f"{len(ps)} papers (first public {y_a}–{y_b}), {n_es} citation lines within the group; " + (f"all were first made public in {KNEE[0]} or later." if late == len(ps) else f"none was first made public in {KNEE[0]} or later." if late == 0 else f"{late} of the {len(ps)} were first made public in {KNEE[0]} or later."),
                    "Citations to papers of other groups are not drawn on this page."]
        body = f"""<h1>{esc(t['theme_names'][l])}</h1><p class="lead">{esc(C.LANE_LEAD[lang].get(l, ''))}</p>{glance(lang, [esc(x) for x in lsum])}
<figure>{lineage_svg(ps, es, lang, href_prefix='../chapters/')}<figcaption>{lineage_caption(lang, ps, es, by_key, "lane")}</figcaption></figure>
<div class="wrap"><table class="sort"><thead><tr><th>{t['year']}</th><th>{t['author']}</th><th>{t['title']}</th><th>{t['chapter']}</th></tr></thead><tbody>{rows}</tbody></table></div>"""
        (out / f"lineage/{l}.html").write_text(page(lang, t["theme_names"][l], body, 2, active="lineage"), encoding="utf-8")
    # winters
    (out / "winters.html").write_text(page(lang, t["nav_winters"], winters_body(lang), 1, active="winters"), encoding="utf-8")
    # papers list
    rows = []
    for p in papers:
        url, kind = primary_link(p)
        rows.append(f'<tr><td class="nw" data-v="{p["yearf"]:.2f}">{esc(p["first_public_date"])}</td><td>{esc(p["authors_short"])}</td><td><a href="chapters/{p["era"]}.html#{p["key"]}">{esc(p["title"])}</a></td><td class="nw">{esc(p["venue_short"])}</td><td class="nw"><a href="{esc(url)}">{kind}</a></td><td class="nw">{esc(C.ERA_SHORT[lang][p["era"]])}</td><td class="nw">{esc(t["theme_names"][p["lane"]])}</td></tr>')
    span = f"{papers[0]['first_public_date'][:4]}–{papers[-1]['first_public_date'][:4]}"
    p_head = (f"선정 논문 {len(papers)}편(첫 공개 {span}년)을 한 표에 모았다. " if lang == "ko"
              else f"All {len(papers)} selected papers (first public {span}) in one table. ")
    body = f"""<h1>{t['nav_papers']}</h1><p class="lead">{esc(p_head + C.PAPERS_LEAD[lang].split(". ", 1)[1])}</p>
<p class="files"><a href="../data/papers.csv">{t['download']}: papers.csv</a> <a href="../data/edges.csv">edges.csv</a> <a href="../data/datapackage.json">datapackage.json</a></p>
<div class="filter"><input type="search" data-target="pt" placeholder="{t['filter']}"></div>
<div class="wrap"><table class="sort" id="pt"><thead><tr><th>{t['first_public']}</th><th>{t['author']}</th><th>{t['title']}</th><th>{t['venue']}</th><th>{t['original']}</th><th>{t['chapter']}</th><th>{t['theme']}</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div>"""
    (out / "papers.html").write_text(page(lang, t["nav_papers"], body, 1, active="papers"), encoding="utf-8")
    # method
    (out / "method.html").write_text(page(lang, t["nav_method"], C.METHOD[lang](papers, edges), 1, active="method"), encoding="utf-8")


def winters_body(lang):
    t = T[lang]
    ph = read_csv("winter_title_phrases.csv")
    att = [a for a in read_csv("winter_attendance.csv") if not a["note"]]
    nips = read_csv("winter_neurips_accepted.csv")
    s1 = [(lab, [(int(r["year"]), float(r[f"per10k_{col}"])) for r in ph if r[f"per10k_{col}"] and 1960 <= int(r["year"]) <= 2024 and int(r["year"]) != 1970], ci, False)
          for lab, col, ci in (("“artificial intelligence”", "artificial_intelligence", 1), ("“expert system”", "expert_system", 2), ("“neural network”", "neural_network", 3))]
    confs = ["AAAI", "IJCAI", "NeurIPS"]
    s2 = []
    for i, c in enumerate(confs, 1):
        pts = {}
        for a in att:
            if a["conference"] == c:
                pts.setdefault(int(a["year"]), int(a["attendees"]))
        s2.append((c, sorted(pts.items()), i, False))
    s3 = [("NeurIPS", [(int(r["year"]), int(r["accepted_papers"])) for r in nips if not r["note"]], 1, False)]
    note1, note2 = winter_notes(lang, s1, s2)
    s1z, zoom_title, zoom_cap = winter_zoom(lang, s1)
    xl = "연도" if lang == "ko" else "Year"
    body = f"""<h1>{t['nav_winters']}</h1><p class="lead">{esc(C.WINTER_LEAD[lang])}</p>{glance(lang, C.WINTER_KEY[lang])}
<div class="prose">{C.WINTER_TEXT[lang]['intro']}</div>
<h2 id="title-terms">{esc(C.WINTER_TEXT[lang]['h1'])}</h2><figure>{line_svg(s1, lang, ylabel=C.WINTER_TEXT[lang]['y1'], xr=(1960, 2024), breaks=(1970,), xlabel=xl, names=PHRASE_KO if lang == 'ko' else None)}<figcaption><p>{esc(C.WINTER_TEXT[lang]['cap1'].replace('{EX1970}', ex1970(lang, ph)))}</p><p>{esc(note1)}</p></figcaption></figure>
<h3>{esc(zoom_title)}</h3><figure>{line_svg(s1z, lang, ylabel=C.WINTER_TEXT[lang]['y1'], xr=ZOOM, breaks=(1970,), xlabel=xl, names=PHRASE_KO if lang == 'ko' else None)}<figcaption><p>{esc(zoom_cap)}</p></figcaption></figure>
<div class="prose">{C.WINTER_TEXT[lang]['t1']}</div>
<h2 id="attendance">{esc(C.WINTER_TEXT[lang]['h2'])}</h2><figure>{line_svg(s2, lang, ylabel=C.WINTER_TEXT[lang]['y2'], xr=(1984, 2025), xlabel=xl)}<figcaption><p>{esc(C.WINTER_TEXT[lang]['cap2'])}</p><p>{esc(note2)}</p></figcaption></figure>
<div class="prose">{C.WINTER_TEXT[lang]['t2']}</div>
<h2 id="neurips-papers">{esc(C.WINTER_TEXT[lang]['h3'])}</h2><figure>{line_svg(s3, lang, ylabel=C.WINTER_TEXT[lang]['y3'], logy=True, y0=50, y1=6000, xr=(1987, 2024), xlabel=xl)}<figcaption>{esc(C.WINTER_TEXT[lang]['cap3'])}</figcaption></figure>
<div class="prose">{C.WINTER_TEXT[lang]['t3']}</div>
<h2 id="funding">{esc(C.WINTER_TEXT[lang]['h4'])}</h2><div class="prose">{C.WINTER_TEXT[lang]['t4']}</div>
<p class="files"><a href="../data/winter_title_phrases.csv">winter_title_phrases.csv</a> <a href="../data/winter_attendance.csv">winter_attendance.csv</a> <a href="../data/winter_neurips_accepted.csv">winter_neurips_accepted.csv</a></p>"""
    return body


ZOOM = (1960, 2015)
PHRASE_KO = {"“artificial intelligence”": "“artificial intelligence”(인공지능)", "“expert system”": "“expert system”(전문가 시스템)", "“neural network”": "“neural network”(신경망)"}


def winter_zoom(lang, s1):
    """1.1.6: the two low phrase series of the first chart drawn again on their own scale, so that values such as 9, 3.4
    and 1.5 per 10,000 no longer lie along the bottom. Same values; years and series cut as the caption says."""
    low = [(lab, [(x, y) for x, y in ps if ZOOM[0] <= x <= ZOOM[1]], ci, d) for lab, ps, ci, d in s1 if lab != "“neural network”"]
    top = _nice(0, max(y for _, ps, _, _ in low for _, y in ps))[1]
    peaks = [(lab, max(ps, key=lambda t: t[1])) for lab, ps, _, _ in low]
    nn = next(ps for lab, ps, _, _ in s1 if lab == "“neural network”")
    assert any(ZOOM[0] <= x <= ZOOM[1] and y > top for x, y in nn)  # the caption says it goes above this scale
    v2000 = {lab: dict(ps)[2000] for lab, ps, _, _ in low}
    if lang == "ko":
        title = f"같은 그래프의 확대 — 「artificial intelligence」와 「expert system」, {ZOOM[0]}–{ZOOM[1]}년"
        pk = ", ".join(f"「{lab.strip('“”')}」 {y}년 {v:.1f}건" for lab, (y, v) in peaks)
        cap = (f"위 그래프의 두 구절만 세로축을 0–{top:g}으로 늘려 다시 그렸다. 점 하나가 한 해의 값이고 단위는 위 그래프와 같다(OpenAlex 레코드 1만 건당, 제목에 그 구절이 든 레코드 수). 값도 위 그래프와 같고, 1970년은 위처럼 뺐다. "
               f"「neural network」는 이 기간에도 이 눈금을 넘는 해가 있어(가장 높은 해는 위 그래프에서 본다) 이 그래프에는 그리지 않았다. "
               f"보이는 것: 가장 높은 해는 {pk}이고, 2000년에는 각각 "
               + ", ".join(f"{v:.2f}건" if v < 1 else f"{v:.1f}건" for v in v2000.values()) + "이다.")
    else:
        title = f"The same chart enlarged: “artificial intelligence” and “expert system”, {ZOOM[0]}–{ZOOM[1]}"
        pk = ", ".join(f"{lab.strip('“”')} {v:.1f} in {y}" for lab, (y, v) in peaks)
        cap = (f"The two phrases of the chart above drawn again with the vertical axis stretched to 0–{top:g}. Each dot is one year's value, in the same unit as above (records with the phrase in the title per 10,000 OpenAlex records). The values are the same, and 1970 is left out as above. "
               f"“Neural network” goes above this scale in some of these years (its highest year is in the chart above), so it is not drawn here. "
               f"What it shows: the highest years are {pk}; in 2000 the values are "
               + " and ".join(f"{v:.2f}" if v < 1 else f"{v:.1f}" for v in v2000.values()) + " respectively.")
    return low, title, cap


def ex1970(lang, ph):
    """Why 1970 is left out of the title-phrase chart: what the table shows, and what was not checked (1.1.5)."""
    row = {int(r["year"]): r for r in ph}
    cols = ("artificial_intelligence", "expert_system", "neural_network")
    assert all(int(row[1970][f"title_{c}"]) > int(row[1969][f"title_{c}"]) and int(row[1970][f"title_{c}"]) > int(row[1971][f"title_{c}"]) for c in cols)
    a, b, c = (int(row[y]["title_expert_system"]) for y in (1969, 1970, 1971))
    if lang == "ko":
        return (f"1970년 값은 뺐다. 그해에는 세 구절의 건수가 모두 앞뒤 해보다 많아서다(「expert system」이 1969년 {a}건, 1970년 {b}건, 1971년 {c}건). "
                "레코드를 하나씩 확인하지 않아 그 까닭은 알지 못하며, 이 면은 이 값을 해석하지 않는다.")
    return (f"The 1970 value is left out: the counts of all three phrases in that year are higher than in the years before and after "
            f"(“expert system”: {a} in 1969, {b} in 1970, {c} in 1971). The records were not checked one by one, so the reason is not known, and this page does not interpret the value.")


def winter_notes(lang, s1, s2):
    """1.1.5: two computed sentences that name values the page does not interpret — the 2002 title-phrase values
    (above both neighboring years) and NeurIPS attendance after 2020. Values come from the plotted series."""
    YR = 2002
    d = {lab: dict(ps) for lab, ps, _, _ in s1}
    up = [lab for lab, v in d.items() if all(y in v for y in (YR - 1, YR, YR + 1)) and v[YR] > v[YR - 1] and v[YR] > v[YR + 1]]
    nn = d["“neural network”"]
    n = dict(next(ps for lab, ps, _, _ in s2 if lab == "NeurIPS"))
    a = 2020; after = {y: v for y, v in n.items() if y > a}
    low_y = min((y for y in after if y < max(after)), key=lambda y: after[y]); last = max(after)
    if lang == "ko":
        both = "세 구절 모두" if len(up) == len(d) else f"{len(up)}개 구절이"
        one = (f"{YR}년 값은 {both} 바로 앞뒤 해보다 높다(「neural network」 {YR - 1}년 {nn[YR - 1]:.1f} → {YR}년 {nn[YR]:.1f} → {YR + 1}년 {nn[YR + 1]:.1f}). "
               "이 면은 그 까닭을 확인하지 않았고, 이 튀는 값을 해석하지 않는다.")
        two = (f"NeurIPS 참가자는 {a}년 {n[a]:,}명 뒤 {low_y}년 {after[low_y]:,}명까지 줄었다가 {last}년 {after[last]:,}명이 되었다. "
               f"이 면은 그 까닭을 확인하지 않았고, {a}년 뒤의 오르내림을 해석하지 않는다.")
    else:
        both = "all three phrases" if len(up) == len(d) else f"{len(up)} phrases"
        one = (f"In {YR} {both} are higher than in the year before and the year after (“neural network”: {nn[YR - 1]:.1f} in {YR - 1}, {nn[YR]:.1f} in {YR}, {nn[YR + 1]:.1f} in {YR + 1}). "
               "This page has not checked the reason and does not interpret this jump.")
        two = (f"NeurIPS attendance went from {n[a]:,} in {a} down to {after[low_y]:,} in {low_y} and then to {after[last]:,} in {last}. "
               f"This page has not checked the reason and does not interpret the rise and fall after {a}.")
    return one, two


def write_data(papers, edges):
    (SITE / "data").mkdir(parents=True, exist_ok=True)
    for f in ("papers.csv", "edges.csv", "winter_title_phrases.csv", "winter_attendance.csv", "winter_neurips_accepted.csv", "awards.csv"):
        if (D / f).exists():
            shutil.copy(D / f, SITE / "data" / f)
    dp = {"name": "ai-history-in-papers", "version": VERSION, "created": BUILD_DATE, "licenses": [{"name": "CC-BY-4.0", "path": "https://creativecommons.org/licenses/by/4.0/"}],
          "resources": C.DATAPACKAGE_RESOURCES}
    (SITE / "data" / "datapackage.json").write_text(json.dumps(dp, indent=1, ensure_ascii=False), encoding="utf-8")


def main():
    papers, edges = load()
    if SITE.exists():
        for child in SITE.iterdir():
            shutil.rmtree(child) if child.is_dir() else child.unlink()
    for lang in ("ko", "en"):
        build_lang(lang, papers, edges)
    write_data(papers, edges)
    (SITE / "index.html").write_text('<!DOCTYPE html><html lang="ko"><head><meta charset="utf-8"><meta http-equiv="refresh" content="0; url=ko/index.html"><title>AI History in Papers</title></head><body><a href="ko/index.html">한국어</a> · <a href="en/index.html">English</a></body></html>', encoding="utf-8")
    (SITE / ".nojekyll").write_text("", encoding="utf-8")
    print("papers", len(papers), "edges", len(edges), "files", sum(1 for _ in SITE.rglob("*") if _.is_file()))


if __name__ == "__main__":
    main()
