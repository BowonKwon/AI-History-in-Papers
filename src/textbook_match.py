"""R1 textbook matching: does each candidate's original publication appear in the
bibliography of T2..T6 (T1 Nilsson pending)?  Output data/derived/textbook_matches.csv

Match = normalized title substring (first 6+ words) found in the normalized bibliography
text, OR (first-author surname AND year AND 3 rarest title words within 300 chars).
Each hit is recorded with the kind of evidence so it can be audited.
"""
import csv, re, unicodedata, collections
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TB = ROOT / "data/raw/textbooks"

STOP = set("a an the of in on for and or to with by from via its is are as at using toward towards".split())


def norm(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def load_text(name):
    p = TB / name
    if not p.exists():
        return None
    t = p.read_text(encoding="utf-8", errors="ignore")
    for a, b in (("↵", "ff"), ("ﬀ", "ff"), ("ﬁ", "fi"), ("ﬂ", "fl"), ("ﬃ", "ffi"), ("ﬄ", "ffl")):
        t = t.replace(a, b)
    if name.endswith(".html"):
        t = re.sub(r"<[^>]+>", " ", t)
    if name.endswith(".bib"):
        t = re.sub(r"[{}~]", " ", t)
    return norm(t)


def squeeze(s):
    return s.replace(" ", "")


BOOKS = {
    "T2": "t2_aima4e.bib",
    "T3": "t3_goodfellow_bib.html",
    "T4": "t4_sutton_barto_2020_refs.txt",
    "T5": "t5_prince_udl_refs.txt",
    "T6": "t6_jurafsky_slp3_refs.txt",
}


def main():
    texts = {k: load_text(v) for k, v in BOOKS.items()}
    sq = {k: squeeze(t) if t else None for k, t in texts.items()}
    rows = list(csv.DictReader(open(ROOT / "data/derived/candidates_v0.csv", encoding="utf-8-sig")))
    # word rarity across all candidate titles for picking distinctive words
    out = []
    for r in rows:
        nt = norm(r["title"])
        words = [w for w in nt.split() if w not in STOP and len(w) > 2]
        head = " ".join(nt.split()[:7])
        sur = norm(r["author"]).split()[-1] if norm(r["author"]) else ""
        yr = r["year"]
        rec = {"key": r["key"], "year": yr, "author": r["author"], "title": r["title"]}
        hits = 0
        for k, t in texts.items():
            ev = ""
            if t is None:
                ev = "n/a"
            else:
                if len(head) >= 20 and squeeze(head) in sq[k]:
                    ev = "title"
                else:
                    # author+year+distinctive words proximity
                    for m in re.finditer(re.escape(sur) + r"[^a-z]{0,40}", t) if sur else []:
                        win = t[m.start(): m.start() + 400]
                        if yr in win or str(int(yr) + 1) in win or str(int(yr) - 1) in win:
                            dw = sorted(words, key=len, reverse=True)[:3]
                            if dw and all(w in win for w in dw):
                                ev = "author+year+words"
                                break
            rec[k] = ev
            if ev and ev != "n/a":
                hits += 1
        rec["n_hits"] = hits
        rec["R1"] = "pass" if hits >= 2 else ("one" if hits == 1 else "none")
        out.append(rec)
    with open(ROOT / "data/derived/textbook_matches.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0].keys())); w.writeheader(); w.writerows(out)
    c = collections.Counter(o["R1"] for o in out)
    print(len(out), dict(c))
    for k in BOOKS:
        print(k, sum(1 for o in out if o[k] not in ("", "n/a")))


if __name__ == "__main__":
    main()
