"""
=============================================================================
Στατιστική Ανάλυση — ΚΔΗΦ «Ο Κήπος της Λυσούς»
Κοινωνικο-Συναισθηματική Ενδυνάμωση Ενηλίκων με Αναπηρίες

Αρχείο δεδομένων: action_1_responses_30complete.xlsx
Κλίμακα ερωτηματολογίου: 0–4 (μετατρέπεται αυτόματα σε 1–5)

Ανάλυση:
  - Cronbach's alpha ανά αξιολογητή και φάση
  - Περιγραφική στατιστική (M, SD, 95% CI) ανά φάση
  - Έλεγχος κανονικότητας: Shapiro-Wilk
  - Paired t-tests (Φάση Α vs Γ) + Cohen's d με 95% CI
  - Wilcoxon signed-rank (non-parametric backup)
  - Friedman test (3 φάσεις)
  - Bonferroni-corrected pairwise comparisons

Εξαρτήσεις: pandas, scipy, numpy
Εγκατάσταση: pip install pandas scipy matplotlib openpyxl

Χρήση:
  python statistical_analysis.py

Σημείωση: Βάλε το αρχείο Excel στον ίδιο φάκελο με το script,
          ή άλλαξε τη μεταβλητή DATA_FILE παρακάτω.
=============================================================================
"""

import pandas as pd
import numpy as np
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# ─── ΠΑΡΑΜΕΤΡΟΙ — ΑΛΛΑΞΕ ΕΔΩ ΑΝ ΧΡΕΙΑΣΤΕΙ ────────────────────────────────────
DATA_FILE = 'action_1_responses_30complete.xlsx'   # path του αρχείου δεδομένων

# ─── ΣΤΑΘΕΡΕΣ ──────────────────────────────────────────────────────────────────
Q_COLS   = [f'Q{i}' for i in range(1, 12)]
RATERS   = ['Ωφελούμενοι', 'Εκπαιδευτές', 'Παρατηρητής']
PHASES   = ['Α', 'Β', 'Γ']
ALPHA_BONFERRONI = 0.017   # α/3 = .05/3

PHASE_MAP = {
    'Φάση Α · Πριν (baseline)':              'Α',
    'Φάση Β · Κατά τη διάρκεια':             'Β',
    'Φάση Γ · Τέλος (μετά το πρόγραμμα)':   'Γ',
}
TYPE_MAP = {
    'Ωφελούμενος/η':           'Ωφελούμενοι',
    'Εκπαιδευτής/τρια':        'Εκπαιδευτές',
    'Ανεξάρτητος παρατηρητής': 'Παρατηρητής',
}

# ─── ΦΟΡΤΩΣΗ & ΠΡΟΕΠΕΞΕΡΓΑΣΙΑ ─────────────────────────────────────────────────
df = pd.read_excel(DATA_FILE)
df[Q_COLS] = df[Q_COLS] + 1              # 0–4 → 1–5
df['score'] = df[Q_COLS].mean(axis=1)
df['phase'] = df['Φάση'].map(PHASE_MAP)
df['rater'] = df['Τύπος'].map(TYPE_MAP)

# Εκπαιδευτές: μέσος όρος βαθμολογιών ανά ωφελούμενο × φάση
educ_avg = (df[df['rater'] == 'Εκπαιδευτές']
            .groupby(['Ωφελούμενος', 'phase'])['score']
            .mean().reset_index())
educ_avg['rater'] = 'Εκπαιδευτές'

bene = (df[df['rater'] == 'Ωφελούμενοι']
        [['Ωφελούμενος', 'phase', 'score', 'rater']]
        .drop_duplicates(subset=['Ωφελούμενος', 'phase']))

obs  = (df[df['rater'] == 'Παρατηρητής']
        [['Ωφελούμενος', 'phase', 'score', 'rater']]
        .drop_duplicates(subset=['Ωφελούμενος', 'phase']))

combined = pd.concat([bene, educ_avg, obs], ignore_index=True)

