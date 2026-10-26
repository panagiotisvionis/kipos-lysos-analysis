"""
build_dataset.py — Reproducible construction of the pseudonymized analysis dataset.

INPUTS (PRIVATE — contain participant / rater names, never committed):
  --raw   raw platform export (300 rows, 7 Oct – 27 Nov 2025)
  --supp  supplementary ratings workbook supplied by the author on 26 Oct 2026
          (PRIVATE.xlsx: sheets 'Παρατηρητής', 'Εκπαιδευτές', 'Προαιρετικά').
          Ratings in this file were not present in the platform export; how and
          when they were originally recorded is not documented here.

OUTPUTS (committed):
  --out      data/action_responses_pseudonymized.xlsx
             270 rows = 30 participants × 3 phases × 3 sources. Trainer rows are the
             item-wise MEAN of the available trainer ratings (unrounded); column
             n_raters says how many ratings entered each row. No imputation.
  --ratings  data/ratings_pseudonymized.xlsx
             one row per individual rating (rater coded SELF / T1 / T2 / OBS),
             with an 'origin' column (export | supplementary).
  --map      pseudonym mapping CSV (PRIVATE — write it OUTSIDE the repository)

Steps
1. Pseudonyms: sorted participant names → P01…P30 (same rule as every earlier
   version, so pseudonyms are stable across datasets).
2. Rater codes: the two named trainers in the export → T1/T2 (sorted names);
   observer → OBS; self-report → SELF. In the supplementary file trainers are
   labelled only "Εκπαιδευτής 1/2"; these are coded T1/T2 by label but are NOT
   linked to the named trainers of the export. In 'Προαιρετικά' the single
   rating is assigned to whichever trainer is missing from that cell.
3. Supplementary rows are merged with the export BEFORE any averaging. Every
   supplementary row is checked to fill a cell that is genuinely absent from the
   export; a row that would collide with an existing (participant, source,
   rater, phase) key stops the script.
4. Duplicate submissions by the same rater for the same participant × phase:
   identical rows are collapsed; rows with differing values are a CONFLICT and
   are resolved by --dup-policy (first | last | mean), which must be given
   explicitly. Every duplicate is printed.
5. Items stay on the 0–4 export scale; analysis scripts add 1 → 1–5.

Usage
  python build_dataset.py --raw <export.xlsx> --supp <PRIVATE.xlsx> \
      --out ../data/action_responses_pseudonymized.xlsx \
      --ratings ../data/ratings_pseudonymized.xlsx \
      --map <outside-repo>/pseudonym_mapping_PRIVATE.csv --dup-policy first
"""
import argparse
import hashlib
import sys

import numpy as np
import pandas as pd

Q = [f'Q{i}' for i in range(1, 12)]
TYPES = ['Ωφελούμενος/η', 'Εκπαιδευτής/τρια', 'Ανεξάρτητος παρατηρητής']
PHASES = ['Φάση Α · Πριν (baseline)', 'Φάση Β · Κατά τη διάρκεια',
          'Φάση Γ · Τέλος (μετά το πρόγραμμα)']
KEY = ['Ωφελούμενος', 'Τύπος', 'rater', 'Φάση']

ap = argparse.ArgumentParser()
ap.add_argument('--raw', required=True)
ap.add_argument('--supp', required=True)
ap.add_argument('--out', required=True)
ap.add_argument('--ratings', required=True)
ap.add_argument('--map', required=True)
ap.add_argument('--dup-policy', required=True, choices=['first', 'last', 'mean'])
args = ap.parse_args()


def sha(path):
    return hashlib.sha256(open(path, 'rb').read()).hexdigest()


def check_items(df, label):
    v = df[Q]
    assert v.notna().all().all(), f'{label}: blank item cells'
    assert ((v % 1) == 0).all().all(), f'{label}: non-integer item values'
    assert v.min().min() >= 0 and v.max().max() <= 4, f'{label}: items outside 0–4'


