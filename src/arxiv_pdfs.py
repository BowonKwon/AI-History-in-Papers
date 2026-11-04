"""Download arXiv PDFs (latest version) for candidates with an arXiv id, one request
per 3+ seconds, single connection, honest UA. Files: data/raw/papers/arxiv_{id}.pdf
Also records the version number served (from the Content-Disposition / final URL)."""
import csv, re, sys, time, urllib.request, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/raw/papers"; OUT.mkdir(parents=True, exist_ok=True)
UA = {"User-Agent": "ai-history-workshop/0.1"}


def main():
    rows = list(csv.DictReader(open(ROOT / "data/derived/candidates_v0.csv", encoding="utf-8-sig")))
    meta = {}
    mp = OUT / "_arxiv_versions.json"
    if mp.exists():
        meta = json.loads(mp.read_text())
    for r in rows:
        h = r["hint"]
        if not h.startswith("arxiv:"):
            continue
        aid = h[6:]
        f = OUT / f"arxiv_{aid}.pdf"
        if f.exists() and f.stat().st_size > 10000:
            continue
        url = f"https://arxiv.org/pdf/{aid}"
        for a in range(4):
            try:
                with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120) as resp:
                    data = resp.read()
                    cd = resp.headers.get("Content-Disposition", "")
                    final = resp.geturl()
                m = re.search(r"v(\d+)", cd) or re.search(r"v(\d+)", final)
                f.write_bytes(data)
                meta[aid] = {"version": m.group(1) if m else "", "bytes": len(data), "final_url": final}
                print(aid, meta[aid]["version"], len(data), flush=True)
                break
            except urllib.error.HTTPError as e:
                print("HTTP", e.code, aid, file=sys.stderr, flush=True)
                if e.code == 404:
                    break
                time.sleep(20 * (a + 1))
            except Exception as e:
                print("ERR", e, aid, file=sys.stderr, flush=True)
                time.sleep(20 * (a + 1))
        time.sleep(3.5)
        mp.write_text(json.dumps(meta, indent=1))


if __name__ == "__main__":
    main()