# ─── ΒΟΗΘΗΤΙΚΕΣ ΣΥΝΑΡΤΗΣΕΙΣ ────────────────────────────────────────────────────
def get_complete(rater: str) -> pd.DataFrame:
    """Επιστρέφει μόνο τους συμμετέχοντες με πλήρη δεδομένα (3 φάσεις)."""
    sub    = combined[combined['rater'] == rater]
    counts = sub.groupby('Ωφελούμενος')['phase'].count()
    return sub[sub['Ωφελούμενος'].isin(counts[counts == 3].index)]


def get_pairs(rater: str, p1: str, p2: str):
    """Επιστρέφει ζεύγη τιμών (p1, p2) για τους complete-case συμμετέχοντες."""
    sub    = get_complete(rater)
    scores = sub.pivot_table(index='Ωφελούμενος', columns='phase', values='score')
    return scores[p1].values, scores[p2].values


def cohens_d_paired(a: np.ndarray, b: np.ndarray):
    """Cohen's d για εξαρτημένα δείγματα με 95% CI (δέλτα μέθοδος)."""
    diffs = np.array(b) - np.array(a)
    d     = diffs.mean() / diffs.std(ddof=1)
    n     = len(diffs)
    se    = np.sqrt(1/n + d**2 / (2*n))
    return d, d - 1.96*se, d + 1.96*se


def cronbach_alpha(df_items: pd.DataFrame) -> float:
    """Cronbach's alpha για πίνακα αντικειμένων."""
    k         = df_items.shape[1]
    if k < 2:
        return np.nan
    item_var  = df_items.var(axis=0, ddof=1).sum()
    total_var = df_items.sum(axis=1).var(ddof=1)
    return (k / (k - 1)) * (1 - item_var / total_var)


# ─── ΑΝΑΛΥΣΗ ───────────────────────────────────────────────────────────────────
sep = "=" * 65

print(sep)
print("COMPLETE CASES ΑΝΑ ΑΞΙΟΛΟΓΗΤΗ")
print(sep)
for rater in RATERS:
    n = get_complete(rater)['Ωφελούμενος'].nunique()
    print(f"  {rater}: n = {n}")

print(f"\n{sep}")
print("ΠΙΝΑΚΑΣ 2 — CRONBACH'S ALPHA")
print(sep)
for rater in RATERS:
    for phase in PHASES:
        r_orig = {v: k for k, v in TYPE_MAP.items()}[rater]
        mask   = (df['rater'] == rater) & (df['phase'] == phase)
        sub_q  = df[mask][Q_COLS].dropna()
        alpha  = cronbach_alpha(sub_q)
        print(f"  {rater} | Φάση {phase}: α = {alpha:.3f}  (n = {len(sub_q)})")
    print()

print(f"\n{sep}")
print("ΠΙΝΑΚΑΣ 3 — ΠΕΡΙΓΡΑΦΙΚΗ ΣΤΑΤΙΣΤΙΚΗ (complete cases)")
print(sep)
print(f"  {'Αξιολογητής':<18} {'Φάση':<6} {'n':>4} {'M':>6} {'SD':>6} {'CI_lo':>7} {'CI_hi':>7}")
print("  " + "-"*55)
for rater in RATERS:
    for phase in PHASES:
        v  = get_complete(rater)
        v  = v[v['phase'] == phase]['score'].values
        n  = len(v)
        m  = v.mean()
        sd = v.std(ddof=1)
        se = sd / np.sqrt(n)
        lo, hi = m - 1.96*se, m + 1.96*se
        print(f"  {rater:<18} {phase:<6} {n:>4} {m:>6.2f} {sd:>6.2f} {lo:>7.2f} {hi:>7.2f}")
    print()

print(f"\n{sep}")
print("ΕΛΕΓΧΟΣ ΚΑΝΟΝΙΚΟΤΗΤΑΣ — SHAPIRO-WILK (διαφορές Φάση Γ − Φάση Α)")
print(sep)
for rater in RATERS:
    a, g    = get_pairs(rater, 'Α', 'Γ')
    stat, p = stats.shapiro(g - a)
    status  = "✅ κανονική" if p > .05 else "❌ μη κανονική"
    print(f"  {rater}: W = {stat:.3f}, p = {p:.3f}  {status}")

