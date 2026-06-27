"""
=============================================================================
Figure Generation — ΚΔΗΦ "O Kipos tis Lysous"
Socio-Emotional Empowerment of Adults with Disabilities

Generates 5 publication-ready figures with English labels:
  Fig 1 — Boxplots (3 evaluators × 3 phases)
  Fig 2 — Violin plots
  Fig 3 — Trajectory plot (M ± 95% CI)
  Fig 4 — Forest plot (Cohen's d, Phase A → Phase C)
  Fig 5 — Q-Q plots (normality check)

Dependencies: pandas, scipy, matplotlib, numpy, openpyxl
Install:      pip install pandas scipy matplotlib openpyxl

Usage:
  python figures_generation_en.py

Note: Place the Excel file in the same folder as this script,
      or update DATA_FILE and OUTPUT_DIR below.
=============================================================================
"""

import pandas as pd
import numpy as np
from scipy import stats
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os
import warnings
warnings.filterwarnings('ignore')

# ── PARAMETERS — EDIT HERE IF NEEDED ─────────────────────────────────────────
DATA_FILE  = 'action_1_responses_30complete.xlsx'  # path to data file
OUTPUT_DIR = 'figures'                                # output folder

# ── CONSTANTS ─────────────────────────────────────────────────────────────────
Q_COLS    = [f'Q{i}' for i in range(1, 12)]
RATERS    = ['Beneficiaries', 'Trainers/Educators', 'Independent Observer']
PHASES    = ['A', 'B', 'C']
PHASE_LBL = ['Phase A\n(baseline)',
             'Phase B\n(during intervention)',
             'Phase C\n(post-intervention)']
COLORS    = ['#2196F3', '#4CAF50', '#FF5722']
DPI       = 150

PHASE_MAP = {
    'Φάση Α · Πριν (baseline)':              'A',
    'Φάση Β · Κατά τη διάρκεια':             'B',
    'Φάση Γ · Τέλος (μετά το πρόγραμμα)':   'C',
}
TYPE_MAP = {
    'Ωφελούμενος/η':           'Beneficiaries',
    'Εκπαιδευτής/τρια':        'Trainers/Educators',
    'Ανεξάρτητος παρατηρητής': 'Independent Observer',
}

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── DATA LOADING & PREPROCESSING ─────────────────────────────────────────────
df = pd.read_excel(DATA_FILE)
df[Q_COLS] = df[Q_COLS] + 1       # 0–4 → 1–5
df['score'] = df[Q_COLS].mean(axis=1)
df['phase'] = df['Φάση'].map(PHASE_MAP)
df['rater'] = df['Τύπος'].map(TYPE_MAP)

# Trainers/Educators: average per beneficiary per phase
educ_avg = (df[df['rater'] == 'Trainers/Educators']
            .groupby(['Ωφελούμενος', 'phase'])['score']
            .mean().reset_index())
educ_avg['rater'] = 'Trainers/Educators'

bene = (df[df['rater'] == 'Beneficiaries']
        [['Ωφελούμενος', 'phase', 'score', 'rater']]
        .drop_duplicates(subset=['Ωφελούμενος', 'phase']))

obs  = (df[df['rater'] == 'Independent Observer']
        [['Ωφελούμενος', 'phase', 'score', 'rater']]
        .drop_duplicates(subset=['Ωφελούμενος', 'phase']))

combined = pd.concat([bene, educ_avg, obs], ignore_index=True)

# ── HELPER FUNCTIONS ──────────────────────────────────────────────────────────
def get_complete(rater):
    """Return only participants with complete data across all 3 phases."""
    sub    = combined[combined['rater'] == rater]
    counts = sub.groupby('Ωφελούμενος')['phase'].count()
    return sub[sub['Ωφελούμενος'].isin(counts[counts == 3].index)]

def get_vals(rater, phase):
    return get_complete(rater)[get_complete(rater)['phase'] == phase]['score'].values

def get_pairs(rater, p1, p2):
    sub    = get_complete(rater)
    scores = sub.pivot_table(index='Ωφελούμενος', columns='phase', values='score')
    return scores[p1].values, scores[p2].values

