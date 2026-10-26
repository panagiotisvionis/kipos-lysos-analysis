"""
=============================================================================
Στατιστική Ανάλυση — ΚΔΗΦ, Κοινωνικο-Συναισθηματική Ενδυνάμωση Ενηλίκων με Αναπηρίες

Αρχείο δεδομένων: ../data/action_responses_pseudonymized.xlsx
  270 γραμμές = 30 ωφελούμενοι × 3 φάσεις × 3 πηγές. Οι γραμμές εκπαιδευτών είναι
  ήδη ο item-wise μέσος των διαθέσιμων αξιολογήσεων (βλ. build_dataset.py).
Προαιρετικό: ../data/ratings_pseudonymized.xlsx (ατομικές αξιολογήσεις) → ICC εκπαιδευτών.
Κλίμακα ερωτηματολογίου: 0–4 (μετατρέπεται σε 1–5)

Ανάλυση (όλα υπολογίζονται από τα δεδομένα — καμία σταθερή τιμή):
  - Cronbach's alpha ανά πηγή και φάση (για εκπαιδευτές: πίνακας μέσων item scores ανά ωφελούμενο)
  - Περιγραφική στατιστική (M, SD, 95% CI) ανά φάση
  - Shapiro-Wilk στις διαφορές Γ − Α
  - Paired t-tests (Α vs Γ) + Cohen's d_z με 95% CI
  - Wilcoxon signed-rank (Α vs Γ)
  - Friedman test (3 φάσεις) + Bonferroni-corrected pairwise paired t-tests
  - ICC(2,1) μεταξύ των δύο εκπαιδευτών (όπου υπάρχουν και οι δύο)

Έξοδος: κονσόλα + ../analysis/results.json (όλοι οι αριθμοί για το manuscript)

Χρήση:
  python statistical_analysis.py [DATA_FILE] [RESULTS_JSON]
=============================================================================
"""

import hashlib
import json
import os
import sys
import warnings

import numpy as np
import pandas as pd
from scipy import stats

warnings.filterwarnings('ignore')

# ─── ΠΑΡΑΜΕΤΡΟΙ ────────────────────────────────────────────────────────────────
DATA_FILE    = sys.argv[1] if len(sys.argv) > 1 else '../data/action_responses_pseudonymized.xlsx'
RESULTS_JSON = sys.argv[2] if len(sys.argv) > 2 else '../analysis/results.json'
RATINGS_FILE = os.path.join(os.path.dirname(DATA_FILE), 'ratings_pseudonymized.xlsx')

# ─── ΣΤΑΘΕΡΕΣ ──────────────────────────────────────────────────────────────────
Q_COLS   = [f'Q{i}' for i in range(1, 12)]
RATERS   = ['Ωφελούμενοι', 'Εκπαιδευτές', 'Παρατηρητής']
PHASES   = ['Α', 'Β', 'Γ']
ALPHA    = 0.05
N_PAIRWISE = 3
ALPHA_BONFERRONI = ALPHA / N_PAIRWISE
Z95 = 1.96

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
assert df['phase'].notna().all() and df['rater'].notna().all()
assert not df.duplicated(['Ωφελούμενος', 'rater', 'phase']).any(), 'duplicate participant × source × phase rows'

results = {
    'data_file': os.path.basename(DATA_FILE),
    'data_sha256': hashlib.sha256(open(DATA_FILE, 'rb').read()).hexdigest(),
    'rows': int(len(df)),
    'participants': int(df['Ωφελούμενος'].nunique()),
    'n_raters_per_source': {r: df[df['rater'] == r]['n_raters'].value_counts().sort_index().to_dict()
                            for r in RATERS} if 'n_raters' in df else None,
    'sources': {},
}


