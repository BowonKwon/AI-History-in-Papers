"""Provisional selection under docs/selection-criteria.md.
R1 from textbook_matches.csv (>=2 of T2..T6; T1 pending), R3 from a hand list of award-named
original publications (docs/awards_named_works.csv), R4 for 2021+ with a peer-reviewed venue
in OpenAlex primary_location (type journal/conference, not repository) or a vault-verified entry,
R2 iteratively: >=3 already-selected papers cite it (edges_oa.csv + edges_manual.csv if present).
Output data/derived/selection_v1.csv with the rule(s) that admitted each paper."""
import csv, json, collections
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / "data/derived"


def read(p):
    p = Path(p)
    return list(csv.DictReader(open(p, encoding="utf-8-sig"))) if p.exists() else []


def main():
    cand = {r["key"]: r for r in read(D / "candidates_v0.csv")}
    tb = {r["key"]: r for r in read(D / "textbook_matches.csv")}
    awards = {r["key"]: r for r in read(ROOT / "docs/awards_named_works.csv")}
    vault = {r["key"] for r in read(ROOT / "docs/vault_verified_recent.csv")}
    edges = read(D / "edges_oa.csv") + read(D / "edges_manual.csv")
    cited_by = collections.defaultdict(set)
    for e in edges:
        cited_by[e["dst"]].add(e["src"])
    manual = {r["key"] for r in read(ROOT / "docs/manual_r1.csv")}  # hand-confirmed two-textbook hits the matcher missed
    rules = collections.defaultdict(list)
    for k, r in cand.items():
        if tb.get(k, {}).get("R1") == "pass" or k in manual:
            rules[k].append("R1")
        if k in awards:
            rules[k].append("R3")
        if int(r["year"]) >= 2021:
            venue_ok = False
            oid = r.get("oa_id")
            f = ROOT / "data/raw/api/oa" / f"{oid}.json"
            if oid and f.exists():
                d = json.loads(f.read_text(encoding="utf-8"))
                src = ((d.get("primary_location") or {}).get("source") or {}) or {}
                venue_ok = src.get("type") in ("journal", "conference") and "arxiv" not in (src.get("display_name") or "").lower()
            if venue_ok or k in vault:
                rules[k].append("R4")
    selected = {k for k in rules}
    changed = True
    while changed:
        changed = False
        for k in cand:
            if k in selected:
                continue
            n = len(cited_by[k] & selected)
            if n >= 3:
                rules[k].append(f"R2({n})"); selected.add(k); changed = True
    out = []
    for k, r in cand.items():
        out.append({"key": k, "year": r["year"], "author": r["author"], "title": r["title"], "era": r["era"], "theme": r["theme"],
                    "rules": "+".join(rules.get(k, [])), "selected": "yes" if k in selected else "no",
                    "tb_hits": tb.get(k, {}).get("n_hits", ""), "cited_by_selected": len(cited_by[k] & selected)})
    with open(D / "selection_v1.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0].keys())); w.writeheader(); w.writerows(out)
    c = collections.Counter(o["selected"] for o in out)
    print(dict(c))
    print("by rule:", collections.Counter(r.split("(")[0] for v in rules.values() for r in v))
    print("by era:", {e: sum(1 for o in out if o["era"] == e and o["selected"] == "yes") for e in sorted({o["era"] for o in out})})
    print("not selected:", [o["key"] for o in out if o["selected"] == "no"])


if __name__ == "__main__":
    main()
