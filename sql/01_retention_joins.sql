PRAGMA threads=4;
CREATE OR REPLACE TABLE customers AS SELECT * FROM read_csv_auto('data/processed/customers.csv', header=true);
CREATE OR REPLACE TABLE orders    AS SELECT * FROM read_csv_auto('data/processed/orders.csv', header=true);
WITH cohorts AS (
  SELECT customer_id, strftime(signup_date, '%Y-%m') AS cohort FROM customers
),
activity AS (
  SELECT customer_id, MIN(order_date) AS first_order, MAX(order_date) AS last_order FROM orders GROUP BY 1
),
retention AS (
  SELECT c.cohort, COUNT(*) cohort_size,
         SUM(CASE WHEN julianday(last_order)-julianday(first_order) >= 90 THEN 1 ELSE 0 END) retained_90d
  FROM cohorts c LEFT JOIN activity a USING(customer_id)
  GROUP BY 1
)
SELECT cohort, cohort_size, retained_90d,
       ROUND(100.0*retained_90d/NULLIF(cohort_size,0),2) AS retention_90d_pct
FROM retention ORDER BY cohort;
