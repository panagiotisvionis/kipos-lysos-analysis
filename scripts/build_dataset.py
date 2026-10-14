"""
build_dataset.py — Reproducible construction of the analysis dataset.

INPUT  (never committed, contains names): raw platform export (300 rows)
OUTPUT (committed): data/action_responses_pseudonymized.xlsx (270 rows)

Steps
1. Beneficiaries: one record per person × phase (no missing).
2. Trainers/educators: two raters per person × phase → item-wise MEAN of the two.
   Where only one rater responded, that single rating is used.
3. Independent observer: single rater; 2/4/4 person-phase records missing in A/B/C.
   One person-phase has a duplicate observer submission; the first submission is
   kept (consistent with scripts/statistical_analysis.py). Missing person-phase
   records are imputed with the PHASE-LEVEL ITEM MEAN across observed participants
   (mean imputation).
4. Participant names are replaced by stable pseudonyms P01…P30 (mapping kept
   offline, not in the repository).
5. Items remain on the original 0–4 export scale; analysis scripts add 1 → 1–5.
"""
import sys, pandas as pd, numpy as np
RAW, OUT, MAP = sys.argv[1], sys.argv[2], sys.argv[3]
q=[f'Q{i}' for i in range(1,12)]
raw=pd.read_excel(RAW)
tcol=[c for c in raw.columns if c.startswith('Τύπος')][0]
ids=sorted(raw.loc[raw[tcol]=='Ωφελούμενος/η','Ωφελούμενος'].unique())
phases=sorted(raw['Φάση'].unique())
full=pd.MultiIndex.from_product([ids,phases],names=['Ωφελούμενος','Φάση'])

def build(typ):
    sub=raw[raw[tcol]==typ]
    if typ!='Εκπαιδευτής/τρια':          # single-rater sources: keep first submission
        sub=sub.drop_duplicates(subset=['Ωφελούμενος','Φάση'],keep='first')
    g=sub.groupby(['Ωφελούμενος','Φάση'])[q].mean().reindex(full)
    for ph in phases:
        idx=g.index.get_level_values('Φάση')==ph
        g.loc[idx]=g.loc[idx].fillna(g.loc[idx].mean())
    g=g.reset_index(); g.insert(1,'Τύπος',typ); return g

out=pd.concat([build('Ωφελούμενος/η'),build('Εκπαιδευτής/τρια'),build('Ανεξάρτητος παρατηρητής')],ignore_index=True)
pseud={name:f'P{i+1:02d}' for i,name in enumerate(ids)}
pd.DataFrame({'pseudonym':pseud.values(),'name':pseud.keys()}).to_csv(MAP,index=False)
out['Ωφελούμενος']=out['Ωφελούμενος'].map(pseud)
out.to_excel(OUT,index=False)
print(f"wrote {OUT}: {len(out)} rows, {out['Ωφελούμενος'].nunique()} participants; mapping → {MAP} (DO NOT COMMIT)")
