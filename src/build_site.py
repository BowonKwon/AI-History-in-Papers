"""Build the static site (ko/en) into site/ from data/derived/*.csv and src/content.py.

  python src/build_site.py

Inputs
  data/derived/papers.csv      one row per selected paper (see docs/data-schema.md)
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
VERSION = "1.0"
BUILD_DATE = date.today().isoformat()
REPO = "https://github.com/BowonKwon/AI-History-in-Papers"

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
               lineage_cap="실선은 인용이 확인된 선(OpenAlex 또는 인용한 논문의 참고문헌 목록), 점선은 교과서가 말하는 영향이지만 인용이 확인되지 않은 선. 세로 위치는 주제 묶음.",
               theme_names={"neural": "신경망 학습", "rl": "강화학습·게임", "lang": "언어·음성", "vision": "시각·생성", "search": "탐색·계획·지식", "stat": "확률·통계·기원", "align": "규모·정렬·안전", "agent": "에이전트"}),
    "en": dict(site="AI History in Papers", lang_other="한국어", tagline="The history of AI research from 1943 to today, followed through its original papers",
               nav_home="Home", nav_chapters="Eras", nav_lineage="Lineage", nav_winters="Winters and booms", nav_papers="Paper list", nav_method="Method and limits",
               key="Key point", version="Version", built="Built", hub="All public materials", first_public="First public", venue="Venue", pages="Pages", original="Original",
               quote="From the paper", what_changed="What changed", cites="Cites (within this list)", cited_by="Cited by (within this list)",
               oa_cited="Citations (OpenAlex)", checked="checked", none="none", edge_oa="Citation confirmed in OpenAlex", edge_orig="Citation confirmed in the paper's reference list", edge_notion="Textbook attribution, citation not confirmed",
               download="Download CSV", filter="Filter", year="Year", author="First author", title="Title", chapter="Era", theme="Theme", papers="papers",
               timeline_cap="One dot per paper. Horizontal position is the first public year (the axis gives the 70 years before 2012 and the 14 years after it similar widths); rows are theme groups. Hover a dot for its card.",
               lineage_cap="Solid lines are confirmed citations (OpenAlex or the citing paper's own reference list); dotted lines are influences stated in textbooks without a confirmed citation. Vertical position is the theme group.",
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
figure{margin:1.2rem 0;background:var(--card);border:1px solid var(--line);border-radius:10px;padding:1rem 1rem .8rem;box-shadow:var(--shadow)}figcaption{font-size:.86rem;color:var(--fg2);margin-top:.5rem;line-height:1.5}
svg{max-width:100%;height:auto;display:block}svg text{font-family:var(--body);fill:var(--fg2);font-size:11px}svg .ax{stroke:var(--line)}svg .grid{stroke:var(--grid)}
svg .dot{cursor:pointer}svg .dot:hover circle,svg .dot.on circle{stroke:var(--fg);stroke-width:2}
svg .edge{fill:none;stroke:var(--fg3);stroke-width:1.1;opacity:.55}svg .edge.notion{stroke-dasharray:3 3;opacity:.5}svg .edge.hi{stroke:var(--accent);stroke-width:2;opacity:1}svg .edge.dim{opacity:.12}
svg .band{fill:var(--s1);opacity:.07}svg .band.alt{fill:var(--s2)}
.legend{display:flex;gap:1.1rem;font-size:.86rem;color:var(--fg2);flex-wrap:wrap;margin:.2rem 0 .4rem}.legend span::before{content:"";display:inline-block;width:11px;height:11px;border-radius:3px;margin-right:.4rem;vertical-align:-1px;background:var(--c)}
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


# ----------------------------------------------------------------- page shell

def page(lang, title, body, depth=1, desc="", active=""):
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
<style>{CSS}</style></head><body>
<header><a class="brand" href="{root}{lang}/index.html">{t['site']}</a><nav>{navh}</nav>
<div class="right"><button id="theme" class="theme" type="button" aria-label="theme">◑</button><a class="lang" href="{root}{other}/index.html">{t['lang_other']}</a></div></header>
<main>{body}</main>
<footer>{t['site']} · {t['version']} {VERSION} · {t['built']} {BUILD_DATE} · <a href="{REPO}">GitHub</a> · {t['hub']} <a href="https://bowonkwon.github.io/{hub_path}">bowonkwon.github.io</a></footer>
<script>{JS}</script></body></html>"""


