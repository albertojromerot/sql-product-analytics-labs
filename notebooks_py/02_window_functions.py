# %% [markdown]
# # 02 - Window functions
# Use ranking and moving averages to understand cohorts and retention.

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
# Ranking top customers by revenue
customer_revenue = con.execute('''
    SELECT c.customer_id,
           c.country,
           SUM(o.revenue_usd) AS revenue,
           ROW_NUMBER() OVER (ORDER BY SUM(o.revenue_usd) DESC) AS rn,
           RANK() OVER (ORDER BY SUM(o.revenue_usd) DESC) AS rnk
    FROM orders o
    JOIN customers c USING (customer_id)
    GROUP BY 1,2
    ORDER BY revenue DESC
''').fetchdf()

customer_revenue.head()

# %%
# Moving averages: 7-day and 28-day revenue
order_daily = con.execute('''
    SELECT date_trunc('day', order_ts) AS day,
           SUM(revenue_usd) AS revenue
    FROM orders
    GROUP BY 1
    ORDER BY 1
''').fetchdf()
order_daily['ma7'] = order_daily['revenue'].rolling(window=7).mean()
order_daily['ma28'] = order_daily['revenue'].rolling(window=28).mean()

plt.figure(figsize=(10,6))
plt.plot(order_daily['day'], order_daily['revenue'], label='Daily revenue', alpha=0.5)
plt.plot(order_daily['day'], order_daily['ma7'], label='7-day MA', linewidth=2)
plt.plot(order_daily['day'], order_daily['ma28'], label='28-day MA', linewidth=2)
plt.title('Revenue moving averages')
plt.xlabel('Day')
plt.ylabel('Revenue (USD)')
plt.legend()
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig('assets/window_revenue_ma.png', bbox_inches='tight')
plt.show()

# %%
# Cohort retention using first purchase month
cohorts = con.execute('''
    WITH first_purchase AS (
        SELECT customer_id, MIN(date_trunc('month', order_ts)) AS cohort_month
        FROM orders
        GROUP BY 1
    ), purchases AS (
        SELECT o.customer_id,
               date_trunc('month', o.order_ts) AS purchase_month
        FROM orders o
    )
    SELECT fp.cohort_month,
           p.purchase_month,
           COUNT(DISTINCT p.customer_id) AS customers
    FROM purchases p
    JOIN first_purchase fp ON p.customer_id = fp.customer_id
    GROUP BY 1,2
    ORDER BY 1,2
''').fetchdf()

cohort_pivot = cohorts.pivot(index='cohort_month', columns='purchase_month', values='customers').fillna(0)
cohort_sizes = cohort_pivot.iloc[:,0]
retention = cohort_pivot.divide(cohort_sizes, axis=0)

plt.figure(figsize=(10,6))
sns.heatmap(retention.iloc[:, :4], annot=True, fmt='.0%', cmap='Blues')
plt.title('3-month retention by cohort')
plt.xlabel('Purchase month')
plt.ylabel('Cohort (first purchase)')
plt.tight_layout()
plt.savefig('assets/window_cohort_retention.png', bbox_inches='tight')
plt.show()

# %% [markdown]
# Business takeaway: Window analyses highlight seasonality and cohorts with superior retention so marketing can target similar audiences.
