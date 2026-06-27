# Statistical Analysis — Lyso's Garden Day Care Center

**Enhancing Socio-Emotional Functioning of Adults with Disabilities**

Analysis code and manuscript files for the paper submitted to *Journal of Applied Research in Intellectual Disabilities* (JARID, Wiley):

> Vionis, P., Christidou, E., Christidou, S., & Kotsilieris, T. (submitted). *Enhancing Socio-Emotional Functioning of Adults with Disabilities: Evaluation of an Experiential Intervention in a Day Care Facility.*

---

## Repository Contents

```
├── manuscript/
│   ├── kipos_jarid.tex              # Main manuscript (JARID submission)
│   ├── kipos_jarid_titlepage.tex    # Title page (authors, ORCIDs, statements)
│   ├── kipos_jarid_coverletter.tex  # Cover letter
│   ├── kipos_final.tex              # Full version (with author details)
│   ├── references.bib               # BibTeX bibliography
│   └── figures/                     # All manuscript figures (English)
│       ├── conceptual_model.jpg
│       ├── boxplot_scores.png
│       ├── violin_scores.png
│       ├── forest_effects.png
│       ├── trajectory_scores.png
│       ├── qqplot_normality.png
│       └── greek/                   # Greek-language figure versions
├── scripts/
│   ├── statistical_analysis.py      # Full statistical pipeline
│   ├── figures_generation_en.py     # English figure generation
│   └── figures_generation.py        # Greek figure generation
└── data/
    └── action_responses.xlsx        # Dataset (anonymised)
```

---

## Study Overview

A three-phase longitudinal evaluation of an arts-based socio-emotional empowerment program ("The Universe Within Us") implemented over three months at a Day Care Center (DCC) serving adults with intellectual and psychosocial disabilities.

**Design:** Three measurement phases (A, B, C) × three evaluator sources (beneficiary self-reports, trainer/educator assessments, independent observer ratings).

**Sample:** n = 30 adults (complete longitudinal sample); mean age 36.8 years (SD = 10.0).

**Program:** Theatre, music, movement, ceramics, narrative dialogue; grounded in Social and Emotional Learning (SEL), emotional intelligence theory, Vygotsky's socio-cultural theory, and Yalom's group therapeutic factors.

---

## Key Results

| Evaluator | Phase A Mean | Phase C Mean | Cohen's *d* | 95% CI | *p* |
|---|---|---|---|---|---|
| Beneficiaries (self-report) | 3.24 | 4.75 | 2.45 | [1.73, 3.16] | < .001 |
| Trainers / Educators | 2.85 | 3.56 | 1.35 | [0.86, 1.85] | < .001 |
| Independent Observer | 2.17 | 2.60 | 1.65 | [1.10, 2.20] | < .001 |

Friedman tests confirmed significant progressive change across all three phases (all χ² > 40, p < .001). Bonferroni-corrected pairwise comparisons showed significant differences between every consecutive phase pair (all p < .003).

---

## Statistical Methods

| Test | Purpose |
|---|---|
| Cronbach's α | Internal consistency per evaluator category (0.84–0.95) |
| Shapiro–Wilk | Normality of difference scores |
| Paired *t*-test | Phase A vs Phase C comparison |
| Cohen's *d* + 95% CI | Effect size estimation |
| Wilcoxon signed-rank | Non-parametric confirmatory test (where normality not met) |
| Friedman test | Longitudinal change across three phases |
| Bonferroni pairwise *t*-tests | Phase A–B, B–C, A–C comparisons (α_adj = .017) |

---

## Requirements

```
Python 3.9+
pandas
scipy
matplotlib
numpy
openpyxl
```

Install dependencies:

```bash
pip install pandas scipy matplotlib numpy openpyxl
```

---

## Usage

```bash
# Run full statistical analysis
python scripts/statistical_analysis.py

# Generate English figures
python scripts/figures_generation_en.py

# Generate Greek figures
python scripts/figures_generation.py
```

Figures are saved automatically to `manuscript/figures/`.

---

## Data Availability

The anonymised dataset (`data/action_responses.xlsx`) is included in this repository. Raw individual-level data are available from the corresponding author upon reasonable request.

---

## License

MIT License — Free to use with attribution.

---

## Contact

Panagiotis Vionis  
Department of Business and Organization Administration, University of Peloponnese  
panagiotisvionis@gmail.com