def glance(lang, items):
    return f'<div class="glance"><p class="glance-h">{T[lang]["key"]}</p><ul>' + "".join(f"<li>{i}</li>" for i in items) + "</ul></div>"


# ----------------------------------------------------------------- data

def load():
    papers = read_csv("papers.csv")
    for p in papers:
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


def timeline_svg(papers, lang, y0=1942, y1=2026, width=1000, lane_h=42, chapter_links=True):
    lanes = [l for l, _ in LANES]
    left, right, top = 150, width - 20, 36
    h = top + lane_h * len(lanes) + 30
    out = [f'<svg viewBox="0 0 {width} {h}" role="img" aria-label="timeline">']
    # era bands
    for i, e in enumerate(ERAS):
        a, b = C.ERA_SPAN[e]
        xa, xb = x_of(a, y0, y1, left, right, KNEE), x_of(min(b, y1), y0, y1, left, right, KNEE)
        out.append(f'<rect class="band{" alt" if i % 2 else ""}" x="{xa:.1f}" y="{top}" width="{xb - xa:.1f}" height="{lane_h * len(lanes)}"/>')
        out.append(f'<text x="{(xa + xb) / 2:.1f}" y="{top - (8 if i % 2 == 0 else 20)}" text-anchor="middle" font-size="10">{esc(C.ERA_SHORT[lang][e])}</text>')
    for i, lane in enumerate(lanes):
        y = top + i * lane_h
        out.append(f'<line class="grid" x1="{left}" x2="{right}" y1="{y + lane_h}" y2="{y + lane_h}"/>')
        out.append(f'<text x="{left - 8}" y="{y + lane_h / 2 + 4}" text-anchor="end">{esc(T[lang]["theme_names"][lane])}</text>')
    for yr in list(range(1950, 2011, 10)) + list(range(2012, 2027, 2)):
        x = x_of(yr, y0, y1, left, right, KNEE)
        out.append(f'<line class="ax" x1="{x:.1f}" x2="{x:.1f}" y1="{top}" y2="{top + lane_h * len(lanes)}"/><text x="{x:.1f}" y="{h - 8}" text-anchor="middle">{yr}</text>')
    # dots with slight vertical jitter by index within lane-year
    seen = defaultdict(int)
    for p in papers:
        li = lanes.index(p["lane"])
        slot = seen[(p["lane"], int(p["yearf"]))]; seen[(p["lane"], int(p["yearf"]))] += 1
        x = x_of(p["yearf"], y0, y1, left, right, KNEE)
        y = top + li * lane_h + lane_h / 2 + ((slot % 3) - 1) * 9
        href = f"chapters/{p['era']}.html#{p['key']}" if chapter_links else f"#{p['key']}"
        meta = f"{esc(p['authors_short'])} · {esc(p['first_public_date'][:4])}"
        out.append(f'<g class="dot" data-k="{p["key"]}" data-t="{esc(p["title"])}" data-m="{meta}" data-w="{esc(card_text(p, lang))}" data-href="{href}"><circle cx="{x:.1f}" cy="{y:.1f}" r="4.2" fill="var(--s{(li % 4) + 1})" stroke="var(--card)" stroke-width="1"/></g>')
    out.append("</svg>")
    return "\n".join(out)


