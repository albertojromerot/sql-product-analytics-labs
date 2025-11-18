# %% [markdown]
# # 01 — Retention Cohorts
import duckdb, pandas as pd, matplotlib.pyplot as plt
con=duckdb.connect(); con.execute(open('sql/01_retention_joins.sql').read()); df=con.fetchdf()
fig=plt.figure(figsize=(8,4)); plt.plot(df['cohort'], df['retention_90d_pct'])
plt.xticks(rotation=45, ha='right'); plt.tight_layout()
plt.savefig('assets/retention_line.png'); print('Saved assets/retention_line.png')
