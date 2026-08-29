CREATE TABLE IF NOT EXISTS orders (
  id bigserial PRIMARY KEY,
  customer_id integer NOT NULL,
  payload text NOT NULL
);
INSERT INTO orders(customer_id, payload)
SELECT (n % 10000) + 1, repeat('order-payload-', 4)
FROM generate_series(1, 500000) AS n;
CREATE INDEX IF NOT EXISTS orders_customer_id_idx ON orders(customer_id);
ANALYZE orders;
