"""awards.csv: Turing Award laureates (Wikidata SPARQL, CC0) and Nobel Prizes 2024 (Nobel API, CC0)
that name a paper in the list, joined through method/awards_named_works.csv (hand-checked mapping)."""
import csv, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
A = ROOT / "data/raw/awards"


def main():
    turing = list(csv.DictReader(open(A / "turing_wikidata.csv", encoding="utf-8")))
    named = list(csv.DictReader(open(ROOT / "method/awards_named_works.csv", encoding="utf-8")))
    rows = []
    by_year = {}
    for t in turing:
        by_year.setdefault(t["year"], []).append(t["personLabel"])
    for t in sorted(turing, key=lambda x: x["year"]):
        keys = [n["key"] for n in named if n["award"] == "Turing" and n["year"] == t["year"]]
        rows.append({"year": t["year"], "award": "ACM A.M. Turing Award", "laureate": t["personLabel"], "wikidata": t["person"].rsplit("/", 1)[-1],
                     "named_keys": ";".join(sorted(set(keys))), "source": "Wikidata P166=Q185667 (CC0), queried 2026-11-03"})
    nobel = json.loads((A / "nobel_2024_2026.json").read_text(encoding="utf-8"))
    for p in nobel.get("nobelPrizes", []):
        for l in p.get("laureates", []):
            name = l.get("knownName", l.get("orgName", {})).get("en", "")
            keys = [n["key"] for n in named if n["award"].startswith("Nobel") and n["year"] == p["awardYear"] and name in n["laureates"]]
            if keys:
                rows.append({"year": p["awardYear"], "award": f"Nobel Prize in {p['category']['en']}", "laureate": name, "wikidata": "",
                             "named_keys": ";".join(sorted(set(keys))), "source": f"Nobel Prize API (CC0): {l['motivation']['en']}"})
    with open(ROOT / "data/derived/awards.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["year", "award", "laureate", "wikidata", "named_keys", "source"]); w.writeheader(); w.writerows(rows)
    print(len(rows), "rows;", sum(1 for r in rows if r["named_keys"]), "linked to papers")


if __name__ == "__main__":
    main()
