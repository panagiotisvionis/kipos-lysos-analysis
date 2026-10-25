# Rounded analysis dataset — derived copy

`action_responses_rounded.xlsx` is the file supplied by the author on 25 October 2026, preserved byte-for-byte under a name identifying it as derived data.

It is **not a raw questionnaire export and does not recover missing observer ratings**. Its content matches `floor(x + 0.5)` applied to every Q1–Q11 value in `../action_responses_pseudonymized.xlsx`: nearest-integer rounding, with .5 rounded upwards. All identifiers, source labels, phases, row order and originally integer item values are unchanged.

- 270 participant/source/phase rows; 30 participant IDs.
- 567 item values changed across 85 rows: 439 trainer values and 128 observer values.
- No duplicate participant/source/phase keys or blank item cells.
- Values remain on the 0–4 export scale. Analysis scores add 1 after taking the item mean.
- Canonical SHA-256: `a8df760827a6991519891752ef6e46475681892d2e5d947f327f6efceefe01a1`.
- Derived SHA-256: `6526d9afd49c3f314daf611ee1266929d13eff03f4194837a3d4e7ae2bd71d65`.

The canonical file already contains averaged and imputed values. Rounding their decimal values does not establish that an actual individual supplied those integer responses. The existence of complete rows in this file must not be described as complete original observation.

## Comparison

`../../analysis/rounding_comparison_2026-10-25.json` records descriptive and inferential results for the canonical and rounded copies using the definitions in the existing analysis script. This is an exploratory comparison of data transformation, not a missing-data sensitivity analysis and not validation of the underlying missing-data method.

The original canonical dataset, existing scripts, figures and manuscript have not been replaced. The analyst should evaluate the rationale for post hoc rounding, the unresolved provenance of imputed records, and appropriate missing-data analyses before adopting any revised primary results. Preserve the canonical file and this provenance if this derived copy is used.

The change in results does not by itself indicate which analysis is less biased. The reason records were missing and appropriate analysis assumptions remain relevant.
