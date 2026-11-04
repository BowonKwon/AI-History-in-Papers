"""Candidate list -> OpenAlex / Crossref / arXiv bibliographic check.
No email or personal data is sent (no mailto=). Polite delays."""
import csv, json, re, sys, time, unicodedata, difflib, urllib.parse, urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).parent
UA = {"User-Agent": "ai-history-bibcheck/0.1 (research script)"}
CACHE = HERE / "cache"; CACHE.mkdir(exist_ok=True)


def get(url, kind="json", delay=0.15):
    import hashlib; key = hashlib.sha1(url.encode()).hexdigest()
    f = CACHE / (key + (".json" if kind == "json" else ".xml"))
    if f.exists():
        t = f.read_text(encoding="utf-8")
        return json.loads(t) if kind == "json" else t
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=40) as r:
                t = r.read().decode("utf-8")
            f.write_text(t, encoding="utf-8")
            time.sleep(delay)
            return json.loads(t) if kind == "json" else t
        except urllib.error.HTTPError as e:
            print("HTTP", e.code, url[:120], file=sys.stderr, flush=True)
            if e.code == 404:
                f.write_text("null" if kind == "json" else "", encoding="utf-8")
                return None if kind == "json" else ""
            if e.code == 400:
                return None if kind == "json" else ""
            time.sleep(12 * (attempt + 1))
        except Exception:
            time.sleep(12 * (attempt + 1))
    return None


def norm(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9 ]+", " ", s).split()


def sim(a, b):
    return difflib.SequenceMatcher(None, " ".join(norm(a)), " ".join(norm(b))).ratio()


def oa_summary(w):
    if not w:
        return {}
    auths = w.get("authorships") or []
    fa = auths[0]["author"]["display_name"] if auths else ""
    src = ((w.get("primary_location") or {}).get("source") or {}) or {}
    return {
        "oa_id": (w.get("id") or "").rsplit("/", 1)[-1],
        "oa_title": w.get("display_name") or "",
        "oa_year": w.get("publication_year"),
        "oa_date": w.get("publication_date"),
        "oa_first_author": fa,
        "oa_venue": src.get("display_name") or "",
        "oa_type": w.get("type") or "",
        "oa_cited_by": w.get("cited_by_count"),
        "oa_doi": (w.get("doi") or "").replace("https://doi.org/", ""),
        "oa_n_refs": len(w.get("referenced_works") or []),
    }


def author_ok(row, oa):
    sur = norm(row["author"])
    fa = norm(oa.get("oa_first_author", ""))
    return bool(sur) and bool(fa) and sur[-1] in fa


def oa_search(row):
    q = urllib.parse.quote(re.sub(r"[,:|!?()\[\]\"']+", " ", row["title"])[:200])
    url = f"https://api.openalex.org/works?filter=title.search:{q}&per-page=10&select=id,display_name,publication_year,publication_date,authorships,primary_location,type,cited_by_count,doi,referenced_works"
    d = get(url)
    res = (d or {}).get("results") or []
    best, bscore = None, 0
    for w in res:
        s = oa_summary(w)
        sc = sim(row["title"], s["oa_title"])
        if author_ok(row, s):
            sc += 0.2
        if s["oa_year"] and abs(int(s["oa_year"]) - int(row["year"])) <= 2:
            sc += 0.1
        # prefer more-cited (merged canonical) when ties
        sc += min((s["oa_cited_by"] or 0), 100000) / 1e7
        if sc > bscore:
            best, bscore = s, sc
    return best or {}


def crossref(doi):
    d = get("https://api.crossref.org/works/" + urllib.parse.quote(doi), delay=0.3)
    if not d:
        return {}
    m = d.get("message", {})
    yr = None
    for k in ("published-print", "published-online", "issued"):
        dp = (m.get(k) or {}).get("date-parts")
        if dp and dp[0] and dp[0][0]:
            yr = dp[0][0]; break
    return {"cr_title": (m.get("title") or [""])[0], "cr_year": yr,
            "cr_container": (m.get("container-title") or [""])[0],
            "cr_volume": m.get("volume") or "", "cr_page": m.get("page") or ""}


def arxiv(aid):
    t = get(f"http://export.arxiv.org/api/query?id_list={aid}", kind="xml", delay=5)
    if not t:
        return {}
    ns = {"a": "http://www.w3.org/2005/Atom"}
    try:
        root = ET.fromstring(t)
    except ET.ParseError:
        return {}
    e = root.find("a:entry", ns)
    if e is None:
        return {}
    title = re.sub(r"\s+", " ", (e.findtext("a:title", "", ns) or "")).strip()
    pub = (e.findtext("a:published", "", ns) or "")[:10]
    au = [a.findtext("a:name", "", ns) for a in e.findall("a:author", ns)]
    return {"ax_title": title, "ax_v1": pub, "ax_first_author": au[0] if au else "", "ax_n_authors": len(au)}


def main():
    rows = list(csv.DictReader(open(HERE / "cand.psv", encoding="utf-8"), delimiter="|"))
    out = []
    for i, r in enumerate(rows):
        hint = r["hint"].strip()
        rec = dict(r)
        oa = {}
        if hint.startswith("doi:"):
            doi = hint[4:]
            oa = oa_summary(get("https://api.openalex.org/works/doi:" + urllib.parse.quote(doi)))
            rec.update(crossref(doi))
        if hint.startswith("arxiv:"):
            rec.update(arxiv(hint[6:]))
            oa = oa_summary(get("https://api.openalex.org/works/doi:10.48550/arxiv." + hint[6:]))
        if not oa:
            oa = oa_search(r)
        rec.update(oa)
        rec["title_sim"] = round(sim(r["title"], oa.get("oa_title", "")), 2) if oa else 0
        rec["author_ok"] = author_ok(r, oa) if oa else False
        flags = []
        if not oa:
            flags.append("OA없음")
        else:
            if rec["title_sim"] < 0.85: flags.append("제목차")
            if not rec["author_ok"]: flags.append("저자차")
            if oa.get("oa_year") and int(oa["oa_year"]) != int(r["year"]): flags.append(f"연도차({oa['oa_year']})")
        if "cr_title" in rec and rec.get("cr_title") and sim(r["title"], rec["cr_title"]) < 0.85: flags.append("CR제목차")
        if hint.startswith("doi:") and not rec.get("cr_title"): flags.append("CR없음")
        if hint.startswith("arxiv:"):
            if not rec.get("ax_title"): flags.append("arXiv없음")
            elif sim(r["title"], rec["ax_title"]) < 0.85: flags.append("arXiv제목차")
        rec["flags"] = ";".join(flags)
        out.append(rec)
        print(i, r["key"], rec["flags"] or "ok", flush=True)
    keys = []
    for o in out:
        for k in o:
            if k not in keys: keys.append(k)
    with open(HERE / "verified.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys); w.writeheader(); w.writerows(out)


if __name__ == "__main__":
    main()
