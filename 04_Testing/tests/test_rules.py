from datetime import datetime, time

import rules
import vision

START = time(9, 0)


def test_T08_recognized_on_time_is_present():
    d = rules.decide(1, 0.30, None, datetime(2026, 10, 5, 9, 2), START, 15, 30)
    assert d.outcome == "Present" and d.person_id == 1


def test_T09_duplicate_within_window():
    d = rules.decide(1, 0.30, "2026-10-05T09:02:00", datetime(2026, 10, 5, 9, 20), START, 15, 30)
    assert d.outcome == "Duplicate" and d.previous_scan == datetime(2026, 10, 5, 9, 2)


def test_scan_after_window_is_not_duplicate():
    d = rules.decide(1, 0.30, "2026-10-05T09:02:00", datetime(2026, 10, 5, 9, 40), START, 15, 30)
    assert d.outcome == "Late"


def test_T10_after_cutoff_is_late_and_cutoff_is_inclusive():
    assert rules.decide(1, 0.3, None, datetime(2026, 10, 5, 9, 15), START, 15, 30).outcome == "Present"
    assert rules.decide(1, 0.3, None, datetime(2026, 10, 5, 9, 16), START, 15, 30).outcome == "Late"


def test_T11_unknown_person_above_threshold():
    d = rules.decide(1, 0.80, None, datetime(2026, 10, 5, 9, 0), START, 15, 30, threshold=0.5)
    assert d.outcome == "Unknown" and d.person_id is None


def test_nobody_enrolled_is_unknown():
    pid, dist = vision.best_match(None, [])
    assert rules.decide(pid, dist, None, datetime.now()).outcome == "Unknown"


def test_threshold_boundary():
    assert rules.is_match(0.5, 0.5) and not rules.is_match(0.5001, 0.5)


def test_best_match_picks_closest_person(enc):
    a, b = enc(1), enc(2)
    known = [(10, a), (10, a + 0.01), (20, b)]
    pid, dist = vision.best_match(b + 0.001, known)
    assert pid == 20 and dist < 0.05
