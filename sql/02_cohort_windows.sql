CREATE OR REPLACE TABLE customers AS SELECT * FROM read_csv_auto('data/processed/customers.csv', header=true);
CREATE OR REPLACE TABLE orders    AS SELECT * FROM read_csv_auto('data/processed/orders.csv', header=true);
WITH base AS (
  SELECT c.customer_id,
         date_trunc('month', c.signup_date) AS cohort_month,
         date_trunc('month', o.order_date)  AS activity_month
  FROM customers c LEFT JOIN orders o USING(customer_id)
),
curve AS (
  SELECT cohort_month,
         datediff('month', cohort_month, activity_month) AS m,
         COUNT(DISTINCT customer_id) AS active_users
  FROM base WHERE activity_month IS NOT NULL GROUP BY 1,2
),
denom AS ( SELECT cohort_month, COUNT(*) cohort_size FROM customers GROUP BY 1 )
SELECT strftime(cohort_month, '%Y-%m') AS cohort,
       m, ROUND(100.0*active_users/NULLIF(cohort_size,0),2) AS active_pct
FROM curve JOIN denom USING(cohort_month)
WHERE m BETWEEN 0 AND 5
ORDER BY cohort, m;
