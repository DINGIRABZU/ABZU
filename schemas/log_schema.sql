CREATE TABLE channel_logs (
    id INTEGER PRIMARY KEY,
    channel_id INTEGER,
    message TEXT,
    created_at TIMESTAMP
);
