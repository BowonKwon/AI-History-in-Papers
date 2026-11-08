"""Build citation edges among candidates from OpenAlex referenced_works (kind=OA),
and an OA-availability table (best_oa_location pdf/landing url, license) for downloading
originals. Outputs data/derived/edges_oa.csv and data/derived/oa_access.csv"""
import csv, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OA = ROOT / "data/raw/api/oa"


def main():
    rows = list(csv.DictReader(open(ROOT / "data/derived/candidates_v0.csv", encoding="utf-8-sig")))
    key_by_id = {r["oa_id"]: r["key"] for r in rows if r.get("oa_id")}
    # second OpenAlex records of the same work (e.g. arXiv and journal), added 2026-11-07
    al = ROOT / "method/oa_aliases.csv"
    if al.exists():
        for a in csv.DictReader(open(al, encoding="utf-8-sig")):
            key_by_id.setdefault(a["oa_id"], a["key"])
    edges, access = [], []
    for r in rows:
        oid = r.get("oa_id")
        if not oid:
            access.append({"key": r["key"], "oa_id": "", "is_oa": "", "pdf_url": "", "landing": "", "license": "", "n_refs": ""})
            continue
        f = OA / f"{oid}.json"
        if not f.exists():
            continue
        d = json.loads(f.read_text(encoding="utf-8"))
        refs = [x.rsplit("/", 1)[-1] for x in d.get("referenced_works") or []]
        for t in refs:
            if t in key_by_id and key_by_id[t] != r["key"]:
                edges.append({"src": r["key"], "dst": key_by_id[t], "kind": "OA", "src_oa": oid, "dst_oa": t})
        b = d.get("best_oa_location") or {}
        oa = d.get("open_access") or {}
        access.append({"key": r["key"], "oa_id": oid, "is_oa": oa.get("is_oa"), "pdf_url": b.get("pdf_url") or "",
                       "landing": b.get("landing_page_url") or "", "license": b.get("license") or "", "n_refs": len(refs)})
    with open(ROOT / "data/derived/edges_oa.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["src", "dst", "kind", "src_oa", "dst_oa"]); w.writeheader(); w.writerows(edges)
    with open(ROOT / "data/derived/oa_access.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(access[0].keys())); w.writeheader(); w.writerows(access)
    print("edges", len(edges), "nodes with out-edges", len({e["src"] for e in edges}), "with in-edges", len({e["dst"] for e in edges}))
    print("oa pdf urls", sum(1 for a in access if a["pdf_url"]), "is_oa", sum(1 for a in access if a["is_oa"] is True))


if __name__ == "__main__":
    main()
