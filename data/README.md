# Data

| File | Status | Use |
|---|---|---|
| `action_responses_pseudonymized.xlsx` | **CANONICAL** (rebuilt 2026-10-26) | The analysis dataset. 270 rows = 30 participants × 3 phases × 3 sources; Q1–Q11 on the 0–4 export scale; trainer rows are the unrounded item-wise mean of the available trainer ratings (`n_raters` = 2 for 88 rows, 1 for 2 rows). **No imputed values.** |
| `ratings_pseudonymized.xlsx` | canonical, rating level | 358 rows = one row per individual rating (rater coded `SELF` / `T1` / `T2` / `OBS`, `origin` = `export` or `supplementary`). Source of the dataset above and of the trainer ICC. |
| `legacy/action_responses_imputed_2026-10-14.xlsx` | superseded | The previous "canonical" file (git `cb73d20` and earlier). Contained 12 observer and 18 trainer participant-phase records imputed with phase-level item means, and 15 trainer records based on a single rater. Reproduces the numbers of the JARID submission and of the RDD draft before 2026-10-26. Kept for provenance only. |
| `legacy/action_responses_UNVERIFIED.xlsx` | legacy | Earlier export of unknown processing. **Do not use.** |
| `derived/action_responses_rounded.xlsx` | superseded | Nearest-integer rounding of the imputed file (see `derived/README.md`). Not used. |

## How the canonical files were built (`scripts/build_dataset.py`)

Inputs — both PRIVATE (participant and rater names), kept outside the repository and never committed:

| Input | Content | SHA-256 |
|---|---|---|
| Raw platform export | 300 rows, submissions dated 7 Oct – 27 Nov 2025 | `c6c42fbe9d6f5761713334b2e2da11ebdba8ec86ed4c99bc2728a25aae9c74b5` |
| Supplementary ratings workbook (`PRIVATE.xlsx`) | Supplied by the first author on 26 Oct 2026. Sheets: `Παρατηρητής` (12 rows), `Εκπαιδευτές` (36 rows = 2 trainers × 18 records), `Προαιρετικά` (15 second-trainer ratings). Integer values 0–4. | `94671c5473c08737d969042b3e071ce7b9d9cd508dae184fdd913a5722fa18ca` |

The supplementary workbook is recorded as a file delivered by the author. It contains exactly the participant-phase records that are absent from the export (verified by key); how and when those ratings were originally recorded is not documented in this repository.

Steps:
1. **Pseudonyms** — sorted participant names → `P01…P30` (same rule as all earlier versions; pseudonyms are stable). Verified: the pseudonyms written in the supplementary workbook match this mapping for all 63 rows.
2. **Rater codes** — the two named trainers of the export → `T1`/`T2` (sorted names), observer → `OBS`, self-report → `SELF`. In the supplementary workbook trainers are labelled only "Εκπαιδευτής 1/2" and are coded `T1`/`T2` by label; this numbering is **not linked** to the named trainers of the export. The 15 `Προαιρετικά` ratings are assigned to whichever trainer was missing from that record in the export.
3. **Merge** of export and supplementary rows at the level of individual ratings, before any averaging. A supplementary row that would collide with an existing (participant, source, rater, phase) key stops the script; none did.
4. **Duplicate submissions** by the same rater for the same participant × phase (5 in the export): three identical pairs collapsed; two pairs with differing values (P14 trainer T2 phase A; P25 observer phase A) resolved by keeping the **first submission** — author decision, 26 Oct 2026 (`--dup-policy first`; `last` and `mean` are available for sensitivity checks).
5. **Aggregation** — trainer ratings averaged item-wise per participant × phase (unrounded); no imputation of any kind.

## Completeness

| Source | Participant-phase records with data in the export (of 90) | After merge | Records with 2 trainer ratings |
|---|---|---|---|
| Beneficiaries | 90 | 90 | — |
| Trainers/educators | 72 (P16 B,C · P18 A,B,C · P23 B · P27–P30 A,B,C missing) | **90** | 55 → **88** (P14 A and P25 A remain single-rater) |
| Independent observer | 78 (P27–P30 A,B,C missing) | **90** | — |

Individual ratings: 295 from the export (300 minus 5 duplicate rows) + 63 supplementary = 358. Items on the 0–4 scale; `statistical_analysis.py` adds 1 → 1–5.

## Verification (2026-10-26, `scripts/statistical_analysis.py` → `analysis/results.json`)

| Source | M_A | M_C | t(29) | d_z [95% CI] | Shapiro–Wilk W / p | Friedman χ²(2) | α A / B / C |
|---|---|---|---|---|---|---|---|
| Beneficiaries | 3.24 | 4.75 | −13.41 | 2.45 [1.73, 3.16] | .945 / .121 | 44.86 | .90 / .95 / .69 |
| Trainers/educators | 2.68 | 3.30 | −8.88 | 1.62 [1.08, 2.16] | .946 / .134 | 36.22 | .95 / .96 / .95 |
| Independent observer | 2.18 | 2.58 | −7.69 | 1.40 [0.90, 1.91] | .953 / .201 | 31.65 | .82 / .87 / .79 |

All paired t, Wilcoxon and Friedman tests p < .001; all Bonferroni pairwise comparisons significant (max p = .004). Shapiro–Wilk values refer to the Phase C − Phase A difference scores; a non-significant result does not establish normality. Beneficiary results are identical to the previous dataset because self-report data were never affected.

**Inter-rater agreement of the two trainers** (composite score, cells with both ratings; `results.json → trainer_interrater_agreement`). Because the T1/T2 labels are arbitrary in the 18 cells where both ratings come from the supplementary file, and because the 88 cells are repeated measures of 30 participants, the primary estimate is a **one-way random-effects ICC computed per phase** with exact F-based 95% CIs (Shrout & Fleiss 1979): ICC(1,2) (reliability of the mean of two ratings, which is what the analysis uses) = .51 [−.05, .77] (A, n = 28), .33 [−.40, .68] (B, n = 30), −.03 [−1.15, .51] (C, n = 30); single-rating ICC(1,1) = .34, .20, −.02. Two-way ICC(2,1) on the 70 cells with identified raters gives .33 / .22 / .06 (sensitivity). One trainer rated systematically higher than the other (mean difference 0.4–0.9 points). A pooled ICC over all 88 cells (earlier reported as .38) is not a valid estimate and is not used. Not yet reported in the manuscript — author decision pending (see STATUS.md).

## Privacy
Names, the pseudonym mapping and the supplementary workbook are stored only on the first author's machine. `.gitignore` excludes `*PRIVATE*` and `*_mapping*.csv`; the raw export is never committed.
