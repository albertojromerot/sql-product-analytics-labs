# %% [markdown]
# # Lab 01 – Joins & Revenue KPIs in DuckDB
#
# This lab walks through the core joins that power product-analytics revenue questions:
# - What is total revenue over time?
# - Which products and categories drive revenue?
# - Who are our best customers by lifetime value?
# - How do signup cohorts perform over time?

# %% [markdown]
# ## Data model recap
# Tables used in this lab:
# - **customers**: one row per customer with signup metadata (country, channel).
# - **orders**: header-level information for each purchase including timestamps.
# - **order_items**: line items connected to orders and products.
# - **products**: catalog with category and price attributes.
# - **events** and **marketing_experiments**: behavioral and experiment context (not used directly here but available for extensions).
#
# Relationships:
# - customers 1—* orders 1—* order_items *—1 products
# - customers 1—* events
# - customers 1—* marketing_experiments (via participants table in other labs)

# %%
import os
from pathlib import Path

import duckdb
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from IPython.display import display

sns.set_theme(style="whitegrid")


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

# Change to project root so relative paths in seed.sql work
os.chdir(PROJECT_ROOT)

con = duckdb.connect(database=":memory:")
con.execute(SCHEMA_PATH.read_text())
con.execute(SEED_PATH.read_text())

print("Tables loaded:", con.execute("SHOW TABLES").fetchall())

# %% [markdown]
# ## Basic joins & daily revenue
# *Definition*: **Revenue** = sum of `qty * unit_price_usd` across order items.
#
# Steps:
# 1. Join `orders` and `order_items` on `order_id`.
# 2. Aggregate revenue by order date (derived from `order_ts`) to view daily trends.

# %%
daily_revenue = con.execute(
    """
    WITH itemized AS (
        SELECT
            CAST(o.order_ts AS DATE) AS order_date,
            oi.qty * oi.unit_price_usd AS line_revenue
        FROM orders o
        JOIN order_items oi USING (order_id)
    )
    SELECT
        order_date,
        SUM(line_revenue) AS daily_revenue_usd
    FROM itemized
    GROUP BY order_date
    ORDER BY order_date
    """
).fetchdf()

display(daily_revenue.head())

plt.figure(figsize=(10, 4))
plt.plot(daily_revenue["order_date"], daily_revenue["daily_revenue_usd"], color="#2563eb")
plt.title("Daily revenue")
plt.xlabel("Order date")
plt.ylabel("Revenue (USD)")
plt.xticks(rotation=30)
plt.tight_layout()
plt.savefig('assets/joins_daily_revenue.png', bbox_inches='tight')
plt.show()

# %% [markdown]
# **Observations**
# - Revenue is stable with seasonal bumps driven by simulated campaign periods.
# - Small variance shows the dataset is balanced enough for KPI demos.

# %% [markdown]
# ## Product and category performance
# We want to see which categories and products contribute most to revenue.
# The query aggregates revenue at both levels to reveal the long-tail pattern.

# %%
category_perf = con.execute(
    """
    SELECT
        p.category,
        SUM(oi.qty * oi.unit_price_usd) AS revenue_usd,
        COUNT(DISTINCT oi.product_id) AS products_sold
    FROM order_items oi
    JOIN products p USING (product_id)
    GROUP BY 1
    ORDER BY revenue_usd DESC
    """
).fetchdf()

display(category_perf)

plt.figure(figsize=(9, 4))
ax = sns.barplot(data=category_perf, x="revenue_usd", y="category", color="#10b981")
ax.set_title("Revenue by category")
ax.set_xlabel("Revenue (USD)")
ax.set_ylabel("Category")
plt.tight_layout()
plt.savefig('assets/joins_revenue_by_category.png', bbox_inches='tight')
plt.show()

product_perf = con.execute(
    """
    SELECT
        p.product_name,
        p.category,
        SUM(oi.qty * oi.unit_price_usd) AS revenue_usd,
        COUNT(*) AS item_lines
    FROM order_items oi
    JOIN products p USING (product_id)
    GROUP BY 1, 2
    ORDER BY revenue_usd DESC
    LIMIT 10
    """
).fetchdf()

display(product_perf)

# %% [markdown]
# **Insights**
# - A handful of categories account for most revenue; others contribute as a long tail.
# - Top products span multiple categories, which is useful when planning merchandising updates.

# %% [markdown]
# ## Customer lifetime value snapshot
# *Definition*: **Lifetime value (LTV)** = total revenue attributed to a customer across all orders.
# We compute order count and revenue per customer to spot high-value segments.

# %%
customer_ltv = con.execute(
    """
    SELECT
        c.customer_id,
        c.country,
        c.channel,
        COUNT(DISTINCT o.order_id) AS orders,
        SUM(oi.qty * oi.unit_price_usd) AS revenue_usd
    FROM customers c
    JOIN orders o USING (customer_id)
    JOIN order_items oi USING (order_id)
    GROUP BY 1, 2, 3
    ORDER BY revenue_usd DESC
    """
).fetchdf()

display(customer_ltv.head())

summary = customer_ltv["revenue_usd"].describe(percentiles=[0.5, 0.75, 0.9, 0.95])
print("\nRevenue distribution summary (USD):")
print(summary)

plt.figure(figsize=(8, 4))
sns.histplot(customer_ltv["revenue_usd"], bins=30, color="#f97316")
plt.title("Customer LTV distribution")
plt.xlabel("Lifetime revenue (USD)")
plt.ylabel("Customers")
plt.tight_layout()
plt.show()

# %% [markdown]
# **Insights**
# - LTV is right-skewed: most customers sit near the median while a small set drive outsized revenue.
# - Acquisition channel and country columns help segment high-value cohorts for targeted campaigns.

# %% [markdown]
# ## Signup-month cohorts (revenue by order month)
# A light cohort view comparing signup month to the order month shows how spend evolves.

# %%
cohort_revenue = con.execute(
    """
    WITH customer_signup AS (
        SELECT
            customer_id,
            date_trunc('month', signup_date) AS signup_month
        FROM customers
    ), revenue_by_month AS (
        SELECT
            cs.signup_month,
            date_trunc('month', o.order_ts) AS order_month,
            SUM(oi.qty * oi.unit_price_usd) AS revenue_usd
        FROM customer_signup cs
        JOIN orders o USING (customer_id)
        JOIN order_items oi USING (order_id)
        GROUP BY 1, 2
    )
    SELECT
        signup_month,
        order_month,
        revenue_usd
    FROM revenue_by_month
    ORDER BY signup_month, order_month
    """
).fetchdf()

cohort_pivot = cohort_revenue.pivot(
    index="signup_month", columns="order_month", values="revenue_usd"
).fillna(0)

display(cohort_pivot)

plt.figure(figsize=(10, 5))
sns.heatmap(cohort_pivot, cmap="Blues", cbar_kws={"label": "Revenue (USD)"})
plt.title("Revenue by signup cohort and order month")
plt.xlabel("Order month")
plt.ylabel("Signup month")
plt.tight_layout()
plt.show()

# %% [markdown]
# **Observations**
# - Cohorts show sustained revenue several months after signup, indicating healthy repeat purchasing.
# - Later cohorts maintain or slightly improve early-month revenue, a sign of improving acquisition quality.

# %% [markdown]
# ## Final takeaways
# - Daily revenue is steady with identifiable peaks that can be traced to campaigns.
# - A few categories dominate revenue, but there is a healthy product long tail to nurture.
# - High-value customers are concentrated in specific channels/countries, enabling targeted retention.
# - Cohort heatmaps confirm continued spending beyond the first purchase window.
