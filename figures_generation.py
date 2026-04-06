"""
=============================================================================
Δημιουργία Γραφημάτων — ΚΔΗΦ «Ο Κήπος της Λυσούς»
Κοινωνικο-Συναισθηματική Ενδυνάμωση Ενηλίκων με Αναπηρίες

Γραφήματα που παράγονται:
  Fig 1 — Boxplots (3 αξιολογητές × 3 φάσεις)
  Fig 2 — Violin plots
  Fig 3 — Trajectory plot (M ± 95% CI)
  Fig 4 — Forest plot (Cohen's d, Φάση Α→Γ)
  Fig 5 — Q-Q plots (έλεγχος κανονικότητας)
  Fig 6 — Heatmap (ανά ερώτηση × φάση, Ωφελούμενοι)
  Fig 7 — Pairwise effect sizes (όλοι οι συνδυασμοί φάσεων)

Εξαρτήσεις: pandas, scipy, matplotlib, numpy, openpyxl
Εγκατάσταση: pip install pandas scipy matplotlib openpyxl

Χρήση:
  python figures_generation.py

Σημείωση: Βάλε το αρχείο Excel στον ίδιο φάκελο με το script,
          ή άλλαξε τις μεταβλητές DATA_FILE / OUTPUT_DIR παρακάτω.
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

# ─── ΠΑΡΑΜΕΤΡΟΙ — ΑΛΛΑΞΕ ΕΔΩ ΑΝ ΧΡΕΙΑΣΤΕΙ ────────────────────────────────────
DATA_FILE  = 'action_1_responses_30complete.xlsx'  # path αρχείου δεδομένων
OUTPUT_DIR = 'figures'                              # φάκελος εξόδου γραφημάτων

# ─── ΣΤΑΘΕΡΕΣ ──────────────────────────────────────────────────────────────────
Q_COLS    = [f'Q{i}' for i in range(1, 12)]
RATERS    = ['Ωφελούμενοι', 'Εκπαιδευτές', 'Παρατηρητής']
PHASES    = ['Α', 'Β', 'Γ']
PHASE_LBL = ['Φάση Α\n(baseline)', 'Φάση Β\n(κατά τη διάρκεια)', 'Φάση Γ\n(τέλος)']
COLORS    = ['#2196F3', '#4CAF50', '#FF5722']
DPI       = 150

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

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ─── ΦΟΡΤΩΣΗ & ΠΡΟΕΠΕΞΕΡΓΑΣΙΑ ─────────────────────────────────────────────────
df = pd.read_excel(DATA_FILE)
df[Q_COLS] = df[Q_COLS] + 1
df['score'] = df[Q_COLS].mean(axis=1)
df['phase'] = df['Φάση'].map(PHASE_MAP)
df['rater'] = df['Τύπος'].map(TYPE_MAP)

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
def get_complete(rater):
    sub    = combined[combined['rater'] == rater]
    counts = sub.groupby('Ωφελούμενος')['phase'].count()
    return sub[sub['Ωφελούμενος'].isin(counts[counts == 3].index)]

def get_vals(rater, phase):
    sub = get_complete(rater)
    return sub[sub['phase'] == phase]['score'].values

def get_pairs(rater, p1, p2):
    sub    = get_complete(rater)
    scores = sub.pivot_table(index='Ωφελούμενος', columns='phase', values='score')
    return scores[p1].values, scores[p2].values

def cohens_d_paired(a, b):
    diffs = np.array(b) - np.array(a)
    d     = diffs.mean() / diffs.std(ddof=1)
    n     = len(diffs)
    se    = np.sqrt(1/n + d**2 / (2*n))
    return d, d - 1.96*se, d + 1.96*se

# ─── FIG 1: BOXPLOT ────────────────────────────────────────────────────────────
fig, axes = plt.subplots(1, 3, figsize=(14, 6), sharey=True)
fig.suptitle('Κατανομή Βαθμολογιών ανά Φάση και Αξιολογητή (Boxplot)',
             fontsize=14, fontweight='bold')
for ax, rater, color in zip(axes, RATERS, COLORS):
    data = [get_vals(rater, p) for p in PHASES]
    bp   = ax.boxplot(data, patch_artist=True, widths=0.5,
                      medianprops=dict(color='black', linewidth=2.5))
    for patch, alpha in zip(bp['boxes'], [0.4, 0.65, 0.9]):
        patch.set_facecolor(color); patch.set_alpha(alpha)
    ax.set_title(rater, fontsize=12, fontweight='bold')
    ax.set_xticks([1, 2, 3]); ax.set_xticklabels(PHASE_LBL, fontsize=9)
    ax.set_ylim(0.5, 5.7)
    ax.set_ylabel('Βαθμολογία (1–5)' if ax == axes[0] else '')
    ax.yaxis.grid(True, alpha=0.4); ax.set_axisbelow(True)
    for i, d in enumerate(data, 1):
        ax.text(i, 0.65, f'n={len(d)}', ha='center', fontsize=8.5, color='gray')
plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/fig1_boxplot.png', dpi=DPI, bbox_inches='tight')
plt.close(); print("✓ Fig 1: Boxplot")

# ─── FIG 2: VIOLIN ─────────────────────────────────────────────────────────────
fig, axes = plt.subplots(1, 3, figsize=(14, 6), sharey=True)
fig.suptitle('Κατανομή Βαθμολογιών ανά Φάση και Αξιολογητή (Violin)',
             fontsize=14, fontweight='bold')
for ax, rater, color in zip(axes, RATERS, COLORS):
    data  = [get_vals(rater, p) for p in PHASES]
    parts = ax.violinplot(data, positions=[1, 2, 3], showmedians=True)
    for pc in parts['bodies']:
        pc.set_facecolor(color); pc.set_alpha(0.6)
    parts['cmedians'].set_color('black'); parts['cmedians'].set_linewidth(2)
    ax.set_title(rater, fontsize=12, fontweight='bold')
    ax.set_xticks([1, 2, 3]); ax.set_xticklabels(PHASE_LBL, fontsize=9)
    ax.set_ylim(0.5, 5.7)
    ax.set_ylabel('Βαθμολογία (1–5)' if ax == axes[0] else '')
    ax.yaxis.grid(True, alpha=0.4); ax.set_axisbelow(True)
    for i, d in enumerate(data, 1):
        ax.text(i, 0.65, f'n={len(d)}', ha='center', fontsize=8.5, color='gray')
plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/fig2_violin.png', dpi=DPI, bbox_inches='tight')
plt.close(); print("✓ Fig 2: Violin")

# ─── FIG 3: TRAJECTORY ─────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(9, 6))
for rater, color in zip(RATERS, COLORS):
    means, ci_lo, ci_hi, ns = [], [], [], []
    for phase in PHASES:
        v  = get_vals(rater, phase)
        m  = v.mean(); se = v.std(ddof=1) / np.sqrt(len(v))
        means.append(m); ci_lo.append(m - 1.96*se)
        ci_hi.append(m + 1.96*se); ns.append(len(v))
    ax.plot([1, 2, 3], means, 'o-', color=color, linewidth=2.5,
            markersize=8, label=rater)
    ax.fill_between([1, 2, 3], ci_lo, ci_hi, alpha=0.12, color=color)
    for xi, m, n in zip([1, 2, 3], means, ns):
        ax.annotate(f'{m:.2f}\n(n={n})', (xi, m),
                    textcoords='offset points', xytext=(0, 13),
                    ha='center', fontsize=8, color=color, fontweight='bold')
ax.set_xticks([1, 2, 3]); ax.set_xticklabels(PHASE_LBL, fontsize=10)
ax.set_ylabel('Μέση Βαθμολογία (1–5)', fontsize=11); ax.set_ylim(1.5, 5.9)
ax.set_title("Εξελικτική Πορεία Μέσων Βαθμολογιών (Μ ± 95% CI)",
             fontsize=13, fontweight='bold')
ax.legend(fontsize=10, loc='upper left')
ax.yaxis.grid(True, alpha=0.4); ax.set_axisbelow(True)
plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/fig3_trajectory.png', dpi=DPI, bbox_inches='tight')
plt.close(); print("✓ Fig 3: Trajectory")

# ─── FIG 4: FOREST PLOT ────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(10, 5))
for i, (rater, color) in enumerate(zip(RATERS, COLORS)):
    a, g        = get_pairs(rater, 'Α', 'Γ')
    d, dlo, dhi = cohens_d_paired(a, g)
    yi          = 2 - i
    ax.plot([dlo, dhi], [yi, yi], '-', color=color, linewidth=3)
    ax.plot(d, yi, 'D', color=color, markersize=11, zorder=5)
    ax.text(dhi + 0.08, yi,
            f"d = {d:.2f}  [{dlo:.2f}, {dhi:.2f}]  (n={len(a)})",
            va='center', fontsize=10, color=color)
ax.axvline(0, color='black', linestyle='--', linewidth=1, alpha=0.5)
for val, lbl in [(0.2,'μικρό'),(0.5,'μέτριο'),(0.8,'μεγάλο'),(1.2,'πολύ μεγάλο')]:
    ax.axvline(val, color='lightgray', linestyle=':', linewidth=1)
    ax.text(val, 2.55, lbl, ha='center', fontsize=7.5, color='gray')
ax.set_yticks([2, 1, 0]); ax.set_yticklabels(RATERS, fontsize=11)
ax.set_xlabel("Cohen's d  (Φάση Α → Φάση Γ)", fontsize=11)
ax.set_title("Forest Plot: Μεγέθη Επίδρασης ανά Αξιολογητή",
             fontsize=13, fontweight='bold')
max_hi = max(cohens_d_paired(*get_pairs(r,'Α','Γ'))[2] for r in RATERS)
ax.set_xlim(-0.4, max_hi + 1.8); ax.set_ylim(-0.5, 2.7)
ax.xaxis.grid(True, alpha=0.4); ax.set_axisbelow(True)
plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/fig4_forest.png', dpi=DPI, bbox_inches='tight')
plt.close(); print("✓ Fig 4: Forest plot")

# ─── FIG 5: Q-Q PLOTS ──────────────────────────────────────────────────────────
fig, axes = plt.subplots(1, 3, figsize=(14, 5))
fig.suptitle("Q-Q Plots Διαφορών (Φάση Γ − Φάση Α) — Έλεγχος Κανονικότητας",
             fontsize=13, fontweight='bold')
for ax, rater, color in zip(axes, RATERS, COLORS):
    a, g  = get_pairs(rater, 'Α', 'Γ')
    diffs = g - a
    stat, p = stats.shapiro(diffs)
    (osm, osr), (slope, intercept, _) = stats.probplot(diffs, dist='norm')
    ax.plot(osm, osr, 'o', color=color, alpha=0.75, markersize=7)
    ax.plot(osm, slope*np.array(osm) + intercept, '-', color='gray', linewidth=1.5)
    status = f"p = {p:.3f}  ✅" if p > .05 else f"p = {p:.3f}  ❌"
    ax.set_title(f"{rater}\nW = {stat:.3f},  {status}",
                 fontsize=10, fontweight='bold')
    ax.set_xlabel('Θεωρητικά Quantiles', fontsize=9)
    ax.set_ylabel('Παρατηρούμενα', fontsize=9)
    ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/fig5_qqplot.png', dpi=DPI, bbox_inches='tight')
plt.close(); print("✓ Fig 5: Q-Q plots")

# ─── FIG 6: HEATMAP ────────────────────────────────────────────────────────────
fig, axes = plt.subplots(1, 3, figsize=(15, 6))
fig.suptitle('Μέση Βαθμολογία ανά Ερώτηση και Φάση (Ωφελούμενοι)',
             fontsize=13, fontweight='bold')
cmap        = plt.get_cmap('YlOrRd')
item_labels = [f'Q{i}' for i in range(1, 12)]
for ax, phase, lbl in zip(axes, PHASES, PHASE_LBL):
    mask  = (df['rater'] == 'Ωφελούμενοι') & (df['phase'] == phase)
    means = df[mask][Q_COLS].mean().values.reshape(-1, 1)
    im    = ax.imshow(means, cmap=cmap, aspect='auto', vmin=1, vmax=5)
    ax.set_yticks(range(11)); ax.set_yticklabels(item_labels, fontsize=9)
    ax.set_xticks([]); ax.set_title(lbl, fontsize=11, fontweight='bold')
    for j, v in enumerate(means.flatten()):
        ax.text(0, j, f'{v:.2f}', ha='center', va='center', fontsize=9,
                color='white' if v > 3.5 else 'black', fontweight='bold')
plt.colorbar(im, ax=axes, shrink=0.7, label='Μέση Βαθμολογία (1–5)')
plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/fig6_heatmap.png', dpi=DPI, bbox_inches='tight')
plt.close(); print("✓ Fig 6: Heatmap")

# ─── FIG 7: PAIRWISE EFFECT SIZES ─────────────────────────────────────────────
pairs       = [('Α', 'Β'), ('Α', 'Γ'), ('Β', 'Γ')]
pair_labels = ['Φάση Α→Β', 'Φάση Α→Γ', 'Φάση Β→Γ']
fig, axes   = plt.subplots(1, 3, figsize=(16, 5))
fig.suptitle("Μεγέθη Επίδρασης (Cohen's d) ανά Φάση και Αξιολογητή",
             fontsize=13, fontweight='bold')
for ax, rater, color in zip(axes, RATERS, COLORS):
    for yi, (p1, p2), lbl in zip([2, 1, 0], pairs, pair_labels):
        a, b        = get_pairs(rater, p1, p2)
        d, dlo, dhi = cohens_d_paired(a, b)
        ax.plot([dlo, dhi], [yi, yi], '-', color=color, linewidth=2.5, alpha=0.8)
        ax.plot(d, yi, 'D', color=color, markersize=9, zorder=5)
        ax.text(dhi + 0.05, yi,
                f"d={d:.2f} [{dlo:.2f},{dhi:.2f}]",
                va='center', fontsize=9, color=color)
    ax.axvline(0, color='black', linestyle='--', linewidth=1, alpha=0.4)
    for val in [0.2, 0.5, 0.8, 1.2]:
        ax.axvline(val, color='#e0e0e0', linestyle=':', linewidth=1)
    ax.set_yticks([2, 1, 0]); ax.set_yticklabels(pair_labels[::-1], fontsize=9)
    ax.set_title(rater, fontsize=12, fontweight='bold')
    ax.set_xlabel("Cohen's d", fontsize=10)
    ax.xaxis.grid(True, alpha=0.3); ax.set_axisbelow(True)
    ax.set_xlim(-0.3, 3.8)
plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/fig7_pairwise_effects.png', dpi=DPI, bbox_inches='tight')
plt.close(); print("✓ Fig 7: Pairwise effects")

print(f"\nΌλα τα γραφήματα αποθηκεύτηκαν στον φάκελο '{OUTPUT_DIR}/'")