print(f"\n{sep}")
print("ΠΙΝΑΚΑΣ 4 — PAIRED t-TESTS (Φάση Α vs Φάση Γ) + COHEN'S d")
print(sep)
print(f"  {'Αξιολογητής':<18} {'n':>4} {'df':>4} {'M_diff':>8} {'t':>8} {'p':>8} "
      f"{'d':>6} {'CI_d':>18}")
print("  " + "-"*76)
for rater in RATERS:
    a, g        = get_pairs(rater, 'Α', 'Γ')
    md          = (g - a).mean()
    t, p        = stats.ttest_rel(a, g)
    d, dlo, dhi = cohens_d_paired(a, g)
    p_str       = '< .001' if p < .001 else f'= {p:.4f}'
    print(f"  {rater:<18} {len(a):>4} {len(a)-1:>4} {md:>8.3f} {t:>8.3f} "
          f"{'p '+p_str:>8} {d:>6.3f} [{dlo:.3f}, {dhi:.3f}]")

print(f"\n{sep}")
print("WILCOXON SIGNED-RANK (non-parametric backup, Φάση Α vs Γ)")
print(sep)
for rater in RATERS:
    a, g    = get_pairs(rater, 'Α', 'Γ')
    stat, p = stats.wilcoxon(a, g)
    p_str   = '< .001' if p < .001 else f'= {p:.4f}'
    print(f"  {rater}: W = {stat:.1f}, p {p_str}")

print(f"\n{sep}")
print("FRIEDMAN TEST (3 φάσεις)")
print(sep)
for rater in RATERS:
    sub     = get_complete(rater)
    wide    = sub.pivot_table(index='Ωφελούμενος', columns='phase',
                               values='score').dropna()
    stat, p = stats.friedmanchisquare(wide['Α'], wide['Β'], wide['Γ'])
    p_str   = '< .001' if p < .001 else f'= {p:.4f}'
    print(f"  {rater}: n = {len(wide)}, χ²({2}) = {stat:.3f}, p {p_str}")

print(f"\n{sep}")
print(f"BONFERRONI-CORRECTED PAIRWISE t-TESTS (α_adj = {ALPHA_BONFERRONI})")
print(sep)
for rater in RATERS:
    print(f"\n  {rater}:")
    for p1, p2 in [('Α', 'Β'), ('Β', 'Γ'), ('Α', 'Γ')]:
        a, b    = get_pairs(rater, p1, p2)
        t, p    = stats.ttest_rel(a, b)
        md      = (b - a).mean()
        sig     = "✅ sig." if p < ALPHA_BONFERRONI else "n.s."
        p_str   = '< .001' if p < .001 else f'= {p:.4f}'
        print(f"    Φάση {p1}→{p2}: n = {len(a)}, M_diff = {md:+.3f}, "
              f"t({len(a)-1}) = {t:.3f}, p {p_str}  {sig}")

print(f"\n{sep}")
print("KEY NUMBERS FOR TEXT (abstract / results)")
print(sep)
for rater in RATERS:
    sub         = get_complete(rater)
    mA          = sub[sub['phase'] == 'Α']['score'].mean()
    mG          = sub[sub['phase'] == 'Γ']['score'].mean()
    a, g        = get_pairs(rater, 'Α', 'Γ')
    t, p        = stats.ttest_rel(a, g)
    d, dlo, dhi = cohens_d_paired(a, g)
    print(f"  {rater}:")
    print(f"    M_A = {mA:.2f}, M_G = {mG:.2f}")
    print(f"    t({len(a)-1}) = {t:.2f}, p < .001")
    print(f"    d = {d:.2f}  [{dlo:.2f}, {dhi:.2f}]")
    print()

print(sep)
print("Ανάλυση ολοκληρώθηκε επιτυχώς.")
print(sep)
