import pandas as pd

import db
import reports


def seed(enc):
    a = db.add_person("2023-00001", "Ana", "A", True, [enc(1)])
    db.add_person("2023-00002", "Ben", "A", True, [enc(2)])
    c = db.add_person("2023-00003", "Cy", "B", True, [enc(3)])
    db.add_attendance(a, "2026-10-05T09:02:00", "Present", 0.3, "S1")
    db.add_attendance(c, "2026-10-05T09:30:00", "Late", 0.4, "S1")


def test_T14_empty_day(tmp_db, enc):
    seed(enc)
    assert reports.get_attendance(date="2026-01-01").empty
    assert reports.daily_counts(reports.get_attendance(date="2026-01-01")).empty


def test_summary_and_absent_list(tmp_db, enc):
    seed(enc)
    att, persons = reports.get_attendance(date="2026-10-05"), db.list_persons()
    assert reports.summary(att, persons) == {"Enrolled": 3, "Present": 1, "Late": 1, "Absent": 1}
    assert list(reports.absent_list(att, persons)["full_name"]) == ["Ben"]
    assert reports.summary(att, persons, "B")["Absent"] == 0      # section filter


def test_daily_counts_has_both_columns(tmp_db, enc):
    seed(enc)
    table = reports.daily_counts(reports.get_attendance())
    assert table.loc["2026-10-05", "Present"] == 1 and table.loc["2026-10-05", "Late"] == 1


def test_T15_csv_columns_and_name(tmp_db, enc):
    seed(enc)
    csv = reports.to_csv_bytes(reports.get_attendance(date="2026-10-05")).decode()
    assert csv.splitlines()[0] == "student_no,full_name,section,scanned_at,status,distance,session_label"
    assert reports.csv_filename("2026-10-05") == "attendance_2026-10-05.csv"
    assert len(pd.read_csv(pd.io.common.StringIO(csv))) == 2
