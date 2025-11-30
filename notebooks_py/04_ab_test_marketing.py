# %% [markdown]
# # 04 - A/B test for marketing
# Evaluate experiment conversion with a z-test.

# %%
import duckdb, pandas as pd, seaborn as sns, matplotlib.pyplot as plt, numpy as np
from pathlib import Path

sns.set_theme(style='whitegrid')


def get_project_root() -> Path:
    if "__file__" in globals():
        start = Path(__file__).resolve()
    else:
        start = Path.cwd().resolve()
    for path in [start, *start.parents]:
        if (path / "sql" / "schema.sql").exists():
            return path
    return start


PROJECT_ROOT = get_project_root()
SCHEMA_PATH = PROJECT_ROOT / "sql" / "schema.sql"
SEED_PATH   = PROJECT_ROOT / "sql" / "seed.sql"

con = duckdb.connect(database=':memory:')
con.execute(SCHEMA_PATH.read_text())
con.execute(SEED_PATH.read_text())

tables = ['customers','products','orders','order_items','events','marketing_experiments']
for table in tables:
    df = con.execute(f"SELECT * FROM {table} LIMIT 5").fetchdf()
    display(df)

# %%
import statsmodels.stats.api as sms

exp = con.execute('''
    SELECT "group" AS grp,
           COUNT(*) AS users,
           SUM(CASE WHEN converted THEN 1 ELSE 0 END) AS converters
    FROM marketing_experiments
    GROUP BY 1
''').fetchdf()

exp['rate'] = exp['converters'] / exp['users']
exp

# %%
# Two-proportion z-test
A = exp.loc[exp['grp']=='A']
B = exp.loc[exp['grp']=='B']
count = np.array([int(A['converters']), int(B['converters'])])
nobs = np.array([int(A['users']), int(B['users'])])
stat, pval = sms.proportions_ztest(count, nobs)
stat, pval

# %%
# Plot conversion rates with 95% CI
fig, ax = plt.subplots(figsize=(6,5))
ax.bar(exp['grp'], exp['rate'], color=['#2563eb', '#7c3aed'])
ci_low, ci_upp = sms.proportion_confint(exp['converters'], exp['users'], alpha=0.05, method='normal')
ax.errorbar(exp['grp'], exp['rate'], yerr=[exp['rate']-ci_low, ci_upp-exp['rate']], fmt='none', c='black', capsize=5)
ax.set_ylabel('Conversion rate')
ax.set_title('Experiment conversion by group (95% CI)')
plt.tight_layout()
plt.savefig('assets/ab_conversion_rates.png', bbox_inches='tight')
plt.show()

# %% [markdown]
# Business takeaway: If group B materially outperforms group A with a low p-value, roll out the winning creative to the broader audience.
