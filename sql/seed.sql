COPY customers FROM '/home/runner/work/sql-product-analytics-labs/sql-product-analytics-labs/data/samples/customers.csv' WITH (HEADER, DELIMITER ',');
COPY products FROM '/home/runner/work/sql-product-analytics-labs/sql-product-analytics-labs/data/samples/products.csv' WITH (HEADER, DELIMITER ',');
COPY orders FROM '/home/runner/work/sql-product-analytics-labs/sql-product-analytics-labs/data/samples/orders.csv' WITH (HEADER, DELIMITER ',');
COPY order_items FROM '/home/runner/work/sql-product-analytics-labs/sql-product-analytics-labs/data/samples/order_items.csv' WITH (HEADER, DELIMITER ',');
COPY events FROM '/home/runner/work/sql-product-analytics-labs/sql-product-analytics-labs/data/samples/events.csv' WITH (HEADER, DELIMITER ',');
COPY marketing_experiments FROM '/home/runner/work/sql-product-analytics-labs/sql-product-analytics-labs/data/samples/marketing_experiments.csv' WITH (HEADER, DELIMITER ',');