# ─── 1. raw export ────────────────────────────────────────────────────────────
raw = pd.read_excel(args.raw)
tcol = [c for c in raw.columns if str(c).startswith('Τύπος')][0]
raw = raw.rename(columns={tcol: 'Τύπος'})
check_items(raw, 'export')
assert set(raw['Τύπος']) == set(TYPES) and set(raw['Φάση']) == set(PHASES)

names = sorted(raw.loc[raw['Τύπος'] == TYPES[0], 'Ωφελούμενος'].unique())
assert len(names) == 30, f'expected 30 participants, found {len(names)}'
assert set(raw['Ωφελούμενος']) <= set(names), 'rated person not among self-report participants'
pseud = {n: f'P{i + 1:02d}' for i, n in enumerate(names)}

trainers = sorted(raw.loc[raw['Τύπος'] == TYPES[1], 'Αξιολογητής'].unique())
observers = sorted(raw.loc[raw['Τύπος'] == TYPES[2], 'Αξιολογητής'].unique())
assert len(trainers) == 2 and len(observers) == 1, (len(trainers), len(observers))
rcode = {trainers[0]: 'T1', trainers[1]: 'T2', observers[0]: 'OBS'}

exp = raw.assign(P=raw['Ωφελούμενος'].map(pseud),
                 rater=np.where(raw['Τύπος'] == TYPES[0], 'SELF', raw['Αξιολογητής'].map(rcode)),
                 origin='export',
                 record=raw['ID'].astype(str))
exp = exp.sort_values('ID')[['P', 'Τύπος', 'rater', 'Φάση', 'origin', 'record'] + Q].rename(columns={'P': 'Ωφελούμενος'})

# ─── 2. supplementary workbook ───────────────────────────────────────────────
supp_sha = sha(args.supp)
sheets = {s: pd.read_excel(args.supp, sheet_name=s) for s in ['Παρατηρητής', 'Εκπαιδευτές', 'Προαιρετικά']}
rows = []
for sheet, d in sheets.items():
    check_items(d, sheet)
    assert (d['Ψευδώνυμο'] == d['Ωφελούμενος'].map(pseud)).all(), f'{sheet}: pseudonym/name mismatch'
    assert set(d['Φάση']) <= set(PHASES), f'{sheet}: unknown phase label'
    d = d.assign(origin='supplementary', record=[f'{sheet[:3]}{i + 1:02d}' for i in range(len(d))])
    if sheet == 'Παρατηρητής':
        assert (d['Τύπος'] == TYPES[2]).all()
        d['rater'] = 'OBS'
    else:
        assert (d['Τύπος'] == TYPES[1]).all()
        if sheet == 'Εκπαιδευτές':
            d['rater'] = d['Αξιολογητής'].map({'Εκπαιδευτής 1': 'T1', 'Εκπαιδευτής 2': 'T2'})
            assert d['rater'].notna().all(), 'Εκπαιδευτές: unexpected rater label'
            per_cell = d.groupby(['Ψευδώνυμο', 'Φάση'])['rater'].nunique()
            assert (per_cell == 2).all(), 'Εκπαιδευτές: a cell does not have exactly two trainer rows'
        else:  # Προαιρετικά: the missing second trainer of a single-rater cell in the export
            have = exp[exp['Τύπος'] == TYPES[1]].groupby(['Ωφελούμενος', 'Φάση'])['rater'].agg(lambda s: set(s))
            def complement(r):
                present = have.get((r['Ψευδώνυμο'], r['Φάση']), set())
                assert len(present) == 1, f'Προαιρετικά: cell {r["Ψευδώνυμο"]}/{r["Φάση"][5]} does not have exactly one trainer in the export ({present})'
                return ({'T1', 'T2'} - present).pop()
            d['rater'] = d.apply(complement, axis=1)
    rows.append(d.rename(columns={'Ψευδώνυμο': 'P'}).drop(columns=['Ωφελούμενος'])
                 .rename(columns={'P': 'Ωφελούμενος'})[['Ωφελούμενος', 'Τύπος', 'rater', 'Φάση', 'origin', 'record'] + Q])
supp = pd.concat(rows, ignore_index=True)

