-- Schema defining event to symbol mapping
CREATE TABLE IF NOT EXISTS event_symbol (
    event TEXT PRIMARY KEY,
    symbol TEXT NOT NULL
);

