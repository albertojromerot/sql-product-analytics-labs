# %% [markdown]
# # 01 - Joins and KPIs
# Explore joins across customers, orders, and products to answer revenue questions.

# %%
import duckdb, pandas as pd, seaborn as sns, matplotlib.pyplot as plt, numpy as np
from pathlib import Path

sns.set_theme(style='whitegrid')

con = duckdb.connect(database=':memory:')
con.execute(Path('sql/schema.sql').read_text())
con.execute(Path('sql/seed.sql').read_text())

tables = ['customers','products','orders','order_items','events','marketing_experiments']
for table in tables:
    df = con.execute(f"SELECT * FROM {table} LIMIT 5").fetchdf()
    display(df)

# %%
# Revenue by country and month
rev_country_month = con.execute('''
    SELECT date_trunc('month', o.order_ts) AS month,
           c.country,
           SUM(o.revenue_usd) AS revenue
    FROM orders o
    JOIN customers c USING (customer_id)
    GROUP BY 1,2
    ORDER BY 1,2
''').fetchdf()

pivot = rev_country_month.pivot(index='month', columns='country', values='revenue').fillna(0)
ax = pivot.plot(figsize=(10,6))
ax.set_title('Monthly revenue by country')
ax.set_ylabel('Revenue (USD)')
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig('assets/joins_revenue_by_country.png', bbox_inches='tight')
plt.show()

# %%
# Top categories per country
cat_country = con.execute('''
    SELECT c.country,
           p.category,
           SUM(oi.qty * oi.unit_price_usd) AS revenue
    FROM order_items oi
    JOIN orders o USING (order_id)
    JOIN customers c USING (customer_id)
    JOIN products p USING (product_id)
    GROUP BY 1,2
    ORDER BY revenue DESC
''').fetchdf()

plt.figure(figsize=(10,6))
sns.barplot(data=cat_country, x='revenue', y='country', hue='category')
plt.title('Revenue by category and country')
plt.xlabel('Revenue (USD)')
plt.ylabel('Country')
plt.tight_layout()
plt.savefig('assets/joins_category_country.png', bbox_inches='tight')
plt.show()

# %%
# Channel performance overview
channel_perf = con.execute('''
    SELECT c.channel,
           COUNT(DISTINCT o.order_id) AS orders,
           SUM(o.revenue_usd) AS revenue,
           COUNT(DISTINCT o.customer_id) AS unique_customers
    FROM orders o
    JOIN customers c USING (customer_id)
    GROUP BY 1
    ORDER BY revenue DESC
''').fetchdf()

fig, ax1 = plt.subplots(figsize=(9,5))
sns.barplot(data=channel_perf, x='channel', y='revenue', ax=ax1, color='#2563eb')
ax1.set_title('Revenue by acquisition channel')
ax1.set_xlabel('Channel')
ax1.set_ylabel('Revenue (USD)')
plt.xticks(rotation=20)
plt.tight_layout()
plt.savefig('assets/joins_channel_revenue.png', bbox_inches='tight')
plt.show()

# %% [markdown]
# Business takeaway: Countries with sustained revenue growth and strong category-channel pairs identify where to double down on acquisition and merchandising.
