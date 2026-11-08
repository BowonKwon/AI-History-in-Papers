"""Provisional selection under method/selection-criteria.md.
R1 from textbook_matches.csv (>=2 of T2..T6; T1 pending), R3 from a hand list of award-named
original publications (method/awards_named_works.csv), R4 for 2021+ with a peer-reviewed venue
in OpenAlex primary_location (type journal/conference, not repository) or a vault-verified entry,
R2 iteratively: >=3 already-selected papers cite it (edges_oa.csv + the reference lists read for the
cards, i.e. refs_to_candidates in data/derived/reading/batch*.csv, + edges_manual.csv if present).
The reading edges were added 2026-11-07: before that R2 and cited_by_selected used only the
edges_manual.csv snapshot, which had not been refreshed after the 1.1 reading (36 reference-list
edges missing), so the stored counts lagged edges.csv.
The 1.1 pool widening (method/selection-criteria.md, 2026-11-07) is checked here against the current textbook
comparison: a work listed in method/pool-1.1-added.csv stays in the candidate pool only if it is cited in OpenAlex
by at least three papers selected in 1.0.1 (the recorded oa_citing_selected) and matched in at least three
reference works now (textbook_matches.csv, after the hand overrides). Works that fail leave the pool and are not
written to selection_v1.csv (added 2026-11-07 after a hand check removed a T6 hit for Jelinek 1976).
Output data/derived/selection_v1.csv with the rule(s) that admitted each paper."""
import csv, glob, json, collections
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / "data/derived"


def read(p):
    p = Path(p)
    return list(csv.DictReader(open(p, encoding="utf-8-sig"))) if p.exists() else []


def main():
    cand = {r["key"]: r for r in read(D / "candidates_v0.csv")}
    tb = {r["key"]: r for r in read(D / "textbook_matches.csv")}
    out_of_pool = []
    for w in read(ROOT / "method/pool-1.1-added.csv"):
        k = w["key"]
        n_tb = int(tb.get(k, {}).get("n_hits") or 0)
        ok = int(w["oa_citing_selected"]) >= 3 and n_tb >= 3
        if (w["meets_rule"] == "yes") != ok or int(w["n_textbooks"]) != n_tb:
            print("POOL RECORD DIFFERS:", k, "recorded", w["n_textbooks"], w["meets_rule"], "now", n_tb, ok)
        if not ok:
            cand.pop(k, None); out_of_pool.append(k)
    print("left the 1.1 pool (widening condition not met):", out_of_pool)
    awards = {r["key"]: r for r in read(ROOT / "method/awards_named_works.csv")}
    vault = {r["key"] for r in read(ROOT / "method/vault_verified_recent.csv")}
    edges = read(D / "edges_oa.csv") + read(D / "edges_manual.csv")
    reading = {}
    for f in sorted(glob.glob(str(D / "reading" / "batch*.csv"))):  # later batch wins per key, as in merge_cards
        for r in read(f):
            reading[r["key"]] = r
    for k, r in reading.items():
        for dst in [x.strip() for x in (r.get("refs_to_candidates") or "").split(";") if x.strip()]:
            if dst in cand and dst != k:
                edges.append({"src": k, "dst": dst})
    cited_by = collections.defaultdict(set)
    for e in edges:
        cited_by[e["dst"]].add(e["src"])
    manual = {r["key"] for r in read(ROOT / "method/manual_r1.csv")}  # hand-confirmed two-textbook hits the matcher missed
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
    # method/hold.csv: papers that meet a rule but whose original text could not be read (added 2026-11-07, 1.1)
    hold = {r["key"] for r in read(ROOT / "method/hold.csv")}
    for k in hold:
        rules.pop(k, None)
    selected = {k for k in rules}
    changed = True
    while changed:
        changed = False
        for k in cand:
            if k in selected or k in hold:
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
