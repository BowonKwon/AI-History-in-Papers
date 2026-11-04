"""Merge reading outputs (data/derived/reading/batch*.csv) with the selection, candidate metadata
and OpenAlex records into data/derived/papers.csv and data/derived/edges.csv.

Translations (key_sentence_ko, what_changed_ko) and venue_short come from data/derived/cards_ko.csv
(key, key_sentence_ko, what_changed_ko, venue_short, authors_short) written by hand in stage 2;
missing rows leave the fields empty so the site can still build.
Edges: OA (edges_oa.csv) + original (refs_to_candidates from reading) + notion (docs/notion_edges.csv).
"""
import csv, json, re, glob
from collections import OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / "data/derived"
OA_CHECK_DATE = "2026-11-03"


def read(p):
    p = Path(p)
    return list(csv.DictReader(open(p, encoding="utf-8-sig"))) if p.exists() else []


US = [("behaviour", "behavior"), ("Behaviour", "Behavior"), ("modelling", "modeling"), ("modelled", "modeled"), ("analysed", "analyzed"), ("analyse", "analyze"),
      ("optimisation", "optimization"), ("optimise", "optimize"), ("recognised", "recognized"), ("organised", "organized"), ("labelled", "labeled"), ("labelling", "labeling"),
      ("colour", "color"), ("centre", "center"), ("favour", "favor"), ("catalogue", "catalog"), ("programme", "program"), ("defence", "defense"), ("licence", "license"), ("summarises", "summarizes"), ("synthesises", "synthesizes"), ("generalises", "generalizes"), ("utilise", "utilize")]


def us_spelling(t):
    """American spelling in our own summaries (quotations are left as printed)."""
    for a, b in US:
        t = t.replace(a, b)
    return t


def short_authors(authors, first):
    a = (authors or "").strip()
    if not a:
        return first
    parts = re.split(r",\s*|\s+and\s+|\s*&\s*|;\s*", a)
    parts = [x for x in parts if x and not re.fullmatch(r"[A-Z]\.?(\s?[A-Z]\.?)*", x)]
    def surname(s):
        s = s.strip()
        toks = s.replace(".", ". ").split()
        return toks[-1] if toks else s
    if len(parts) == 1:
        return surname(parts[0])
    if len(parts) == 2:
        return f"{surname(parts[0])} & {surname(parts[1])}"
    return f"{surname(parts[0])} et al."


