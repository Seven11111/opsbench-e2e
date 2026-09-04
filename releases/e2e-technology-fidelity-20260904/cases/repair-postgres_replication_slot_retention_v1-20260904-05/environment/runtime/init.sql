CREATE TABLE IF NOT EXISTS wal_probe(id bigserial PRIMARY KEY, payload text NOT NULL); INSERT INTO wal_probe(payload) VALUES ('baseline');
