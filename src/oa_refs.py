"""Fetch full OpenAlex records (single-entity lookups, free tier) for every candidate
with an OpenAlex id: referenced_works, open_access url, authorship countries/institutions,
best_oa_location. Cached JSON in data/raw/api/oa/{id}.json. No email is sent."""
import csv, json, sys, time, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/raw/api/oa"; OUT.mkdir(parents=True, exist_ok=True)
UA = {"User-Agent": "ai-history-workshop/0.1"}
SEL = "id,doi,display_name,publication_year,publication_date,type,cited_by_count,referenced_works,referenced_works_count,open_access,best_oa_location,primary_location,authorships,ids"


def fetch(oid):
    f = OUT / f"{oid}.json"
    if f.exists():
        return json.loads(f.read_text(encoding="utf-8"))
    url = f"https://api.openalex.org/works/{oid}?select={SEL}"
    for a in range(5):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
                d = json.loads(r.read().decode("utf-8"))
            f.write_text(json.dumps(d), encoding="utf-8")
            time.sleep(0.2)
            return d
        except urllib.error.HTTPError as e:
            print("HTTP", e.code, oid, file=sys.stderr, flush=True)
            if e.code == 404:
                return None
            time.sleep(10 * (a + 1))
        except Exception as e:
            print("ERR", e, oid, file=sys.stderr, flush=True)
            time.sleep(10 * (a + 1))
    return None


def main():
    rows = list(csv.DictReader(open(ROOT / "data/derived/candidates_v0.csv", encoding="utf-8-sig")))
    ids = {r["oa_id"] for r in rows if r.get("oa_id")}
    n = 0
    for oid in sorted(ids):
        if fetch(oid):
            n += 1
    print("fetched", n, "of", len(ids))


if __name__ == "__main__":
    main()