# every supplementary row must fill a cell that is absent from the export
exp_keys = set(map(tuple, exp[KEY].values))
collide = supp[[tuple(k) in exp_keys for k in supp[KEY].values]]
assert collide.empty, f'supplementary rows collide with export keys:\n{collide[KEY]}'

# ─── 3. merge, then resolve duplicate submissions ────────────────────────────
allr = pd.concat([exp, supp], ignore_index=True)
kept, conflicts = [], []
for key, g in allr.groupby(KEY, sort=False):
    if len(g) == 1:
        kept.append(g); continue
    distinct = g[Q].drop_duplicates()
    tag = f'{key[0]} {key[1]} {key[2]} phase {key[3][5]}: {len(g)} submissions ({", ".join(g["record"])})'
    if len(distinct) == 1:
        print(f'  duplicate (identical)  {tag} → collapsed')
        kept.append(g.iloc[[0]])
    else:
        print(f'  duplicate (CONFLICT)   {tag} → policy "{args.dup_policy}"')
        for _, r in g.iterrows():
            print(f'      {r["record"]:>6}: {list(r[Q].astype(int))}')
        conflicts.append(tag)
        if args.dup_policy == 'first':
            kept.append(g.iloc[[0]])
        elif args.dup_policy == 'last':
            kept.append(g.iloc[[-1]])
        else:
            m = g.iloc[[0]].copy(); m[Q] = g[Q].mean().values; m['record'] = '+'.join(g['record']); kept.append(m)
ratings = pd.concat(kept, ignore_index=True)
assert not ratings.duplicated(KEY).any()

# ─── 4. completeness check (no imputation) ───────────────────────────────────
cells = ratings.groupby(['Ωφελούμενος', 'Τύπος', 'Φάση']).size()
full = pd.MultiIndex.from_product([list(pseud.values()), TYPES, PHASES], names=['Ωφελούμενος', 'Τύπος', 'Φάση'])
missing = full.difference(cells.index)
single_trainer = cells[(cells.index.get_level_values('Τύπος') == TYPES[1]) & (cells == 1)]
print(f'\ncells with data: {len(cells)} / 270   missing: {len(missing)}')
for m in missing:
    print('  MISSING', m[0], m[1], 'phase', m[2][5])
print(f'trainer cells with one rating only: {len(single_trainer)}',
      [(p, ph[5]) for p, _, ph in single_trainer.index])

# ─── 5. outputs ───────────────────────────────────────────────────────────────
torder = {t: i for i, t in enumerate(TYPES)}
porder = {p: i for i, p in enumerate(PHASES)}
ratings = ratings.assign(_t=ratings['Τύπος'].map(torder), _p=ratings['Φάση'].map(porder)) \
    .sort_values(['_t', 'Ωφελούμενος', '_p', 'rater']).drop(columns=['_t', '_p'])
ratings.to_excel(args.ratings, index=False)

agg = ratings.groupby(['Ωφελούμενος', 'Τύπος', 'Φάση'], sort=False)
out = agg[Q].mean()
out['n_raters'] = agg.size()
out = out.reset_index()
out = out.assign(_t=out['Τύπος'].map(torder), _p=out['Φάση'].map(porder)) \
    .sort_values(['_t', 'Ωφελούμενος', '_p']).drop(columns=['_t', '_p'])
out.to_excel(args.out, index=False)

pd.DataFrame({'pseudonym': list(pseud.values()), 'name': list(pseud.keys())}).to_csv(args.map, index=False)

print(f'\nexport  sha256 {sha(args.raw)}\nsupp    sha256 {supp_sha}')
print(f'ratings rows {len(ratings)} ({(ratings.origin == "export").sum()} export + {(ratings.origin == "supplementary").sum()} supplementary) → {args.ratings}')
print(f'dataset rows {len(out)}, participants {out["Ωφελούμενος"].nunique()}, dup policy {args.dup_policy}, conflicts {len(conflicts)} → {args.out}')
print(f'mapping → {args.map}  (PRIVATE — DO NOT COMMIT)')
if missing.size:
    sys.exit('dataset is incomplete — see MISSING lines above')