# ─── ΒΟΗΘΗΤΙΚΕΣ ΣΥΝΑΡΤΗΣΕΙΣ ────────────────────────────────────────────────────
def wide(rater: str) -> pd.DataFrame:
    """Πίνακας ωφελούμενος × φάση (score) — μόνο ωφελούμενοι με και τις 3 φάσεις."""
    w = df[df['rater'] == rater].pivot(index='Ωφελούμενος', columns='phase', values='score')
    return w.dropna()


def cohens_d_paired(a: np.ndarray, b: np.ndarray):
    """d_z = M_diff / SD_diff, με 95% CI (προσεγγιστική μέθοδος δέλτα)."""
    diffs = np.asarray(b) - np.asarray(a)
    d     = diffs.mean() / diffs.std(ddof=1)
    n     = len(diffs)
    se    = np.sqrt(1 / n + d ** 2 / (2 * n))
    return d, d - Z95 * se, d + Z95 * se


def cronbach_alpha(items: pd.DataFrame) -> float:
    k = items.shape[1]
    item_var  = items.var(axis=0, ddof=1).sum()
    total_var = items.sum(axis=1).var(ddof=1)
    return (k / (k - 1)) * (1 - item_var / total_var)


def icc_oneway(x: np.ndarray, alpha: float = ALPHA) -> dict:
    """ICC(1,1) και ICC(1,k): one-way random effects (Shrout & Fleiss 1979, Case 1) με ακριβή F-based CI.
    Κατάλληλο όταν οι αξιολογητές ΔΕΝ είναι ταυτοποιήσιμοι σε όλα τα κελιά (βλ. build_dataset.py)."""
    n, k = x.shape
    grand = x.mean()
    msb = k * ((x.mean(axis=1) - grand) ** 2).sum() / (n - 1)
    msw = ((x - x.mean(axis=1, keepdims=True)) ** 2).sum() / (n * (k - 1))
    F  = msb / msw
    Fu = stats.f.ppf(1 - alpha / 2, n - 1, n * (k - 1))
    Fl = stats.f.ppf(alpha / 2,     n - 1, n * (k - 1))
    return {'n': int(n), 'k': int(k),
            'icc_single': (msb - msw) / (msb + (k - 1) * msw),
            'icc_single_ci': [(F / Fu - 1) / (F / Fu + k - 1), (F / Fl - 1) / (F / Fl + k - 1)],
            'icc_average': (msb - msw) / msb,
            'icc_average_ci': [1 - Fu / F, 1 - Fl / F]}


def icc_twoway_agreement(x: np.ndarray, alpha: float = ALPHA) -> dict:
    """ICC(2,1) = ICC(A,1): two-way random effects, absolute agreement, single rating,
    με CI κατά McGraw & Wong (1996). Απαιτεί σταθερή ταυτότητα αξιολογητή ανά στήλη."""
    n, k = x.shape
    grand = x.mean()
    msr = k * ((x.mean(axis=1) - grand) ** 2).sum() / (n - 1)
    msc = n * ((x.mean(axis=0) - grand) ** 2).sum() / (k - 1)
    mse = (((x - grand) ** 2).sum() - msr * (n - 1) - msc * (k - 1)) / ((n - 1) * (k - 1))
    icc = (msr - mse) / (msr + (k - 1) * mse + k * (msc - mse) / n)
    a = k * icc / (n * (1 - icc)); b = 1 + k * icc * (n - 1) / (n * (1 - icc))
    v = (a * msc + b * mse) ** 2 / ((a * msc) ** 2 / (k - 1) + (b * mse) ** 2 / ((n - 1) * (k - 1)))
    Fs  = stats.f.ppf(1 - alpha / 2, n - 1, v)
    Fss = stats.f.ppf(1 - alpha / 2, v, n - 1)
    lo = n * (msr - Fs * mse) / (Fs * (k * msc + (k * n - k - n) * mse) + n * msr)
    hi = n * (Fss * msr - mse) / (k * msc + (k * n - k - n) * mse + n * Fss * msr)
    return {'n': int(n), 'icc_single': icc, 'icc_single_ci': [lo, hi],
            'rater_mean_diff': float((x[:, 0] - x[:, 1]).mean())}


