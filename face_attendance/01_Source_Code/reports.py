"""Reporting: pandas summaries, Absent list, daily chart data, CSV export."""
import pandas as pd

import db

COLUMNS = ["student_no", "full_name", "section", "scanned_at", "status", "distance", "session_label"]


def get_attendance(date=None, section=None, session=None) -> pd.DataFrame:
    return db.fetch_attendance(date=date, section=section, session=session)


def summary(att: pd.DataFrame, persons: pd.DataFrame, section=None) -> dict:
    enrolled = persons if not section else persons[persons["section"] == section]
    present = int((att["status"] == "Present").sum()) if not att.empty else 0
    late = int((att["status"] == "Late").sum()) if not att.empty else 0
    absent = len(absent_list(att, persons, section))
    return {"Enrolled": len(enrolled), "Present": present, "Late": late, "Absent": absent}


def absent_list(att: pd.DataFrame, persons: pd.DataFrame, section=None) -> pd.DataFrame:
    """Absent = enrolled persons minus persons who have a record in `att`."""
    enrolled = persons if not section else persons[persons["section"] == section]
    scanned = set(att["student_no"]) if not att.empty else set()
    return enrolled[~enrolled["student_no"].isin(scanned)][["student_no", "full_name", "section"]]


def daily_counts(att: pd.DataFrame) -> pd.DataFrame:
    """Rows = date, columns = Present / Late (for st.bar_chart)."""
    if att.empty:
        return pd.DataFrame(columns=["Present", "Late"])
    day = att["scanned_at"].str[:10]
    table = att.groupby([day, "status"]).size().unstack(fill_value=0)
    for col in ("Present", "Late"):
        if col not in table:
            table[col] = 0
    return table[["Present", "Late"]]


def to_csv_bytes(att: pd.DataFrame) -> bytes:
    return att.reindex(columns=COLUMNS).to_csv(index=False).encode("utf-8")


def csv_filename(date) -> str:
    return f"attendance_{date}.csv"
