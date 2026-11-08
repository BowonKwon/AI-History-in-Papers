# Selection criteria — registered 2026-11-03

Registered before the textbook matching began. Changes after this date are logged at the bottom with reasons; the site's method page reproduces this file.

## Reference set (textbooks and general histories)

| Code | Work | Edition used | Role |
|---|---|---|---|
| T1 | Nilsson, *The Quest for Artificial Intelligence* | Cambridge UP 2010 / author web PDF | general history, 1950s–2000s |
| T2 | Russell & Norvig, *Artificial Intelligence: A Modern Approach* | 4th ed. (2020) bibliography | AI in general |
| T3 | Goodfellow, Bengio & Courville, *Deep Learning* | MIT Press 2016, online bibliography | neural networks to 2016 |
| T4 | Sutton & Barto, *Reinforcement Learning: An Introduction* | 2nd ed. (2018), author PDF | reinforcement learning |
| T5 | Prince, *Understanding Deep Learning* | MIT Press 2023, author PDF | deep learning and generative models to 2023 |
| T6 | Jurafsky & Martin, *Speech and Language Processing* | 3rd ed. draft of 2026-08-19 (author PDF, downloaded 2026-11-03) — corrected 2026-11-07, see change log | language processing and LLMs |
| T7 | Murphy, *Probabilistic Machine Learning: An Introduction* | MIT Press 2022; author draft PDF 2025-04-18 bibliography | statistical machine learning (added 2026-11-07, 1.1) |

Schmidhuber, "Annotated History of Modern AI and Deep Learning" (2022, v3 2025) is used only as a comparison source for priority boxes, not as a reference-set member.

## Inclusion rules (any one suffices)

- **R1 Textbooks.** At least two of T1–T7 (T7 from 2026-11-07) cite the work's original publication in their bibliography.
- **R2 Lineage node.** At least three already-selected papers cite it (OpenAlex or the citing paper's own reference list), and the chapter narrative cannot be written without it.
- **R3 Award.** The Turing Award or Nobel Prize citation names the achievement, and this is its original publication.
- **R4 Recent (2021 onward).** Peer-reviewed publication (or a public review record), original text checked, and the chapter's "what changed" sentence can be written from the paper's own words. Cutoff for 1.0: papers first public on or before 2025-12-31.

## Exclusions and merges

- Conference, journal, and extended versions of one contribution are one node; the node's date follows the date rule.
- Surveys and textbooks are nodes only when they are themselves turning points (e.g., Minsky & Papert 1969; Sutton & Barto 1998).
- Press releases, blog posts, and model cards are not nodes unless they are the only public record of the contribution (noted as such).

## Date rule

The node is placed at the **first public date** (technical report, thesis, preprint v1, or conference presentation, whichever came first and is documented). All other dates appear on the card. OpenAlex `publication_year` is stored separately as "record year" and never used as the node date.

## Bias report

After selection, the country and institution distribution of author affiliations (OpenAlex) is computed and published unchanged on the method page, with a note that the reference set consists of English-language textbooks.

## Change log

- 2026-11-03 — registered (owner decision D2).
- 2026-11-07 — 1.1 amendment. (a) Reference set: added **T7** Murphy, *Probabilistic Machine Learning: An Introduction* (MIT Press 2022), bibliography taken from the author's public draft PDF (version 2025-04-18; CC BY-NC-ND), because no statistical machine-learning textbook was in the set. R1 now reads "at least two of T1–T7". (b) Candidate pool widened once: works cited (OpenAlex `referenced_works`) by at least three selected papers **and** matched in at least three of T1–T7, not already candidates. Excluded at this step: textbooks and surveys (Bishop 1995, Duda & Hart 1973, Bengio et al. 2013 review), other versions of an existing node (Rumelhart et al. 1985 report and PDP chapter → rumelhart1986; Hinton et al. 2012 dropout preprint → srivastava2014; Sutton & Barto, Krizhevsky 2012, He 2015, Schapire 1990, Turing 1950, Werbos 1974 records), and works whose textbook hits could not be tied to the same work (Samuel 1967 Part II — title collides with Samuel 1959; Lin 1992/1993 — textbooks cite the 1992 journal paper, citing papers cite the 1993 thesis). 16 works added; selection then runs under R1–R4 unchanged. A second OpenAlex record of the same work (e.g. arXiv and journal) is mapped to the same node so that its citations count.
- 2026-11-07 — 1.1 corrections after an outside check. No rule changed. (a) The 16 works added by the widening are listed in `pool-1.1-added.csv`, reconstructed from the candidate lists of 1.0.1 and 1.1. One of them, Jelinek 1976, entered on a T6 match that was a different Jelinek paper (Jelinek, Mercer & Bahl 1975); with T1 and T2 it meets R1 but not the widening condition, and its place in the pool was put to the owner (decided the same day; see the next entry). (b) Textbook matching: running page footers are removed from the T7 text (an entry split by a footer was missed: Rajpurkar et al. 2016); titles with a subtitle are also matched by surname, year and the title before the colon (T1 and T3 cite Rosenblatt 1962 that way); hits checked by hand are kept in `textbook_overrides.csv` (four proximity-rule hits removed: Jelinek 1976 in T6, Cho et al. 2014 in T5, LeCun et al. 2015 in T3, Ha & Schmidhuber 2018 in T6). No selection changed. (c) R2 counts now include the reference lists read for the cards, as R2 says; before, an older snapshot of those lists was used and 36 reference-list citations from 1.1 were missing. Two R2 counts rose; no selection changed. (d) `edges.csv` keeps only citations between selected papers, as the data schema states; 87 rows touching unselected candidates had been included.
- 2026-11-07 — Owner decisions after the outside check. No rule changed. (a) **Correction (정정) of the T6 edition.** The reference-set table said "3rd ed. draft (2024–25)", but the bibliography compared since registration is the authors' draft dated 2026-08-19 (title page "Draft of August 19, 2026"), downloaded on 2026-11-03, the registration date. Description only; no match changed. (b) Jelinek 1976 applied under the widening condition as registered: with the T6 hit removed it is matched in two reference works (T1, T2), short of the three the widening requires, so it leaves the candidate pool and is not selected. No exception was made. 15 of the 16 works recorded in `pool-1.1-added.csv` stay in the pool; the selection is 214. The selection script now checks the widening condition against the current textbook comparison. Jelinek 1976 would come back only if a later version (e.g. 1.2) adopted a two-reference-work widening condition, registered with its date before the matching. (c) Watkins & Dayan 1992 in T1: Nilsson cites Watkins's 1989 thesis, which first stated Q-learning. The thesis is its own selected point (watkins1989, matched in T1 by title), and the two points stay distinct, so the T1 hit is removed from the 1992 paper (`textbook_overrides.csv`); its point stays at its 1992 journal date. It still meets R1 with T4 and T5. No selection changed.