def lineage_svg(papers, edges, lang, width=1000, lane_h=70, href_prefix=""):
    if not papers:
        return ""
    lanes = [l for l, _ in LANES if any(p["lane"] == l for p in papers)]
    y0 = math.floor(min(p["yearf"] for p in papers)) - 1
    y1 = math.ceil(max(p["yearf"] for p in papers)) + 1
    left, right, top = 150, width - 20, 16
    h = top + lane_h * len(lanes) + 30
    pos = {}
    seen = defaultdict(int)
    for p in papers:
        li = lanes.index(p["lane"])
        slot = seen[(p["lane"], round(p["yearf"] * 2))]; seen[(p["lane"], round(p["yearf"] * 2))] += 1
        x = x_of(p["yearf"], y0, y1, left, right)
        y = top + li * lane_h + lane_h / 2 + ((slot % 4) - 1.5) * 13
        pos[p["key"]] = (x, y)
    out = [f'<svg viewBox="0 0 {width} {h}" role="img" aria-label="lineage">']
    for i, lane in enumerate(lanes):
        y = top + i * lane_h
        out.append(f'<line class="grid" x1="{left}" x2="{right}" y1="{y + lane_h}" y2="{y + lane_h}"/>')
        out.append(f'<text x="{left - 8}" y="{y + lane_h / 2 + 4}" text-anchor="end">{esc(T[lang]["theme_names"][lane])}</text>')
    step = 1 if y1 - y0 <= 12 else (5 if y1 - y0 <= 50 else 10)
    for yr in range(int(math.ceil(y0 / step) * step), int(y1) + 1, step):
        x = x_of(yr, y0, y1, left, right)
        out.append(f'<line class="ax" x1="{x:.1f}" x2="{x:.1f}" y1="{top}" y2="{top + lane_h * len(lanes)}"/><text x="{x:.1f}" y="{h - 8}" text-anchor="middle">{yr}</text>')
    for e in edges:
        if e["src"] in pos and e["dst"] in pos:
            (x2, y2), (x1, y1_) = pos[e["src"]], pos[e["dst"]]  # dst (older) -> src (newer)
            cx = (x1 + x2) / 2
            out.append(f'<path class="edge{" notion" if e["kind"] == "notion" else ""}" data-s="{e["src"]}" data-d="{e["dst"]}" d="M{x1:.1f},{y1_:.1f} C{cx:.1f},{y1_:.1f} {cx:.1f},{y2:.1f} {x2:.1f},{y2:.1f}"/>')
    for p in papers:
        x, y = pos[p["key"]]
        li = lanes.index(p["lane"])
        meta = f"{esc(p['authors_short'])} · {esc(p['first_public_date'][:4])}"
        out.append(f'<g class="dot" data-k="{p["key"]}" data-t="{esc(p["title"])}" data-m="{meta}" data-w="{esc(card_text(p, lang))}" data-href="{href_prefix}{p["era"]}.html#{p["key"]}"><circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="var(--s{(li % 4) + 1})" stroke="var(--card)" stroke-width="1"/></g>')
    out.append("</svg>")
    return "\n".join(out)


