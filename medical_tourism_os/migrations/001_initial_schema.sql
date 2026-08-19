BEGIN;

CREATE TABLE IF NOT EXISTS schema_migrations (
    version TEXT PRIMARY KEY,
    applied_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS facts (
    id TEXT PRIMARY KEY,
    claim TEXT NOT NULL,
    source TEXT NOT NULL,
    source_date TEXT NOT NULL,
    scope TEXT NOT NULL,
    classification TEXT NOT NULL,
    confidence TEXT NOT NULL,
    freshness TEXT NOT NULL,
    conflict_status TEXT NOT NULL,
    review_status TEXT NOT NULL,
    reviewed_by TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    provenance TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS lifecycle_events (
    id TEXT PRIMARY KEY,
    record_id TEXT NOT NULL,
    stage TEXT NOT NULL,
    action TEXT NOT NULL,
    details_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (record_id) REFERENCES facts(id)
);

INSERT OR IGNORE INTO schema_migrations (version, applied_at)
VALUES ('001_initial_schema', CURRENT_TIMESTAMP);

COMMIT;
