import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta

np.random.seed(42)

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
SAMPLES_DIR = DATA_DIR / "samples"
SYNTHETIC_DIR = DATA_DIR / "synthetic"
SQL_DIR = BASE_DIR / "sql"

SAMPLES_DIR.mkdir(parents=True, exist_ok=True)
SYNTHETIC_DIR.mkdir(parents=True, exist_ok=True)
SQL_DIR.mkdir(parents=True, exist_ok=True)

END_DATE = pd.Timestamp("2024-12-31")
START_DATE = END_DATE - pd.DateOffset(months=24)


def random_dates(start: pd.Timestamp, end: pd.Timestamp, n: int) -> pd.Series:
    delta = (end - start).days
    return start + pd.to_timedelta(np.random.randint(0, delta + 1, size=n), unit="D")


def generate_customers(n_customers: int = 20000) -> pd.DataFrame:
    """Create the core customer dimension with spec-aligned categories."""

    countries = ["CO", "US", "MX", "AR", "CL", "PE", "BR", "ES"]
    age_bands = ["18-24", "25-34", "35-44", "45-54", "55-64", "65+"]
    income_bands = ["<1k", "1-2k", "2-4k", "4-6k", "6-10k", "10k+"]
    channels = ["organic", "paid", "referral", "partner"]

    signup_dates = random_dates(START_DATE, END_DATE, n_customers)
    df = pd.DataFrame({
        "customer_id": np.arange(1, n_customers + 1),
        "signup_date": signup_dates,
        "country": np.random.choice(countries, size=n_customers),
        "age_band": np.random.choice(age_bands, size=n_customers, p=[0.18, 0.32, 0.22, 0.14, 0.09, 0.05]),
        "income_band": np.random.choice(income_bands, size=n_customers, p=[0.14, 0.2, 0.22, 0.2, 0.16, 0.08]),
        "channel": np.random.choice(channels, size=n_customers, p=[0.48, 0.22, 0.18, 0.12]),
    })
    return df


def generate_products() -> pd.DataFrame:
    categories = [
        ("Analytics", 49, 299),
        ("Marketing", 29, 199),
        ("Productivity", 19, 149),
        ("Finance", 39, 249),
    ]
    product_rows = []
    product_id = 1
    for cat, low, high in categories:
        for _ in range(10):
            price = np.random.uniform(low, high)
            product_rows.append({
                "product_id": product_id,
                "category": cat,
                "price_usd": round(price, 2),
            })
            product_id += 1
    return pd.DataFrame(product_rows)


def generate_orders(customers: pd.DataFrame, n_orders: int = 30000) -> pd.DataFrame:
    customer_ids = customers["customer_id"].values
    # weight by recency to create more recent orders
    signup_rank = customers["signup_date"].rank(method="first")
    weights = 0.3 + 0.7 * (signup_rank / signup_rank.max())
    weights = weights / weights.sum()

    chosen_customers = np.random.choice(customer_ids, size=n_orders, p=weights)
    signup_map = customers.set_index("customer_id")["signup_date"]
    order_dates = []
    for cid in chosen_customers:
        start = signup_map.loc[cid]
        order_dates.append(random_dates(start, END_DATE, 1)[0])
    order_dates = pd.to_datetime(order_dates)

    sources = ["web", "app", "partner", "sales"]
    df = pd.DataFrame({
        "order_id": np.arange(1, n_orders + 1),
        "customer_id": chosen_customers,
        "order_ts": order_dates,
        "source": np.random.choice(sources, size=n_orders, p=[0.55, 0.25, 0.12, 0.08]),
    })
    return df


def generate_order_items(orders: pd.DataFrame, products: pd.DataFrame) -> pd.DataFrame:
    """Guarantee every order has at least one line item while preserving realism."""

    product_ids = products["product_id"].values
    prices = products.set_index("product_id")["price_usd"].to_dict()

    rows = []
    # ensure coverage: each order gets 1-3 products, no replacement to avoid duplicates per order
    for order_id in orders["order_id"]:
        n_items = np.random.choice([1, 2, 3], p=[0.55, 0.3, 0.15])
        chosen_products = np.random.choice(product_ids, size=n_items, replace=False)
        for pid in chosen_products:
            qty = np.random.randint(1, 5)
            base_price = prices[pid]
            price_noise = np.random.normal(0, 3)
            unit_price = max(base_price + price_noise, base_price * 0.7)
            rows.append({
                "order_id": order_id,
                "product_id": pid,
                "qty": int(qty),
                "unit_price_usd": round(unit_price, 2),
            })

    return pd.DataFrame(rows)


