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

**Inter-rater agreement of the two trainers** (`results.json → trainer_interrater_agreement`; composite score 1–5). The two educators are specific persons who rated everyone and the analysed trainer score is their mean, so a **two-way model for the average of k = 2** (McGraw & Wong 1996) is used, with absolute agreement ICC(A,2) and consistency ICC(C,2) reported side by side. Rater identity is confirmed only where both ratings come from the export (55 cells: 16/19/20 per phase); the 15 `Προαιρετικά` ratings are assigned to the missing rater by assumption, and in the 18 cells supplied entirely by the supplementary file the labels are arbitrary. The primary estimates are therefore computed **per phase on the export-only subset**:

| Phase | n | ICC(A,2) [95% CI] | ICC(C,2) [95% CI] | T1 − T2 (paired t p) |
|---|---|---|---|---|
| A | 16 | .57 [−.08, .84] | .64 [−.04, .87] | −0.40 (.028) |
| B | 19 | .42 [−.24, .78] | .70 [.22, .88] | −0.81 (<.001) |
| C | 20 | .14 [−.20, .50] | .32 [−.71, .73] | −0.80 (<.001) |

Single-rating coefficients, the 70-cell (identity-assumed) and 88-cell (labels partly arbitrary) subsets, and one-way reference values are all in the JSON. A one-way model is not adopted because the two educators differ systematically. Earlier figures (pooled ICC(2,1) = .38; one-way per-phase .51/.33/−.03) are superseded. Not yet in the manuscript — proposed wording in STATUS.md, author decision pending.

**Sensitivity — export ratings only** (`results.json → sensitivity_export_only`, complete cases without the 63 supplementary ratings): trainers n = 23, d_z = 1.32 [0.76, 1.87]; observer n = 26, d_z = 1.53 [0.97, 2.10]; beneficiaries unchanged. Supplementary trainer ratings are on average lower than export trainer ratings (2.38 vs 3.24 on the 1–5 scale); supplementary observer ratings are close to the export level (2.33 vs 2.42).

## Privacy
Names, the pseudonym mapping and the supplementary workbook are stored only on the first author's machine. `.gitignore` excludes `*PRIVATE*` and `*_mapping*.csv`; the raw export is never committed.
