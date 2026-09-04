CREATE TABLE IF NOT EXISTS orders(id integer PRIMARY KEY, value text NOT NULL); INSERT INTO orders VALUES (1, 'baseline'), (2, 'baseline') ON CONFLICT DO NOTHING;
