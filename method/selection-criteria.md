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
| T6 | Jurafsky & Martin, *Speech and Language Processing* | 3rd ed. draft (2024–25), author PDF | language processing and LLMs |

Schmidhuber, "Annotated History of Modern AI and Deep Learning" (2022, v3 2025) is used only as a comparison source for priority boxes, not as a reference-set member.

## Inclusion rules (any one suffices)

- **R1 Textbooks.** At least two of T1–T6 cite the work's original publication in their bibliography.
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
