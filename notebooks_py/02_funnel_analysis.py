# %% [markdown]
# # 02 — Funnel Analysis
import duckdb, pandas as pd, matplotlib.pyplot as plt
con=duckdb.connect(); con.execute(open('sql/03_funnel_ctes.sql').read()); row=con.fetchdf().iloc[0]
stages=['page','product','cart','checkout']; vals=[row[c] for c in row.index]
fig=plt.figure(figsize=(6,4)); plt.bar(stages, vals); plt.tight_layout()
plt.savefig('assets/funnel.png'); print('Saved assets/funnel.png')
