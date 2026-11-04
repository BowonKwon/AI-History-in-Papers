# AI History in Papers · 논문으로 읽는 인공지능의 역사

**Site:** https://bowonkwon.github.io/AI-History-in-Papers/ — Korean and English.

The history of AI research from 1943 to today, followed through its original papers. Every point on the timeline is a paper with a link to the original, one sentence quoted from it with a page number, and one or two lines on what changed. Lineage lines are drawn only where a citation is confirmed; textbook attributions without a confirmed citation are dotted. Priority disputes show both sides' bibliographies and make no ruling. The "winters" are re-examined with yearly series.

1943년부터 지금까지 인공지능 연구의 역사를 원 논문으로 따라간다. 연대표의 점마다 원문 링크, 쪽을 밝힌 원문 한 문장, 「무엇을 바꿨나」 한두 줄이 붙어 있다. 계보선은 인용이 확인된 것만 실선으로 긋고, 교과서가 말하는 영향이지만 인용이 확인되지 않은 선은 점선이다. 우선권 논쟁은 양쪽 서지를 나란히 놓고 판정하지 않는다. 「겨울」은 연도 계열로 다시 본다.

## Contents · 구성

| Page · 면 | What it holds · 내용 |
|---|---|
| Home · 홈 | Timeline 1943–2025 by theme group; chapter cards · 주제 묶음별 연대표, 장 카드 |
| Eras · 시대 (7) | Narrative, citation lineage graph, paper cards, priority and date boxes · 서술, 인용 계보 그림, 논문 카드, 우선권·날짜 상자 |
| Lineage · 계보 (8) | Lineage by theme group · 주제 묶음별 계보 |
| Winters and booms · 겨울과 붐 | Title-phrase share, conference attendance, NeurIPS accepted papers, funding records · 제목 구절 비율, 학회 참가자, NeurIPS 채택 논문, 연구비 기록 |
| Paper list · 논문 목록 | All papers, sortable; CSV · 전체 표, 정렬, CSV |
| Method and limits · 방법·한계 | Registered selection rules, date rule, what was read, bias · 등록된 선정 기준, 날짜 규칙, 읽은 범위, 편중 |

## Data · 데이터

`data/` holds the CSVs the site is built from; `data/datapackage.json` describes every column and source.

| File | Rows | Content |
|---|---|---|
| `papers.csv` | one per paper | first-public date and type, identifiers, venue, pages, verbatim sentence with page, what changed (en/ko), OpenAlex id and citation count with the date read, selection rules, source status |
| `edges.csv` | one per citation | `src` cites `dst`; `kind` = `OA` (OpenAlex), `original` (seen in the citing paper's reference list), `notion` (textbook attribution, citation not confirmed) |
| `winter_title_phrases.csv` | one per year | OpenAlex records with a phrase in the title, per 10,000 of all records |
| `winter_attendance.csv` | one per conference-year | attendance (AI Index 2019; Our World in Data) |
| `winter_neurips_accepted.csv` | one per year | papers listed on proceedings.neurips.cc |
| `awards.csv` | one per laureate | Turing Award (Wikidata) and 2024 Nobel laureates linked to papers |
| `textbook_matches.csv`, `selection_v1.csv` | one per candidate | the textbook comparison and the selection outcome |

## Method · 방법

The selection rules were registered before the list was made (`method/selection-criteria.md`, 2026-11-03): at least two of six reference textbooks cite the original (R1), or three already-selected papers cite it (R2), or an award citation names it (R3), or, for 2021 onward, peer review plus a checked original (R4). Dates are first-public dates read from the originals; OpenAlex years are stored separately. Each card's quotation was read from the stated version (`method/reading-protocol.md`). Limits — the missing Nilsson comparison, inaccessible originals, late arXiv revisions, English-textbook bias — are stated on the site's method page.

## Rebuild · 다시 만들기

```
python src/merge_cards.py      # reading outputs + selection + OpenAlex -> data/papers.csv, edges.csv
python src/check_claims.py     # every link and citation claim in the narrative against the data
python src/build_site.py       # -> docs/ (ko/, en/, data/)
```

The pipeline that produced the inputs (`bibcheck.py`, `oa_refs.py`, `oa_edges.py`, `arxiv_pdfs.py`, `textbook_match.py`, `select_papers.py`, `winter_series.py`, `awards.py`) is included; it reads OpenAlex, Crossref and arXiv without an API key or e-mail, and downloads nothing that is not public.

## Sources and licenses · 자료원과 라이선스

- OpenAlex (CC0), arXiv metadata (CC0), Crossref metadata, Wikidata (CC0), Nobel Prize API (CC0), AI Index 2019 (attendance sheet), Our World in Data (CC BY), proceedings.neurips.cc.
- Text: **CC BY-NC 4.0**. Code: **PolyForm Noncommercial 1.0.0**. Data compilation: **CC BY 4.0** (sources CC0 or CC BY). See `LICENSE.md`.
- Paper texts are not redistributed; the site links to the originals and quotes one sentence per paper with its page.

Citation of OpenAlex, as they request: Priem, J., Piwowar, H., & Orr, R. (2022). OpenAlex: A fully-open index of scholarly works, authors, venues, institutions, and concepts. arXiv:2205.01833.

---

Part of [bowonkwon.github.io](https://bowonkwon.github.io/) · [공개 자료 전체](https://bowonkwon.github.io/)