def generate_events(customers: pd.DataFrame, target_events: int = 80000) -> pd.DataFrame:
    event_types = ["visit", "signup", "trial_start", "purchase", "cancel"]
    probs = [0.55, 0.1, 0.12, 0.18, 0.05]

    events_per_customer = np.random.poisson(4, size=len(customers))
    scale = target_events / events_per_customer.sum()
    events_per_customer = np.maximum(1, (events_per_customer * scale).astype(int))

    rows = []
    for customer_id, signup_date, epc in zip(customers["customer_id"], customers["signup_date"], events_per_customer):
        timestamps = random_dates(signup_date, END_DATE, epc)
        timestamps = np.sort(timestamps)
        event_types_for_customer = np.random.choice(event_types, size=epc, p=probs)
        for ts, et in zip(timestamps, event_types_for_customer):
            rows.append({
                "event_id": len(rows) + 1,
                "customer_id": customer_id,
                "event_ts": ts,
                "event_type": et,
            })
    df = pd.DataFrame(rows)
    return df


def generate_marketing_experiments(customers: pd.DataFrame, n_participants: int = 30000) -> pd.DataFrame:
    # Cap participant draw to the available customer pool to avoid oversampling errors
    participant_count = min(n_participants, len(customers))
    chosen_customers = np.random.choice(
        customers["customer_id"].values, size=participant_count, replace=False
    )
    groups = np.random.choice(["A", "B"], size=participant_count)
    exposures = random_dates(
        START_DATE + pd.DateOffset(months=1), END_DATE, participant_count
    )

    base_rate = 0.12
    lift = 0.04
    conversions = []
    conversion_ts = []
    for grp, exp_ts in zip(groups, exposures):
        prob = base_rate + (lift if grp == "B" else 0)
        converted = np.random.rand() < prob
        conversions.append(converted)
        if converted:
            delay_days = np.random.randint(1, 30)
            conversion_ts.append(exp_ts + timedelta(days=int(delay_days)))
        else:
            conversion_ts.append(pd.NaT)

    df = pd.DataFrame({
        "exp_id": np.arange(1, participant_count + 1),
        "user_id": chosen_customers,
        "group": groups,
        "exposed_ts": exposures,
        "converted": conversions,
        "conversion_ts": conversion_ts,
    })
    return df


def compute_order_revenue(orders: pd.DataFrame, order_items: pd.DataFrame) -> pd.DataFrame:
    revenue = order_items.assign(line_total=lambda d: d["qty"] * d["unit_price_usd"])
    revenue = revenue.groupby("order_id")["line_total"].sum().rename("revenue_usd")
    orders = orders.join(revenue, on="order_id")
    return orders


def write_schema_and_seed(sample_dir: Path):
    schema = f"""
CREATE TABLE customers (
    customer_id INTEGER PRIMARY KEY,
    signup_date DATE,
    country VARCHAR,
    age_band VARCHAR,
    income_band VARCHAR,
    channel VARCHAR
);

CREATE TABLE products (
    product_id INTEGER PRIMARY KEY,
    category VARCHAR,
    price_usd DECIMAL(10,2)
);

CREATE TABLE orders (
    order_id INTEGER PRIMARY KEY,
    customer_id INTEGER,
    order_ts TIMESTAMP,
    revenue_usd DECIMAL(10,2),
    source VARCHAR
);

CREATE TABLE order_items (
    order_id INTEGER,
    product_id INTEGER,
    qty INTEGER,
    unit_price_usd DECIMAL(10,2)
);

CREATE TABLE events (
    event_id INTEGER PRIMARY KEY,
    customer_id INTEGER,
    event_ts TIMESTAMP,
    event_type VARCHAR
);

CREATE TABLE marketing_experiments (
    exp_id INTEGER PRIMARY KEY,
    user_id INTEGER,
    "group" VARCHAR,
    exposed_ts TIMESTAMP,
    converted BOOLEAN,
    conversion_ts TIMESTAMP
);
"""
    seed_lines = []
    for table in ["customers", "products", "orders", "order_items", "events", "marketing_experiments"]:
        seed_lines.append(
            f"COPY {table} FROM '{sample_dir / (table + '.csv')}' WITH (HEADER, DELIMITER ',');"
        )
    (SQL_DIR / "schema.sql").write_text(schema.strip() + "\n")
    (SQL_DIR / "seed.sql").write_text("\n".join(seed_lines) + "\n")


def save_samples(df: pd.DataFrame, name: str, sample_size: int = 500):
    df.to_csv(SYNTHETIC_DIR / f"{name}.csv", index=False)
    df.sample(n=min(sample_size, len(df)), random_state=42).to_csv(
        SAMPLES_DIR / f"{name}.csv", index=False
    )


def main():
    customers = generate_customers()
    products = generate_products()
    orders = generate_orders(customers)
    order_items = generate_order_items(orders, products)
    orders = compute_order_revenue(orders, order_items)
    events = generate_events(customers)
    marketing = generate_marketing_experiments(customers)

    datasets = {
        "customers": customers,
        "products": products,
        "orders": orders,
        "order_items": order_items,
        "events": events,
        "marketing_experiments": marketing,
    }

    for name, df in datasets.items():
        save_samples(df, name)

    write_schema_and_seed(SAMPLES_DIR)

    print("Row count summary:")
    for name, df in datasets.items():
        print(f"- {name}: {len(df):,} rows")


if __name__ == "__main__":
    main()
