# Data

| File | Status | Use |
|---|---|---|
| `action_responses_pseudonymized.xlsx` | **CANONICAL** | The analysis dataset. 270 rows = 30 participants × 3 phases × 3 sources. Reproduces every number in the manuscript exactly. |
| `legacy/action_responses_UNVERIFIED.xlsx` | legacy | Earlier export of unknown processing; differs on ~45% of rows and gives slightly different trainer/observer statistics. **Do not use.** Kept only for provenance. |

## How the canonical file was built
`scripts/build_dataset.py` takes the raw platform export (300 rows, **contains names, never committed**) and:
1. keeps one beneficiary self-report per person × phase;
2. averages the two trainer/educator ratings item-wise per person × phase;
3. for the independent observer (2/4/4 person-phase records missing in A/B/C) imputes missing records with the phase-level item mean; a single duplicate observer submission is resolved by keeping the first;
4. replaces names with pseudonyms P01–P30 (mapping held offline by the first author).

Items are on the export's 0–4 scale; `statistical_analysis.py` adds 1 to obtain the 1–5 scale reported in the paper.

## Verification (2026-10-14)
Running `statistical_analysis.py` on the canonical file yields exactly the manuscript values:
Beneficiaries t(29)=−13.41, d=2.45 [1.73, 3.16] · Trainers t=−7.40, d=1.35 [0.86, 1.85] · Observer t=−9.05, d=1.65 [1.10, 2.20]; Shapiro–Wilk 0.945/0.950/0.904; Friedman 44.86/44.67/40.27.