def line_svg(series, lang, ylabel="", width=900, height=300, y0=None, y1=None, logy=False, xr=None):
    """series: list of (label, [(x,y)], color_idx, dashed)"""
    pts = [p for _, ps, _, _ in series for p in ps]
    if not pts:
        return ""
    xa = xr[0] if xr else min(p[0] for p in pts); xb = xr[1] if xr else max(p[0] for p in pts)
    ya = y0 if y0 is not None else 0; yb = y1 if y1 is not None else max(p[1] for p in pts) * 1.05
    left, right, top, bot = 60, width - 20, 16, height - 30
    def X(x): return left + (x - xa) / (xb - xa) * (right - left)
    def Y(y):
        if logy:
            return bot - (math.log10(max(y, 1)) - math.log10(max(ya, 1))) / (math.log10(yb) - math.log10(max(ya, 1))) * (bot - top)
        return bot - (y - ya) / (yb - ya) * (bot - top)
    out = [f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="line chart">']
    ticks = [10 ** k for k in range(int(math.log10(max(ya, 1))), int(math.log10(yb)) + 1)] if logy else [ya + (yb - ya) * i / 4 for i in range(5)]
    for tv in ticks:
        out.append(f'<line class="grid" x1="{left}" x2="{right}" y1="{Y(tv):.1f}" y2="{Y(tv):.1f}"/><text x="{left - 6}" y="{Y(tv) + 4:.1f}" text-anchor="end">{tv:g}</text>')
    step = 5 if xb - xa <= 50 else 10
    for xv in range(int(math.ceil(xa / step) * step), int(xb) + 1, step):
        out.append(f'<text x="{X(xv):.1f}" y="{height - 8}" text-anchor="middle">{xv}</text>')
    out.append(f'<line class="ax" x1="{left}" x2="{right}" y1="{bot}" y2="{bot}"/>')
    for label, ps, ci, dashed in series:
        ps = sorted(ps)
        d = " ".join(f"{'M' if i == 0 else 'L'}{X(x):.1f},{Y(y):.1f}" for i, (x, y) in enumerate(ps))
        out.append(f'<path d="{d}" fill="none" stroke="var(--s{ci})" stroke-width="2"{" stroke-dasharray=\"4 3\"" if dashed else ""}/>')
        for x, y in ps:
            out.append(f'<circle cx="{X(x):.1f}" cy="{Y(y):.1f}" r="2.2" fill="var(--s{ci})"><title>{esc(label)} {x}: {y:g}</title></circle>')
    if ylabel:
        out.append(f'<text x="{left}" y="{top - 4}" font-size="10">{esc(ylabel)}</text>')
    out.append("</svg>")
    legend = '<div class="legend">' + "".join(f'<span style="--c:var(--s{ci})">{esc(l)}</span>' for l, _, ci, _ in series) + "</div>"
    return legend + "\n".join(out)


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
    body = f"""<div class="hero"><h1>{t['site']}</h1><p class="lead">{esc(t['tagline'])}</p>{glance(lang, C.HOME_KEY[lang])}</div>
<div class="stats"><span class="stat"><span class="n">{len(papers)}</span><small>{esc(C.STAT[lang]['papers'])}</small></span><span class="stat"><span class="n">{n_edges}</span><small>{esc(C.STAT[lang]['edges'])}</small></span><span class="stat"><span class="n">{papers[0]['first_public_date'][:4]}–{papers[-1]['first_public_date'][:4]}</span><small>{esc(C.STAT[lang]['span'])}</small></span></div>
<figure class="tl-wide">{timeline_svg(papers, lang)}<figcaption>{esc(t['timeline_cap'])}</figcaption></figure>
<div class="tl-list"><ol>{tl_list}</ol></div>
<h2>{t['nav_chapters']}</h2><div class="cards">{eras_html}</div>
<div class="prose">{C.HOME_INTRO[lang]}</div>"""
    (out / "index.html").write_text(page(lang, t["site"], body, 1, active="home"), encoding="utf-8")
    # chapters index + pages
    body = f"<h1>{t['nav_chapters']}</h1><div class=\"cards\">{eras_html.replace('href=\"chapters/', 'href=\"')}</div>"
    (out / "chapters/index.html").write_text(page(lang, t["nav_chapters"], body, 2, active="chapters"), encoding="utf-8")
    for e in ERAS:
        ps = [p for p in papers if p["era"] == e]
        es = [x for x in edges if x["src"] in {p["key"] for p in ps} and x["dst"] in {p["key"] for p in ps}]
        boxes = "".join(C.BOXES[lang].get(e, []))
        body = f"""<div class="eyebrow"><span class="tag">{esc(C.ERA_SHORT[lang][e])}</span></div><h1>{esc(C.ERA_TITLE[lang][e])}</h1><p class="lead">{esc(C.ERA_LEAD[lang][e])}</p>
{glance(lang, C.ERA_KEY[lang][e])}
<div class="prose">{C.ERA_TEXT[lang][e]}</div>
{boxes}
<h2>{t['nav_lineage']}</h2><figure>{lineage_svg(ps, es, lang)}<figcaption>{esc(t['lineage_cap'])}</figcaption></figure>
<h2>{t['nav_papers']} ({len(ps)})</h2>{''.join(paper_block(p, lang, edges, by_key) for p in ps)}"""
        (out / f"chapters/{e}.html").write_text(page(lang, C.ERA_TITLE[lang][e], body, 2, active="chapters"), encoding="utf-8")
    # lineage pages by lane
    lane_cards = "".join(f'<a class="card" href="{l}.html"><b>{esc(t["theme_names"][l])}</b><small>{sum(1 for p in papers if p["lane"] == l)} {t["papers"]}</small></a>' for l, _ in LANES)
    body = f"<h1>{t['nav_lineage']}</h1><p class=\"lead\">{esc(C.LINEAGE_LEAD[lang])}</p><div class=\"cards\">{lane_cards}</div>"
    (out / "lineage/index.html").write_text(page(lang, t["nav_lineage"], body, 2, active="lineage"), encoding="utf-8")
    for l, _ in LANES:
        ps = [p for p in papers if p["lane"] == l]
        ks = {p["key"] for p in ps}
        es = [x for x in edges if x["src"] in ks and x["dst"] in ks]
        rows = "".join(f'<tr><td class="nw">{esc(p["first_public_date"][:4])}</td><td>{esc(p["authors_short"])}</td><td><a href="../chapters/{p["era"]}.html#{p["key"]}">{esc(p["title"])}</a></td><td>{esc(C.ERA_SHORT[lang][p["era"]])}</td></tr>' for p in ps)
        body = f"""<h1>{esc(t['theme_names'][l])}</h1><p class="lead">{esc(C.LANE_LEAD[lang].get(l, ''))}</p>
<figure>{lineage_svg(ps, es, lang, href_prefix='../chapters/')}<figcaption>{esc(t['lineage_cap'])}</figcaption></figure>
<div class="wrap"><table class="sort"><thead><tr><th>{t['year']}</th><th>{t['author']}</th><th>{t['title']}</th><th>{t['chapter']}</th></tr></thead><tbody>{rows}</tbody></table></div>"""
        (out / f"lineage/{l}.html").write_text(page(lang, t["theme_names"][l], body, 2, active="lineage"), encoding="utf-8")
    # winters
    (out / "winters.html").write_text(page(lang, t["nav_winters"], winters_body(lang), 1, active="winters"), encoding="utf-8")
    # papers list
    rows = []
    for p in papers:
        url, kind = primary_link(p)
        rows.append(f'<tr><td class="nw" data-v="{p["yearf"]:.2f}">{esc(p["first_public_date"])}</td><td>{esc(p["authors_short"])}</td><td><a href="chapters/{p["era"]}.html#{p["key"]}">{esc(p["title"])}</a></td><td class="nw">{esc(p["venue_short"])}</td><td class="nw"><a href="{esc(url)}">{kind}</a></td><td class="nw">{esc(C.ERA_SHORT[lang][p["era"]])}</td><td class="nw">{esc(t["theme_names"][p["lane"]])}</td></tr>')
    body = f"""<h1>{t['nav_papers']}</h1><p class="lead">{esc(C.PAPERS_LEAD[lang])}</p>
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
    body = f"""<h1>{t['nav_winters']}</h1><p class="lead">{esc(C.WINTER_LEAD[lang])}</p>{glance(lang, C.WINTER_KEY[lang])}
<div class="prose">{C.WINTER_TEXT[lang]['intro']}</div>
<h2>{esc(C.WINTER_TEXT[lang]['h1'])}</h2><figure>{line_svg(s1, lang, ylabel=C.WINTER_TEXT[lang]['y1'], xr=(1960, 2024))}<figcaption>{esc(C.WINTER_TEXT[lang]['cap1'])}</figcaption></figure>
<div class="prose">{C.WINTER_TEXT[lang]['t1']}</div>
<h2>{esc(C.WINTER_TEXT[lang]['h2'])}</h2><figure>{line_svg(s2, lang, ylabel=C.WINTER_TEXT[lang]['y2'], xr=(1984, 2025))}<figcaption>{esc(C.WINTER_TEXT[lang]['cap2'])}</figcaption></figure>
<div class="prose">{C.WINTER_TEXT[lang]['t2']}</div>
<h2>{esc(C.WINTER_TEXT[lang]['h3'])}</h2><figure>{line_svg(s3, lang, ylabel=C.WINTER_TEXT[lang]['y3'], logy=True, y0=50, y1=6000, xr=(1987, 2024))}<figcaption>{esc(C.WINTER_TEXT[lang]['cap3'])}</figcaption></figure>
<div class="prose">{C.WINTER_TEXT[lang]['t3']}</div>
<h2>{esc(C.WINTER_TEXT[lang]['h4'])}</h2><div class="prose">{C.WINTER_TEXT[lang]['t4']}</div>
<p class="files"><a href="../data/winter_title_phrases.csv">winter_title_phrases.csv</a> <a href="../data/winter_attendance.csv">winter_attendance.csv</a> <a href="../data/winter_neurips_accepted.csv">winter_neurips_accepted.csv</a></p>"""
    return body


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
