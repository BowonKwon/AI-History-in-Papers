# Reading protocol for paper cards (stage 1)

You are given a manifest CSV of papers (key, year, first_author, title, era, identifier, local_pdf, oa_landing, oa_pdf_url, openalex_id). For each paper, produce one row in an output CSV with exactly these columns:

| column | content |
|---|---|
| key | from the manifest |
| status | `verified` (you read the original text), `partial` (only abstract/first page or a secondary copy read), `not_accessible` (no legitimate copy found) |
| source_used | local path, or the URL of the copy you actually read |
| version_used | e.g. `journal`, `conference`, `arXiv v5`, `technical report`, `thesis`, `book`, `author preprint` |
| first_public_date | the earliest documented public date of this contribution: `YYYY-MM-DD` if known, else `YYYY-MM`, else `YYYY` |
| first_public_type | what that date is: `journal issue`, `conference`, `arXiv v1`, `tech report`, `thesis`, `book`, `received date` is NOT a public date |
| date_evidence | where you saw the date (e.g. "arXiv abstract page: [v1] Mon, 12 Jun 2017"; "journal header: Received 1 Feb 1986, published 9 Oct 1986"; "Crossref published-print 1986-10") |
| other_dates | other dates for the same work, semicolon-separated (e.g. "NeurIPS 2017 proceedings (Dec 2017); journal reprint 1988") |
| venue_full | journal/proceedings name, volume(issue), or publisher for books |
| pages | printed page range of the version used, e.g. `115–133`; for arXiv give total pages, e.g. `15 pp. (arXiv v5)` |
| key_sentence | ONE sentence quoted VERBATIM from the paper (original spelling, punctuation; no paraphrase, no ellipsis inside; ≤ 60 words). Prefer the sentence where the authors state what they propose or what they found. |
| key_sentence_page | the printed page number where the sentence appears (for arXiv: PDF page number and version, e.g. `p. 2 (arXiv v5)`) |
| what_changed | 1–2 plain English sentences on what this paper introduced or established, written only from the paper's own text (abstract/introduction/conclusion). No evaluative adjectives (no "seminal", "groundbreaking", "revolutionary", "first ever"). No priority claims. |
| refs_to_candidates | keys of candidate papers (from candidates_v0.psv) that appear in THIS paper's reference list, semicolon-separated. Check the reference list itself; match by title/author/year. Empty if none or if the reference list was not readable. |
| refs_checked | `yes` if you read the whole reference list, `no` otherwise |
| notes | anything odd: title differs between versions, author list differs, date disputes, OCR problems |

## Rules

1. **Read the original.** Use `local_pdf` if present (Read tool opens PDFs by page range). Otherwise find a legitimate public copy: the publisher's open-access page, PubMed Central, the author's or university's page, an institutional repository, proceedings sites (neurips.cc, proceedings.mlr.press, aclanthology.org, ojs.aaai.org, ijcai.org), OpenReview, or an archive.org item page. Give the URL in `source_used`.
2. **Do not bypass paywalls or bot checks.** Use ordinary requests only; do not spoof a browser user agent; do not use Sci-Hub or similar. If a page blocks automated access, try one alternate legitimate source and then mark `not_accessible` with the landing URL in `source_used`.
3. **Never put an email address or personal data in any request** (no `mailto=` parameters, no API keys).
4. **Quotes are verbatim.** Copy the sentence exactly as printed. If the PDF text is garbled, choose another sentence or mark `partial`. Do not invent page numbers; if you cannot see the page number, write `page unknown`.
5. **Dates:** the earliest public date must be evidenced. For arXiv papers open `https://arxiv.org/abs/{id}` and read the `[v1]` submission date. For old journal papers use the issue date printed on the paper or Crossref (`https://api.crossref.org/works/{doi}`, public pool, no mailto). "Received" dates are not public dates.
6. **Reference list:** read the paper's own bibliography and list which candidate papers it cites. This is used to draw lineage lines, so be exact — a wrong edge is worse than a missing one.
7. **Write the output** with Python's `csv` module (UTF-8 with BOM, quoting all fields) to the path given in your brief. Do not write anywhere else. Do not modify the manifest.
8. Work through every paper in the manifest; when you cannot verify, say so in `status` and `notes` instead of guessing.
