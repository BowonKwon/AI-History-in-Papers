"""Assemble the 'winters and booms' series into data/derived/winter_*.csv
1. OpenAlex title-phrase counts per year (data/raw/winter/t_*.json, fetched 2026-11-03) and
   all-works-per-year (all.json) -> share per 10,000 works.
2. Conference attendance: AI Index 2019 sheet (1984-2019; IJCAI odd years interpolated by the
   report -- we keep only years IJCAI actually met: odd years to 2015, then yearly) and OWID (2010-2025).
3. NeurIPS accepted papers per year counted from proceedings.neurips.cc (2026-11-03).
"""
import csv, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
W = ROOT / "data/raw/winter"; D = ROOT / "data/derived"


def gb(f):
    d = json.loads((W / f).read_text(encoding="utf-8"))
    return {int(x["key"]): x["count"] for x in d["group_by"] if x["key"].isdigit()}


def main():
    total = gb("all.json")
    phrases = {"artificial intelligence": "t_artificial.json", "expert system": "t_expert.json",
               "neural network": "t_neural.json", "perceptron": "t_perceptron.json"}
    series = {p: gb(f) for p, f in phrases.items()}
    rows = []
    for y in range(1950, 2026):
        r = {"year": y, "all_works": total.get(y, 0)}
        for p, s in series.items():
            n = s.get(y, 0)
            r[f"title_{p.replace(' ', '_')}"] = n
            r[f"per10k_{p.replace(' ', '_')}"] = round(1e4 * n / total[y], 3) if total.get(y) else ""
        rows.append(r)
    with open(D / "winter_title_phrases.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)

    # attendance
    att = []
    rr = list(csv.reader(open(W / "aiindex2019_attendance.csv", encoding="utf-8-sig")))
    hdr = rr[0]
    for r in rr[1:]:
        if len(r) < 3 or not r[1].strip() or not r[0].strip():
            continue
        conf = r[1].strip()
        for i in range(2, min(len(r), len(hdr))):
            v = r[i].replace(",", "").strip()
            if not v or not hdr[i].strip().isdigit():
                continue
            y = int(hdr[i])
            note = ""
            if conf == "IJCAI" and y <= 2014 and y % 2 == 0:
                note = "interpolated by AI Index (IJCAI met in odd years); excluded"
            att.append({"conference": conf, "year": y, "attendees": int(v), "source": "AI Index 2019 ch.2 sheet", "note": note})
    for r in csv.DictReader(open(W / "owid_attendance.csv", encoding="utf-8-sig")):
        att.append({"conference": r["entity"], "year": int(r["year"]), "attendees": int(float(r["attendees"])),
                    "source": "OWID grapher (AI Index 2026)", "note": ""})
    att.sort(key=lambda x: (x["conference"], x["year"], x["source"]))
    with open(D / "winter_attendance.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["conference", "year", "attendees", "source", "note"]); w.writeheader(); w.writerows(att)

    nips = [{"year": int(a), "accepted_papers": int(b), "source": "proceedings.neurips.cc listing, counted 2026-11-03",
             "note": "incomplete listing" if int(a) >= 2025 else ""}
            for a, b in csv.reader(open(W / "neurips_accepted_counts.csv"))]
    with open(D / "winter_neurips_accepted.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(nips[0].keys())); w.writeheader(); w.writerows(nips)
    print("phrases", len(rows), "attendance", len(att), "neurips", len(nips))
    for y in (1984, 1985, 1986, 1987, 1988, 1990, 1992, 1995, 1998, 2000):
        print(y, [(a["conference"], a["attendees"]) for a in att if a["year"] == y and not a["note"] and a["source"].startswith("AI Index")])


if __name__ == "__main__":
    main()
