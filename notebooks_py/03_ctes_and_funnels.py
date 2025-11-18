# %% [markdown]
# # 03 - CTEs and funnels
# Model the visit→signup→purchase journey with CTEs.

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
# Build funnel with CTEs
funnel = con.execute('''
    WITH visits AS (
        SELECT customer_id, MIN(event_ts) AS visit_ts
        FROM events WHERE event_type='visit'
        GROUP BY 1
    ), signups AS (
        SELECT customer_id, MIN(event_ts) AS signup_ts
        FROM events WHERE event_type='signup'
        GROUP BY 1
    ), purchases AS (
        SELECT customer_id, MIN(event_ts) AS purchase_ts
        FROM events WHERE event_type='purchase'
        GROUP BY 1
    )
    SELECT v.customer_id,
           v.visit_ts,
           s.signup_ts,
           p.purchase_ts
    FROM visits v
    LEFT JOIN signups s USING (customer_id)
    LEFT JOIN purchases p USING (customer_id)
''').fetchdf()

steps = {
    'visit': funnel['visit_ts'].notna().sum(),
    'signup': funnel['signup_ts'].notna().sum(),
    'purchase': funnel['purchase_ts'].notna().sum(),
}
conversion_rates = {
    'visit_to_signup': steps['signup'] / steps['visit'],
    'signup_to_purchase': steps['purchase'] / steps['signup'],
    'visit_to_purchase': steps['purchase'] / steps['visit'],
}
steps, conversion_rates

# %%
# Funnel bar chart
funnel_order = ['visit', 'signup', 'purchase']
counts = [steps[s] for s in funnel_order]
plt.figure(figsize=(7,5))
sns.barplot(x=funnel_order, y=counts, palette='crest')
plt.title('Visit to purchase funnel counts')
plt.ylabel('Users')
plt.tight_layout()
plt.savefig('assets/cte_funnel_counts.png', bbox_inches='tight')
plt.show()

# %%
# Step-through rates over time
monthly = con.execute('''
    WITH first_events AS (
        SELECT customer_id,
               MIN(CASE WHEN event_type='visit' THEN event_ts END) AS first_visit,
               MIN(CASE WHEN event_type='signup' THEN event_ts END) AS first_signup,
               MIN(CASE WHEN event_type='purchase' THEN event_ts END) AS first_purchase
        FROM events
        GROUP BY 1
    )
    SELECT date_trunc('month', first_visit) AS month,
           COUNT(*) AS visitors,
           COUNT(first_signup) AS signups,
           COUNT(first_purchase) AS purchasers
    FROM first_events
    GROUP BY 1
    ORDER BY 1
''').fetchdf()

monthly['visit_to_signup'] = monthly['signups'] / monthly['visitors']
monthly['signup_to_purchase'] = monthly['purchasers'] / monthly['signups'].replace({0: pd.NA})

plt.figure(figsize=(10,6))
plt.plot(monthly['month'], monthly['visit_to_signup'], label='Visit → Signup')
plt.plot(monthly['month'], monthly['signup_to_purchase'], label='Signup → Purchase')
plt.title('Monthly funnel step-through rates')
plt.xlabel('Month')
plt.ylabel('Rate')
plt.legend()
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig('assets/cte_funnel_rates.png', bbox_inches='tight')
plt.show()

# %% [markdown]
# Business takeaway: Improving signup quality has outsized impact on purchases—focus on landing pages and onboarding where drop-off is highest.
