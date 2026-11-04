# Data schema (public CSVs)

## papers.csv — one row per selected paper

| column | meaning |
|---|---|
| key | stable id `{firstauthor}{year}` |
| era | E1–E7 chapter |
| theme | fine theme code (NN, RL, LANG, …) |
| first_public_date | earliest documented public date (YYYY-MM-DD, YYYY-MM or YYYY) — node position |
| first_public_type | what that date is (arXiv v1, conference, journal issue, tech report, thesis, book) |
| other_dates | other dates for the same work |
| record_year | OpenAlex publication_year (for the record; not used for placement) |
| authors | full author list as printed (et al. beyond 6) |
| authors_short | first author surname (+ "et al." or second author) |
| title | title as printed on the version used |
| venue | journal/proceedings, volume(issue) |
| venue_short | short venue label for tables |
| pages | printed page range of the version used |
| doi / arxiv / url | identifiers; url = legitimate public copy or landing page when no DOI/arXiv |
| version_used | the version the quote and pages refer to |
| key_sentence | one sentence quoted verbatim |
| key_sentence_cite | page and version of the quote |
| key_sentence_ko | Korean translation of the quote (ours) |
| what_changed_en / what_changed_ko | 1–2 sentences, from the paper's own text, no evaluative adjectives |
| openalex_id, oa_cited_by, oa_checked | OpenAlex work id, cited_by_count and the date it was read |
| rules | selection rules satisfied (R1–R4) |
| source_status | verified / partial / not_accessible (what we could read) |

## edges.csv — citation lineage among selected papers

| column | meaning |
|---|---|
| src | the citing (newer) paper key |
| dst | the cited (older) paper key |
| kind | `OA` = in OpenAlex referenced_works; `original` = seen in the citing paper's own reference list; `notion` = influence stated by a textbook, citation not confirmed |
| evidence | for `original`: page of the reference list; for `notion`: the textbook and page |

## winter_*.csv

- `winter_title_phrases.csv` — OpenAlex works per year whose title contains the phrase, and per 10,000 of all OpenAlex works that year (fetched 2026-11-03).
- `winter_attendance.csv` — conference attendance; source column names the AI Index 2019 sheet or OWID (AI Index 2026); IJCAI interpolated years are flagged and excluded from charts.
- `winter_neurips_accepted.csv` — accepted papers per year counted on proceedings.neurips.cc (2026-11-03).

## awards.csv

Turing Award (Wikidata, CC0) and Nobel Prize (Nobel API, CC0) entries whose citations name a paper in the list.