def pfmt(p: float) -> str:
    return '< .001' if p < .001 else f'= {p:.3f}'


# ─── ΑΝΑΛΥΣΗ ───────────────────────────────────────────────────────────────────
sep = "=" * 70
print(sep); print(f"ΔΕΔΟΜΕΝΑ: {DATA_FILE}  ({len(df)} γραμμές, {df['Ωφελούμενος'].nunique()} ωφελούμενοι)"); print(sep)
for rater in RATERS:
    n_all = df[df['rater'] == rater]['Ωφελούμενος'].nunique()
    print(f"  {rater}: ωφελούμενοι με δεδομένα = {n_all}, με και τις 3 φάσεις = {len(wide(rater))}")

print(f"\n{sep}\nCRONBACH'S ALPHA (ανά πηγή × φάση, πίνακας ωφελούμενος × 11 items)\n{sep}")
for rater in RATERS:
    res = results['sources'].setdefault(rater, {})
    res['alpha'] = {}
    for phase in PHASES:
        items = df[(df['rater'] == rater) & (df['phase'] == phase)].set_index('Ωφελούμενος')[Q_COLS]
        a = cronbach_alpha(items)
        res['alpha'][phase] = {'alpha': a, 'n': int(len(items))}
        print(f"  {rater:<12} Φάση {phase}: α = {a:.3f}  (n = {len(items)})")
    res['alpha_mean_of_phases'] = float(np.mean([res['alpha'][p]['alpha'] for p in PHASES]))
    print(f"  {rater:<12} μέσος των 3 φάσεων: {res['alpha_mean_of_phases']:.3f}\n")

print(f"{sep}\nΠΕΡΙΓΡΑΦΙΚΗ ΣΤΑΤΙΣΤΙΚΗ (score 1–5)\n{sep}")
print(f"  {'Πηγή':<12} {'Φάση':<5} {'n':>3} {'M':>6} {'SD':>6} {'CI_lo':>7} {'CI_hi':>7}")
for rater in RATERS:
    w = wide(rater); res = results['sources'][rater]; res['n'] = int(len(w)); res['descriptives'] = {}
    for phase in PHASES:
        v = w[phase].values; n = len(v); m = v.mean(); sd = v.std(ddof=1); se = sd / np.sqrt(n)
        res['descriptives'][phase] = {'n': n, 'mean': m, 'sd': sd, 'ci_lo': m - Z95 * se, 'ci_hi': m + Z95 * se}
        print(f"  {rater:<12} {phase:<5} {n:>3} {m:>6.2f} {sd:>6.2f} {m - Z95*se:>7.2f} {m + Z95*se:>7.2f}")

print(f"\n{sep}\nSHAPIRO-WILK (διαφορές Γ − Α)\n{sep}")
for rater in RATERS:
    w = wide(rater); W, p = stats.shapiro(w['Γ'] - w['Α'])
    results['sources'][rater]['shapiro'] = {'W': W, 'p': p, 'nonsignificant_at_05': bool(p > ALPHA),
                                            'note': 'test of the Phase C − Phase A difference scores; a non-significant result does not establish normality'}
    print(f"  {rater:<12} W = {W:.3f}, p {pfmt(p)}  {'κανονική' if p > ALPHA else 'ΜΗ κανονική'}")

print(f"\n{sep}\nPAIRED t-TESTS (Α vs Γ) + COHEN'S d_z\n{sep}")
print(f"  {'Πηγή':<12} {'n':>3} {'df':>3} {'M_diff':>7} {'t':>8} {'p':>8} {'d_z':>6} {'95% CI':>16}")
for rater in RATERS:
    w = wide(rater); a, g = w['Α'].values, w['Γ'].values
    t, p = stats.ttest_rel(a, g); d, dlo, dhi = cohens_d_paired(a, g)
    results['sources'][rater]['paired_t_AC'] = {'n': len(a), 'df': len(a) - 1, 'mean_diff': (g - a).mean(),
                                                't': t, 'p': p, 'd_z': d, 'd_ci_lo': dlo, 'd_ci_hi': dhi}
    print(f"  {rater:<12} {len(a):>3} {len(a)-1:>3} {(g-a).mean():>+7.3f} {t:>8.3f} {'p '+pfmt(p):>8} {d:>6.3f} [{dlo:.3f}, {dhi:.3f}]")

