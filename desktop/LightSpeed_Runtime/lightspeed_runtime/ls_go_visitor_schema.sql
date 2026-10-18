-- Owner-reviewed additive tables in existing Merovingian/LS GO database.
-- Apply explicitly; bridge reads/uses tables but never auto-migrates.
CREATE TABLE IF NOT EXISTS ls_go_visitor_invites (
 invite_id TEXT PRIMARY KEY, reviewer_id TEXT NOT NULL,
 token_sha256 TEXT NOT NULL UNIQUE, expiry_utc TEXT NOT NULL,
 redeemed_utc TEXT, revoked_utc TEXT
);
CREATE TABLE IF NOT EXISTS ls_go_visitor_profiles (
 reviewer_id TEXT PRIMARY KEY, name TEXT NOT NULL, theme TEXT NOT NULL,
 lens TEXT NOT NULL, handshake_json TEXT NOT NULL, consent_utc TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS ls_go_visitor_sessions (
 session_sha256 TEXT PRIMARY KEY, reviewer_id TEXT NOT NULL REFERENCES ls_go_visitor_profiles(reviewer_id),
 expires_utc TEXT NOT NULL, revoked_utc TEXT
);
CREATE TABLE IF NOT EXISTS ls_go_visitor_events (
 sequence INTEGER PRIMARY KEY AUTOINCREMENT, event_id TEXT NOT NULL UNIQUE,
 reviewer_id TEXT NOT NULL REFERENCES ls_go_visitor_profiles(reviewer_id),
 event_type TEXT NOT NULL, recorded_utc TEXT NOT NULL,
 payload_json TEXT NOT NULL, previous_hash TEXT NOT NULL,
 event_hash TEXT NOT NULL UNIQUE, event_hmac TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_ls_go_visitor_events_reviewer ON ls_go_visitor_events(reviewer_id, sequence);