def main():
    cand = {r["key"]: r for r in read(D / "candidates_v0.csv")}
    sel = {r["key"]: r for r in read(D / "selection_v1.csv")}
    ko = {r["key"]: r for r in read(D / "cards_ko.csv")}
    # docs/cards_ko.txt: blocks "## key / Q: translation / W: Korean what-changed"
    kt = ROOT / "docs/cards_ko.txt"
    if kt.exists():
        cur = None
        for line in kt.read_text(encoding="utf-8").splitlines():
            if line.startswith("## "):
                cur = line[3:].strip(); ko.setdefault(cur, {})
            elif cur and line.startswith("Q: "):
                ko[cur]["key_sentence_ko"] = line[3:].strip()
            elif cur and line.startswith("W: "):
                ko[cur]["what_changed_ko"] = line[3:].strip()
    reading = {}
    for f in sorted(glob.glob(str(D / "reading" / "batch*.csv"))):
        for r in read(f):
            reading[r["key"]] = r
    papers, edges = [], []
    for e in read(D / "edges_oa.csv"):
        edges.append({"src": e["src"], "dst": e["dst"], "kind": "OA", "evidence": f"OpenAlex referenced_works ({OA_CHECK_DATE})"})
    for k, s in sel.items():
        if s["selected"] != "yes":
            continue
        c = cand[k]; r = reading.get(k, {}); kk = ko.get(k, {})
        oid = c.get("oa_id", "")
        oa = {}
        f = ROOT / "data/raw/api/oa" / f"{oid}.json"
        if oid and f.exists():
            oa = json.loads(f.read_text(encoding="utf-8"))
        hint = c["hint"]
        doi = hint[4:] if hint.startswith("doi:") else (c.get("oa_doi", "") if not c.get("oa_doi", "").startswith("10.48550") else "")
        arxiv = hint[6:] if hint.startswith("arxiv:") else ""
        src_used = (r.get("source_used", "") or "").split()[0] if (r.get("source_used") or "").strip() else ""
        url = src_used if (src_used.startswith("http") and not doi and not arxiv) else ""
        if not url and not doi and not arxiv:
            url = c.get("oa_doi", "") and f"https://doi.org/{c['oa_doi']}" or ""
        fpd = r.get("first_public_date", "") or c["year"]
        authors = ", ".join(a["author"]["display_name"] for a in (oa.get("authorships") or [])[:6]) if oa else c["author"]
        if oa and len(oa.get("authorships") or []) > 6:
            authors += " et al."
        papers.append(OrderedDict([
            ("key", k), ("era", c["era"]), ("theme", c["theme"]),
            ("first_public_date", fpd), ("first_public_type", r.get("first_public_type", "")), ("other_dates", r.get("other_dates", "")),
            ("record_year", c.get("oa_year", "")),
            ("authors", authors), ("authors_short", kk.get("authors_short") or short_authors(authors, c["author"])),
            ("title", c["title"]), ("venue", r.get("venue_full", "") or c.get("oa_venue", "")), ("venue_short", kk.get("venue_short", "") or (r.get("venue_full", "") or c.get("oa_venue", ""))[:40]),
            ("pages", r.get("pages", "")), ("doi", doi), ("arxiv", arxiv), ("url", url), ("version_used", r.get("version_used", "")),
            ("key_sentence", r.get("key_sentence", "")), ("key_sentence_cite", r.get("key_sentence_page", "")), ("key_sentence_ko", kk.get("key_sentence_ko", "")),
            ("what_changed_en", us_spelling(r.get("what_changed", ""))), ("what_changed_ko", kk.get("what_changed_ko", "")),
            ("openalex_id", oid), ("oa_cited_by", oa.get("cited_by_count", "") if oa else ""), ("oa_checked", OA_CHECK_DATE if oa else ""),
            ("rules", s["rules"]), ("source_status", r.get("status", "")),
        ]))
        for dst in [x.strip() for x in (r.get("refs_to_candidates") or "").split(";") if x.strip()]:
            if dst in cand and dst != k:
                edges.append({"src": k, "dst": dst, "kind": "original", "evidence": f"reference list of {k} ({r.get('version_used', '')})"})
    # hand overrides (docs/card_overrides.csv: key,field,value,reason) — e.g. a wrong DOI in the candidate list
    for o in read(ROOT / "docs/card_overrides.csv"):
        for p in papers:
            if p["key"] == o["key"] and o["field"] in p:
                p[o["field"]] = o["value"]
    for e in read(ROOT / "docs/notion_edges.csv"):
        edges.append({"src": e["src"], "dst": e["dst"], "kind": "notion", "evidence": e["evidence"]})
    # de-duplicate: OA and original for same pair both kept? keep one row per (src,dst) preferring OA
    seen, dedup = {}, []
    for e in edges:
        key = (e["src"], e["dst"])
        if key in seen:
            if e["kind"] == "original" and seen[key]["kind"] == "OA":
                seen[key]["evidence"] += "; also in reference list"
            continue
        seen[key] = e; dedup.append(e)
    papers.sort(key=lambda p: (p["first_public_date"][:4], p["key"]))
    with open(D / "papers.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(papers[0].keys())); w.writeheader(); w.writerows(papers)
    with open(D / "edges.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["src", "dst", "kind", "evidence"]); w.writeheader(); w.writerows(dedup)
    print("papers", len(papers), "read", sum(1 for p in papers if p["source_status"]), "edges", len(dedup),
          {k: sum(1 for e in dedup if e["kind"] == k) for k in ("OA", "original", "notion")})


if __name__ == "__main__":
    main()