print(f"\n{sep}\nWILCOXON SIGNED-RANK (Α vs Γ)\n{sep}")
for rater in RATERS:
    w = wide(rater); W, p = stats.wilcoxon(w['Α'], w['Γ'])
    results['sources'][rater]['wilcoxon_AC'] = {'W': W, 'p': p}
    print(f"  {rater:<12} W = {W:.1f}, p {pfmt(p)}")

print(f"\n{sep}\nFRIEDMAN (3 φάσεις)\n{sep}")
for rater in RATERS:
    w = wide(rater); chi2, p = stats.friedmanchisquare(w['Α'], w['Β'], w['Γ'])
    results['sources'][rater]['friedman'] = {'n': int(len(w)), 'chi2': chi2, 'df': 2, 'p': p}
    print(f"  {rater:<12} n = {len(w)}, χ²(2) = {chi2:.2f}, p {pfmt(p)}")

print(f"\n{sep}\nBONFERRONI PAIRWISE PAIRED t-TESTS (α_adj = {ALPHA_BONFERRONI:.4f})\n{sep}")
for rater in RATERS:
    w = wide(rater); res = results['sources'][rater]; res['pairwise'] = {}
    print(f"  {rater}:")
    for p1, p2 in [('Α', 'Β'), ('Β', 'Γ'), ('Α', 'Γ')]:
        a, b = w[p1].values, w[p2].values; t, p = stats.ttest_rel(a, b)
        res['pairwise'][f'{p1}-{p2}'] = {'mean_diff': (b - a).mean(), 't': t, 'df': len(a) - 1, 'p': p,
                                          'significant_bonferroni': bool(p < ALPHA_BONFERRONI)}
        print(f"    {p1}→{p2}: M_diff = {(b-a).mean():+.3f}, t({len(a)-1}) = {t:.3f}, p {pfmt(p)}  {'sig.' if p < ALPHA_BONFERRONI else 'n.s.'}")
    res['pairwise_max_p'] = max(v['p'] for v in res['pairwise'].values())

