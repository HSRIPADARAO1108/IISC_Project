-- Question C schema. Written for SQLite; comments show the PostgreSQL / TimescaleDB change.

CREATE TABLE IF NOT EXISTS users (
    user_id     INTEGER PRIMARY KEY,
    name        TEXT NOT NULL,
    device_id   TEXT
);

-- One row per user per second. ~20 bytes of payload, so the table is huge and append-only.
CREATE TABLE IF NOT EXISTS readings (
    user_id   INTEGER NOT NULL REFERENCES users(user_id),
    ts        INTEGER NOT NULL,          -- unix epoch seconds (PostgreSQL: TIMESTAMPTZ)
    hr        REAL    NOT NULL,          -- bpm; 0 = sensor lost
    acc       REAL    NOT NULL,          -- accelerometer magnitude
    PRIMARY KEY (user_id, ts)            -- also makes duplicate sends harmless (idempotent insert)
) WITHOUT ROWID;                         -- PostgreSQL: PARTITION BY RANGE (ts) / Timescale hypertable

-- Few rows, read often, so it is indexed for the two dashboard questions:
-- "alerts for one user" and "alerts in a time range".
CREATE TABLE IF NOT EXISTS alerts (
    alert_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id   INTEGER NOT NULL REFERENCES users(user_id),
    ts        INTEGER NOT NULL,          -- second of the reading that triggered it
    kind      TEXT    NOT NULL CHECK (kind IN ('spike', 'drop_out', 'silent_drift')),
    hr        REAL,
    message   TEXT    NOT NULL,
    status    TEXT    NOT NULL DEFAULT 'new'   -- new / sent / acknowledged
);
CREATE INDEX IF NOT EXISTS idx_alerts_user_ts ON alerts(user_id, ts);
CREATE INDEX IF NOT EXISTS idx_alerts_ts      ON alerts(ts);
