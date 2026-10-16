PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS persons (
    person_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    student_no    TEXT NOT NULL UNIQUE,
    full_name     TEXT NOT NULL,
    section       TEXT,
    consent_given INTEGER NOT NULL CHECK (consent_given IN (0,1)),
    consent_date  TEXT NOT NULL,          -- ISO 8601
    created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS face_encodings (
    encoding_id INTEGER PRIMARY KEY AUTOINCREMENT,
    person_id   INTEGER NOT NULL REFERENCES persons(person_id) ON DELETE CASCADE,
    encoding    BLOB NOT NULL,            -- 128 float64 values = 1024 bytes
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS attendance (
    attendance_id INTEGER PRIMARY KEY AUTOINCREMENT,
    person_id     INTEGER NOT NULL REFERENCES persons(person_id),
    scanned_at    TEXT NOT NULL,          -- ISO 8601 timestamp
    status        TEXT NOT NULL CHECK (status IN ('Present','Late')),
    distance      REAL NOT NULL,          -- match distance (lower = better)
    session_label TEXT                    -- e.g. 'IPT-Lecture-2026-10-05'
);

CREATE INDEX IF NOT EXISTS idx_att_person_time
    ON attendance(person_id, scanned_at);
