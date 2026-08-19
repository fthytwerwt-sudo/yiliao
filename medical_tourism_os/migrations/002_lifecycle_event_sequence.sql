BEGIN;

CREATE INDEX IF NOT EXISTS idx_lifecycle_events_record_sequence
ON lifecycle_events (record_id, sequence);

INSERT OR IGNORE INTO schema_migrations (version, applied_at)
VALUES ('002_lifecycle_event_sequence', CURRENT_TIMESTAMP);

COMMIT;
