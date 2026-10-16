import logging
import sqlite3

import numpy as np
import pytest

import config
import db


def test_blob_roundtrip_is_1024_bytes(enc):
    e = enc(1)
    blob = db.to_blob(e)
    assert len(blob) == 1024
    assert np.array_equal(db.from_blob(blob), e)


def test_T01_enroll_stores_person_and_encodings(tmp_db, enc):
    pid = db.add_person("2023-00123", "Juan Dela Cruz", "A", True, [enc(1), enc(2), enc(3)])
    known = db.load_all_encodings()
    assert [p for p, _ in known] == [pid] * 3
    assert db.list_persons().iloc[0]["samples"] == 3


def test_T03_duplicate_student_number_rejected_and_atomic(tmp_db, enc):
    db.add_person("2023-00123", "Juan", "A", True, [enc(1), enc(2), enc(3)])
    with pytest.raises(db.DuplicateStudentError):
        db.add_person("2023-00123", "Other", "A", True, [enc(4), enc(5), enc(6)])
    assert len(db.load_all_encodings()) == 3          # nothing from the failed enrollment
    assert len(db.list_persons()) == 1


def test_T02_consent_required_at_db_layer(tmp_db, enc):
    with pytest.raises(ValueError, match="Consent"):
        db.add_person("2023-00124", "No Consent", "A", False, [enc(1)])


def test_T16_corrupt_encoding_skipped_and_logged(tmp_db, enc, caplog):
    pid = db.add_person("2023-00123", "Juan", "A", True, [enc(1)])
    raw = sqlite3.connect(tmp_db)
    raw.execute("INSERT INTO face_encodings(person_id, encoding) VALUES (?, ?)", (pid, b"\x00" * 100))
    raw.commit()
    raw.close()
    with caplog.at_level(logging.WARNING):
        known = db.load_all_encodings()
    assert len(known) == 1
    assert "Skipping encoding_id" in caplog.text


def test_T13_database_missing(tmp_db):
    tmp_db.rename(tmp_db.with_suffix(".bak"))
    with pytest.raises(db.DatabaseError):
        db.list_persons()


def test_T13_database_locked(tmp_db):
    blocker = sqlite3.connect(tmp_db, isolation_level=None)
    blocker.execute("BEGIN EXCLUSIVE")
    try:
        with pytest.raises(db.DatabaseError):
            db.list_persons()
    finally:
        blocker.execute("ROLLBACK")
        blocker.close()


def test_attendance_roundtrip_and_last_scan(tmp_db, enc):
    pid = db.add_person("2023-00123", "Juan", "A", True, [enc(1)])
    assert db.last_scan(pid, "S1") is None
    db.add_attendance(pid, "2026-10-05T09:02:00", "Present", 0.31, "S1")
    assert db.last_scan(pid, "S1") == "2026-10-05T09:02:00"
    assert db.last_scan(pid, "S2") is None            # different session
    df = db.fetch_attendance(date="2026-10-05")
    assert df.iloc[0]["full_name"] == "Juan" and df.iloc[0]["status"] == "Present"
    assert db.list_sessions("2026-10-05") == ["S1"]


def test_delete_my_data_cascades(tmp_db, enc):
    pid = db.add_person("2023-00123", "Juan", "A", True, [enc(1), enc(2)])
    db.add_attendance(pid, "2026-10-05T09:02:00", "Present", 0.3, "S1")
    db.delete_person(pid)
    assert db.list_persons().empty and db.load_all_encodings() == []
    assert db.fetch_attendance().empty