# ─── ICC ΕΚΠΑΙΔΕΥΤΩΝ (από το αρχείο ατομικών αξιολογήσεων, αν υπάρχει) ──────────
if os.path.exists(RATINGS_FILE):
    r = pd.read_excel(RATINGS_FILE)
    r = r[r['Τύπος'] == 'Εκπαιδευτής/τρια'].copy()
    r['score'] = r[Q_COLS].mean(axis=1) + 1
    r['phase'] = r['Φάση'].map(PHASE_MAP)
    both = r.pivot_table(index=['Ωφελούμενος', 'phase'], columns='rater', values='score').dropna()
    origin = r.pivot_table(index=['Ωφελούμενος', 'phase'], columns='rater', values='origin', aggfunc='first').loc[both.index]
    # Σε κελιά όπου ΚΑΙ οι δύο αξιολογήσεις προέρχονται από το συμπληρωματικό αρχείο, οι ετικέτες T1/T2
    # είναι αυθαίρετες (δεν συνδέονται με τους ονομαστικούς εκπαιδευτές του export). Γι' αυτό το κύριο
    # μοντέλο είναι one-way (αξιολογητές μη ταυτοποιήσιμοι) και υπολογίζεται ΑΝΑ ΦΑΣΗ (ανεξάρτητα άτομα).
    identified = ~((origin['T1'] == 'supplementary') & (origin['T2'] == 'supplementary'))
    icc = {'model_primary': 'one-way random effects (ICC(1,1) single rating; ICC(1,2) = reliability of the mean of the two '
                            'trainer ratings actually analysed), per phase, exact F-based 95% CI (Shrout & Fleiss 1979)',
           'unit': 'composite score (mean of 11 items, 1–5) per participant; participants with both trainer ratings in that phase',
           'why_not_pooled': 'the 88 two-rater participant-phase cells are repeated measures of 30 participants; a pooled '
                             'single-level ICC treats them as independent and its CI is invalid',
           'why_not_two_way_primary': f'T1/T2 labels are arbitrary in {int((~identified).sum())} cells where both ratings come '
                                      f'from the supplementary file; two-way estimates are given only as a sensitivity '
                                      f'analysis on the {int(identified.sum())} cells with identified raters',
           'by_phase': {}, 'sensitivity_two_way_identified_cells': {}}
    print(f"\n{sep}\nΣΥΜΦΩΝΙΑ ΤΩΝ ΔΥΟ ΕΚΠΑΙΔΕΥΤΩΝ (composite score· κελιά με 2 αξιολογήσεις: {len(both)}, "
          f"με ταυτοποιημένους αξιολογητές: {int(identified.sum())})\n{sep}")
    for ph in PHASES:
        x = both.xs(ph, level='phase')[['T1', 'T2']].values
        ow = icc_oneway(x); icc['by_phase'][ph] = ow
        xi = both.xs(ph, level='phase')[identified.xs(ph, level='phase')][['T1', 'T2']].values
        tw = icc_twoway_agreement(xi); icc['sensitivity_two_way_identified_cells'][ph] = tw
        print(f"  Φάση {ph} (n = {ow['n']}): ICC(1,1) = {ow['icc_single']:.2f} [{ow['icc_single_ci'][0]:.2f}, {ow['icc_single_ci'][1]:.2f}]"
              f"   ICC(1,2) = {ow['icc_average']:.2f} [{ow['icc_average_ci'][0]:.2f}, {ow['icc_average_ci'][1]:.2f}]"
              f"   | two-way ICC(2,1) σε {tw['n']} ταυτοποιημένα κελιά = {tw['icc_single']:.2f} [{tw['icc_single_ci'][0]:.2f}, {tw['icc_single_ci'][1]:.2f}], T1−T2 = {tw['rater_mean_diff']:+.2f}")
    results['trainer_interrater_agreement'] = icc

# ─── KEY NUMBERS + JSON ─────────────────────────────────────────────────────────
print(f"\n{sep}\nKEY NUMBERS FOR TEXT\n{sep}")
for rater in RATERS:
    s = results['sources'][rater]; t = s['paired_t_AC']
    print(f"  {rater}: M_A = {s['descriptives']['Α']['mean']:.2f}, M_Γ = {s['descriptives']['Γ']['mean']:.2f}, "
          f"t({t['df']}) = {t['t']:.2f}, p {pfmt(t['p'])}, d = {t['d_z']:.2f} [{t['d_ci_lo']:.2f}, {t['d_ci_hi']:.2f}], "
          f"SW W = {s['shapiro']['W']:.3f} p {pfmt(s['shapiro']['p'])}, Friedman χ² = {s['friedman']['chi2']:.2f}, "
          f"max pairwise p = {s['pairwise_max_p']:.4f}")


def _py(o):
    if isinstance(o, dict):  return {str(k): _py(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)): return [_py(v) for v in o]
    if isinstance(o, (np.floating, float)): return round(float(o), 6)
    if isinstance(o, (np.integer,)): return int(o)
    return o


os.makedirs(os.path.dirname(RESULTS_JSON) or '.', exist_ok=True)
with open(RESULTS_JSON, 'w', encoding='utf-8') as f:
    json.dump(_py(results), f, ensure_ascii=False, indent=1)
print(f"\nΑποτελέσματα → {RESULTS_JSON}")
print(sep)