def cohens_d_paired(a, b):
    """Paired Cohen's d with 95% CI (delta method)."""
    diffs = np.array(b) - np.array(a)
    d     = diffs.mean() / diffs.std(ddof=1)
    n     = len(diffs)
    se    = np.sqrt(1/n + d**2 / (2*n))
    return d, d - 1.96*se, d + 1.96*se

# ── FIG 1: BOXPLOT ────────────────────────────────────────────────────────────
fig, axes = plt.subplots(1, 3, figsize=(14, 6), sharey=True)
fig.suptitle(
    'Distribution of Socio-Emotional Functioning Scores by Phase and Evaluator (Boxplot)',
    fontsize=13, fontweight='bold')

for ax, rater, color in zip(axes, RATERS, COLORS):
    data = [get_vals(rater, p) for p in PHASES]
    bp   = ax.boxplot(data, patch_artist=True, widths=0.5,
                      medianprops=dict(color='black', linewidth=2.5))
    for patch, alpha in zip(bp['boxes'], [0.4, 0.65, 0.9]):
        patch.set_facecolor(color); patch.set_alpha(alpha)
    ax.set_title(rater, fontsize=11, fontweight='bold')
    ax.set_xticks([1, 2, 3])
    ax.set_xticklabels(PHASE_LBL, fontsize=9)
    ax.set_ylim(0.5, 5.7)
    ax.set_ylabel('Score (1–5)' if ax == axes[0] else '')
    ax.yaxis.grid(True, alpha=0.4); ax.set_axisbelow(True)
    for i, d in enumerate(data, 1):
        ax.text(i, 0.65, f'n={len(d)}', ha='center', fontsize=8.5, color='gray')

plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/boxplot_scores.png', dpi=DPI, bbox_inches='tight')
plt.close()
print("✓ Fig 1: Boxplot")

# ── FIG 2: VIOLIN ─────────────────────────────────────────────────────────────
fig, axes = plt.subplots(1, 3, figsize=(14, 6), sharey=True)
fig.suptitle(
    'Distribution of Socio-Emotional Functioning Scores by Phase and Evaluator (Violin)',
    fontsize=13, fontweight='bold')

for ax, rater, color in zip(axes, RATERS, COLORS):
    data  = [get_vals(rater, p) for p in PHASES]
    parts = ax.violinplot(data, positions=[1, 2, 3], showmedians=True)
    for pc in parts['bodies']:
        pc.set_facecolor(color); pc.set_alpha(0.6)
    parts['cmedians'].set_color('black'); parts['cmedians'].set_linewidth(2)
    ax.set_title(rater, fontsize=11, fontweight='bold')
    ax.set_xticks([1, 2, 3])
    ax.set_xticklabels(PHASE_LBL, fontsize=9)
    ax.set_ylim(0.5, 5.7)
    ax.set_ylabel('Score (1–5)' if ax == axes[0] else '')
    ax.yaxis.grid(True, alpha=0.4); ax.set_axisbelow(True)
    for i, d in enumerate(data, 1):
        ax.text(i, 0.65, f'n={len(d)}', ha='center', fontsize=8.5, color='gray')

plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/violin_scores.png', dpi=DPI, bbox_inches='tight')
plt.close()
print("✓ Fig 2: Violin")

# ── FIG 3: TRAJECTORY ─────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(9, 6))

for rater, color in zip(RATERS, COLORS):
    means, ci_lo, ci_hi, ns = [], [], [], []
    for phase in PHASES:
        v  = get_vals(rater, phase)
        m  = v.mean(); se = v.std(ddof=1) / np.sqrt(len(v))
        means.append(m); ci_lo.append(m - 1.96*se)
        ci_hi.append(m + 1.96*se); ns.append(len(v))
    ax.plot([1, 2, 3], means, 'o-', color=color,
            linewidth=2.5, markersize=8, label=rater)
    ax.fill_between([1, 2, 3], ci_lo, ci_hi, alpha=0.12, color=color)
    for xi, m, n in zip([1, 2, 3], means, ns):
        ax.annotate(f'{m:.2f}\n(n={n})', (xi, m),
                    textcoords='offset points', xytext=(0, 13),
                    ha='center', fontsize=8, color=color, fontweight='bold')

