CREATE OR REPLACE TABLE events AS SELECT * FROM read_csv_auto('data/processed/events.csv', header=true);
WITH s AS (
  SELECT customer_id,
         MAX(event_type='page_view') v,
         MAX(event_type='product_view') p,
         MAX(event_type='add_to_cart') c,
         MAX(event_type='checkout') k
  FROM events GROUP BY 1
)
SELECT
  (SELECT COUNT(*) FROM s WHERE v) AS stage_1_page,
  (SELECT COUNT(*) FROM s WHERE p) AS stage_2_product,
  (SELECT COUNT(*) FROM s WHERE c) AS stage_3_cart,
  (SELECT COUNT(*) FROM s WHERE k) AS stage_4_checkout;
