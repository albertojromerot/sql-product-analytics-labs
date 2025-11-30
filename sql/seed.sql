COPY customers FROM 'data/samples/customers.csv' WITH (HEADER, DELIMITER ',');
COPY products FROM 'data/samples/products.csv' WITH (HEADER, DELIMITER ',');
COPY orders FROM 'data/samples/orders.csv' WITH (HEADER, DELIMITER ',');
COPY order_items FROM 'data/samples/order_items.csv' WITH (HEADER, DELIMITER ',');
COPY events FROM 'data/samples/events.csv' WITH (HEADER, DELIMITER ',');
COPY marketing_experiments FROM 'data/samples/marketing_experiments.csv' WITH (HEADER, DELIMITER ',');