ax.set_xticks([1, 2, 3])
ax.set_xticklabels(PHASE_LBL, fontsize=10)
ax.set_ylabel('Mean Score (1–5)', fontsize=11)
ax.set_ylim(1.5, 5.9)
ax.set_title('Longitudinal Trajectory of Mean Scores (M ± 95% CI)',
             fontsize=13, fontweight='bold')
ax.legend(fontsize=10, loc='upper left')
ax.yaxis.grid(True, alpha=0.4); ax.set_axisbelow(True)

plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/trajectory_scores.png', dpi=DPI, bbox_inches='tight')
plt.close()
print("✓ Fig 3: Trajectory")

# ── FIG 4: FOREST PLOT ────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(10, 5))

for i, (rater, color) in enumerate(zip(RATERS, COLORS)):
    a, g        = get_pairs(rater, 'A', 'C')
    d, dlo, dhi = cohens_d_paired(a, g)
    yi          = 2 - i
    ax.plot([dlo, dhi], [yi, yi], '-', color=color, linewidth=3)
    ax.plot(d, yi, 'D', color=color, markersize=11, zorder=5)
    ax.text(dhi + 0.08, yi,
            f"d = {d:.2f}  [{dlo:.2f}, {dhi:.2f}]  (n={len(a)})",
            va='center', fontsize=10, color=color)

ax.axvline(0, color='black', linestyle='--', linewidth=1, alpha=0.5)
for val, lbl in [(0.2,'small'), (0.5,'medium'), (0.8,'large'), (1.2,'very large')]:
    ax.axvline(val, color='lightgray', linestyle=':', linewidth=1)
    ax.text(val, 2.55, lbl, ha='center', fontsize=7.5, color='gray')

ax.set_yticks([2, 1, 0])
ax.set_yticklabels(RATERS, fontsize=11)
ax.set_xlabel("Cohen's d  (Phase A → Phase C)", fontsize=11)
ax.set_title("Forest Plot: Effect Sizes by Evaluator Category",
             fontsize=13, fontweight='bold')
max_hi = max(cohens_d_paired(*get_pairs(r, 'A', 'C'))[2] for r in RATERS)
ax.set_xlim(-0.4, max_hi + 1.8)
ax.set_ylim(-0.5, 2.7)
ax.xaxis.grid(True, alpha=0.4); ax.set_axisbelow(True)

plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/forest_effects.png', dpi=DPI, bbox_inches='tight')
plt.close()
print("✓ Fig 4: Forest plot")

# ── FIG 5: Q-Q PLOTS ──────────────────────────────────────────────────────────
fig, axes = plt.subplots(1, 3, figsize=(14, 5))
fig.suptitle(
    'Q-Q Plots of Difference Scores (Phase C − Phase A) — Normality Check',
    fontsize=13, fontweight='bold')

for ax, rater, color in zip(axes, RATERS, COLORS):
    a, g  = get_pairs(rater, 'A', 'C')
    diffs = g - a
    stat, p = stats.shapiro(diffs)
    (osm, osr), (slope, intercept, _) = stats.probplot(diffs, dist='norm')
    ax.plot(osm, osr, 'o', color=color, alpha=0.75, markersize=7)
    ax.plot(osm, slope*np.array(osm) + intercept, '-',
            color='gray', linewidth=1.5)
    status = f"p = {p:.3f}  ✓" if p > .05 else f"p = {p:.3f}  ✗"
    ax.set_title(f"{rater}\nW = {stat:.3f},  {status}",
                 fontsize=10, fontweight='bold')
    ax.set_xlabel('Theoretical Quantiles', fontsize=9)
    ax.set_ylabel('Observed Quantiles', fontsize=9)
    ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/qqplot_normality.png', dpi=DPI, bbox_inches='tight')
plt.close()
print("✓ Fig 5: Q-Q plots")

print(f"\nAll figures saved to '{OUTPUT_DIR}/'")
