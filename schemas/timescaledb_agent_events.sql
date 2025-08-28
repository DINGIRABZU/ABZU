-- TimescaleDB schema and migration script for agent_events
CREATE TABLE IF NOT EXISTS agent_events (
    time        TIMESTAMPTZ NOT NULL,
    agent_id    TEXT NOT NULL,
    event_type  TEXT NOT NULL,
    payload     JSONB DEFAULT '{}'::JSONB,
    PRIMARY KEY (time, agent_id)
);

-- Convert to hypertable for time-series performance
SELECT create_hypertable('agent_events', 'time', if_not_exists => TRUE);

-- Indexes to accelerate lookups
CREATE INDEX IF NOT EXISTS agent_events_agent_idx ON agent_events (agent_id, time DESC);
CREATE INDEX IF NOT EXISTS agent_events_type_idx ON agent_events (event_type);

-- Retention policy: keep 30 days of data
SELECT add_retention_policy('agent_events', INTERVAL '30 days');
