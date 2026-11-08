"""R1 textbook matching: does each candidate's original publication appear in the
bibliography of T2..T6 (T1 Nilsson pending)?  Output data/derived/textbook_matches.csv

Match = normalized title substring (first 6+ words) found in the normalized bibliography
text, OR (first-author surname AND year AND 3 rarest title words within 300 chars),
OR (for titles with a subtitle: surname, exact year and the title before the colon within 250
characters of the squeezed text — added 2026-11-07, because T1 and T3 cite Rosenblatt 1962 by the
short title only). Running page footers inside a bibliography are removed first (T7 prints one at
every page break, which split the Rajpurkar 2016 entry).
Each hit is recorded with the kind of evidence so it can be audited.

method/textbook_overrides.csv (key,book,action,evidence) records hits checked by hand: action
`remove` drops a hit the proximity rule made from a neighboring entry (the rule cannot be narrowed
without losing true hits such as Nilsson's "LotfiZadeh"); `add` records a hit no rule can see;
`keep` records a hit checked by hand and kept, with the reason (added 2026-11-07, e.g. a book that cites an
earlier version of the same work); the run warns if a kept hit is no longer found.
Removed hits are written as `removed` and not counted.
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
    for pat in FOOTERS.get(name, ()):
        t = re.sub(pat, "", t)
    for a, b in (("↵", "ff"), ("ﬀ", "ff"), ("ﬁ", "fi"), ("ﬂ", "fl"), ("ﬃ", "ffi"), ("ﬄ", "ffl")):
        t = t.replace(a, b)
    if name.endswith(".html"):
        t = re.sub(r"<[^>]+>", " ", t)
    if name.endswith(".bib"):
        t = re.sub(r"[{}~]", " ", t)
    return norm(t)


def squeeze(s):
    return s.replace(" ", "")


# running page footers to drop before matching (regex on the raw text)
FOOTERS = {
    "t7_murphy_pml1_refs.txt": [r"Author: Kevin P\. Murphy\. \(C\) MIT Press\. CC-BY-NC-ND license\s*\n\s*\d{3}\s*\n\s*BIBLIOGRAPHY\s*\n"],
}

BOOKS = {
    "T1": "t1_nilsson_qai_refs.txt",  # Nilsson cites in chapter endnotes; the whole book text is matched (web PDF, Wayback 2026-10-11)
    "T2": "t2_aima4e.bib",
    "T3": "t3_goodfellow_bib.html",
    "T4": "t4_sutton_barto_2020_refs.txt",
    "T5": "t5_prince_udl_refs.txt",
    "T6": "t6_jurafsky_slp3_refs.txt",
    "T7": "t7_murphy_pml1_refs.txt",  # added 2026-11-07 (1.1): Murphy, PML: An Introduction, MIT Press 2022; author draft PDF 2025-04-18
}


def main():
    texts = {k: load_text(v) for k, v in BOOKS.items()}
    sq = {k: squeeze(t) if t else None for k, t in texts.items()}
    rows = list(csv.DictReader(open(ROOT / "data/derived/candidates_v0.csv", encoding="utf-8-sig")))
    ovr = {}
    op = ROOT / "method/textbook_overrides.csv"
    if op.exists():
        for o in csv.DictReader(open(op, encoding="utf-8-sig")):
            ovr[(o["key"], o["book"])] = o["action"]
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
                if not ev and ":" in r["title"] and sur:
                    short = squeeze(norm(r["title"].split(":")[0]))
                    if len(short) >= 12:
                        for m in re.finditer(re.escape(sur), sq[k]):
                            win = sq[k][m.start(): m.start() + 250]
                            if short in win and yr in win:
                                ev = "author+year+short-title"
                                break
            act = ovr.get((r["key"], k))
            if act == "remove" and ev not in ("", "n/a"):
                ev = "removed"
            elif act == "add" and ev in ("", "n/a"):
                ev = "manual"
            elif act == "keep" and ev in ("", "n/a"):
                print("WARNING kept hit not found:", r["key"], k)
            rec[k] = ev
            if ev and ev not in ("n/a", "removed"):
                hits += 1
        rec["n_hits"] = hits
        rec["R1"] = "pass" if hits >= 2 else ("one" if hits == 1 else "none")
        out.append(rec)
    with open(ROOT / "data/derived/textbook_matches.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0].keys())); w.writeheader(); w.writerows(out)
    c = collections.Counter(o["R1"] for o in out)
    print(len(out), dict(c))
    for k in BOOKS:
        print(k, sum(1 for o in out if o[k] not in ("", "n/a", "removed")))
    print("overrides:", {f"{k}:{b}": a for (k, b), a in ovr.items()})


if __name__ == "__main__":
    main()
