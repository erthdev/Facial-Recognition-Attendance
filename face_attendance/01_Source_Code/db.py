"""Database layer: the ONLY module that runs SQL.

Run `python 01_Source_Code/db.py init` or `... reset` from the project root.
"""
import contextlib
import sqlite3
import sys
from datetime import datetime

import numpy as np
import pandas as pd

import config

log = config.get_logger("db")


class DatabaseError(Exception):
    """Database missing, locked or failing. The UI shows a friendly message."""


class DuplicateStudentError(DatabaseError):
    """Student number already enrolled."""


@contextlib.contextmanager
def connection(create: bool = False):
    """Short-lived connection: commit on success, rollback on error, always close."""
    path = config.DB_PATH
    if not create and not path.exists():
        log.error("Database file not found: %s", path)
        raise DatabaseError("Database file not found")
    try:
        conn = sqlite3.connect(path, timeout=config.DB_TIMEOUT_SECONDS)
        conn.execute("PRAGMA foreign_keys = ON")   # must run on EVERY connection
    except sqlite3.Error as exc:
        log.error("Cannot open database: %s", exc)
        raise DatabaseError(str(exc)) from exc
    try:
        yield conn
        conn.commit()
    except (sqlite3.Error, pd.errors.DatabaseError) as exc:   # pandas wraps SQLite errors
        conn.rollback()
        log.error("SQLite error: %s", exc)
        raise DatabaseError(str(exc)) from exc
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    config.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with connection(create=True) as conn:
        conn.executescript(config.SCHEMA_PATH.read_text())


# ---------- encoding <-> BLOB ----------
def to_blob(encoding) -> bytes:
    return np.asarray(encoding, dtype=np.float64).tobytes()


def from_blob(blob: bytes) -> np.ndarray:
    if blob is None or len(blob) != config.ENCODING_BYTES:
        raise ValueError(f"Corrupt encoding: expected {config.ENCODING_BYTES} bytes")
    return np.frombuffer(blob, dtype=np.float64)


# ---------- persons ----------
def student_exists(student_no: str) -> bool:
    with connection() as conn:
        row = conn.execute("SELECT 1 FROM persons WHERE student_no=?", (student_no,)).fetchone()
    return row is not None


def add_person(student_no, full_name, section, consent, encodings) -> int:
    """Insert the person and ALL encodings in one transaction (all or nothing)."""
    if not consent:
        raise ValueError("Consent is required to enroll.")
    now = datetime.now().isoformat(timespec="seconds")
    with connection() as conn:
        try:
            cur = conn.execute(
                "INSERT INTO persons(student_no, full_name, section, consent_given, consent_date)"
                " VALUES (?,?,?,?,?)",
                (student_no, full_name, section or None, int(bool(consent)), now),
            )
        except sqlite3.IntegrityError as exc:
            if "UNIQUE" in str(exc):
                raise DuplicateStudentError("This student number is already enrolled.") from exc
            raise
        person_id = cur.lastrowid
        conn.executemany(
            "INSERT INTO face_encodings(person_id, encoding) VALUES (?,?)",
            [(person_id, to_blob(e)) for e in encodings],
        )
    return person_id


def get_person(person_id: int):
    with connection() as conn:
        row = conn.execute(
            "SELECT person_id, student_no, full_name, section FROM persons WHERE person_id=?",
            (person_id,),
        ).fetchone()
    if row is None:
        return None
    return dict(zip(("person_id", "student_no", "full_name", "section"), row))


def list_persons() -> pd.DataFrame:
    sql = """SELECT p.person_id, p.student_no, p.full_name, p.section,
                    COUNT(e.encoding_id) AS samples
             FROM persons p LEFT JOIN face_encodings e ON e.person_id = p.person_id
             GROUP BY p.person_id ORDER BY p.full_name"""
    with connection() as conn:
        return pd.read_sql_query(sql, conn)


def list_sections() -> list:
    with connection() as conn:
        rows = conn.execute(
            "SELECT DISTINCT section FROM persons WHERE section IS NOT NULL AND section<>'' ORDER BY 1"
        ).fetchall()
    return [r[0] for r in rows]


def delete_person(person_id: int) -> None:
    """'Delete my data': attendance rows first, then the person (encodings cascade)."""
    with connection() as conn:
        conn.execute("DELETE FROM attendance WHERE person_id=?", (person_id,))
        conn.execute("DELETE FROM persons WHERE person_id=?", (person_id,))


# ---------- encodings ----------
def load_all_encodings() -> list:
    """Return [(person_id, np.ndarray(128,))]. Corrupt rows are skipped and logged."""
    with connection() as conn:
        rows = conn.execute("SELECT encoding_id, person_id, encoding FROM face_encodings").fetchall()
    known = []
    for encoding_id, person_id, blob in rows:
        try:
            known.append((person_id, from_blob(blob)))
        except ValueError as exc:
            log.warning("Skipping encoding_id=%s (person_id=%s): %s", encoding_id, person_id, exc)
    return known


# ---------- attendance ----------
def last_scan(person_id: int, session_label):
    """Latest scan time (ISO string) for this person in this session, or None."""
    with connection() as conn:
        row = conn.execute(
            "SELECT MAX(scanned_at) FROM attendance WHERE person_id=? AND session_label IS ?",
            (person_id, session_label),
        ).fetchone()
    return row[0]


def add_attendance(person_id, scanned_at, status, distance, session_label) -> None:
    with connection() as conn:
        conn.execute(
            "INSERT INTO attendance(person_id, scanned_at, status, distance, session_label)"
            " VALUES (?,?,?,?,?)",
            (person_id, scanned_at, status, float(distance), session_label),
        )


def fetch_attendance(date=None, section=None, session=None) -> pd.DataFrame:
    """attendance JOIN persons -> DataFrame. date is 'YYYY-MM-DD'."""
    sql = """SELECT a.attendance_id, p.student_no, p.full_name, p.section,
                    a.scanned_at, a.status, a.distance, a.session_label
             FROM attendance a JOIN persons p ON p.person_id = a.person_id WHERE 1=1"""
    params = []
    if date:
        sql += " AND substr(a.scanned_at,1,10)=?"
        params.append(date)
    if section:
        sql += " AND p.section=?"
        params.append(section)
    if session:
        sql += " AND a.session_label=?"
        params.append(session)
    sql += " ORDER BY a.scanned_at"
    with connection() as conn:
        return pd.read_sql_query(sql, conn, params=params)


def list_sessions(date=None) -> list:
    sql = "SELECT DISTINCT session_label FROM attendance WHERE session_label IS NOT NULL"
    params = []
    if date:
        sql += " AND substr(scanned_at,1,10)=?"
        params.append(date)
    with connection() as conn:
        return [r[0] for r in conn.execute(sql + " ORDER BY 1", params).fetchall()]


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "init"
    if cmd == "reset" and config.DB_PATH.exists():
        config.DB_PATH.unlink()
    if cmd in ("init", "reset"):
        init_db()
        print(f"Database ready: {config.DB_PATH}")
    else:
        print("Usage: python 01_Source_Code/db.py [init|reset]")
