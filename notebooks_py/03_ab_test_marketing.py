# %% [markdown]
# # 03 — A/B Test (Wald z)
import pandas as pd, duckdb, math, matplotlib.pyplot as plt
con=duckdb.connect()
con.execute("CREATE OR REPLACE TABLE marketing AS SELECT * FROM read_csv_auto('data/processed/marketing_experiments.csv', header=true)")
ab=con.execute("SELECT group AS grp, COUNT(*) n, SUM(CASE WHEN converted THEN 1 ELSE 0 END) x FROM marketing GROUP BY 1 ORDER BY 1").fetchdf()
pA=ab.loc[ab.grp=='A','x'].iloc[0]/ab.loc[ab.grp=='A','n'].iloc[0]; pB=ab.loc[ab.grp=='B','x'].iloc[0]/ab.loc[ab.grp=='B','n'].iloc[0]
p=(ab.x.sum())/(ab.n.sum()); se=math.sqrt(p*(1-p)*(1/ab.loc[ab.grp=='A','n'].iloc[0]+1/ab.loc[ab.grp=='B','n'].iloc[0])); z=(pB-pA)/se
print("Lift:", pB/pA-1, "Z:", z)
fig=plt.figure(figsize=(4,4)); plt.bar(['A','B'], [pA,pB]); plt.tight_layout()
plt.savefig('assets/ab_uplift.png'); print('Saved assets/ab_uplift.png')
