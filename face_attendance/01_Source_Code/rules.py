"""Rules engine: pure functions, no I/O. Match threshold, duplicate window, Present/Late."""
from dataclasses import dataclass
from datetime import datetime, timedelta, time
from typing import Optional

import config


@dataclass(frozen=True)
class Decision:
    outcome: str                         # "Present" | "Late" | "Duplicate" | "Unknown"
    person_id: Optional[int]
    distance: float
    previous_scan: Optional[datetime] = None


def is_match(distance: float, threshold: Optional[float] = None) -> bool:
    threshold = config.MATCH_THRESHOLD if threshold is None else threshold
    return distance <= threshold


def status_for(scan_time: datetime, class_start: time, grace_min: int) -> str:
    cutoff = datetime.combine(scan_time.date(), class_start) + timedelta(minutes=grace_min)
    return "Present" if scan_time <= cutoff else "Late"


def is_duplicate(last_scan_iso: Optional[str], now: datetime, window_min: int) -> bool:
    if not last_scan_iso:
        return False
    return now - datetime.fromisoformat(last_scan_iso) <= timedelta(minutes=window_min)


def decide(person_id, distance, last_scan_iso, now, class_start=None, grace_min=None,
           window_min=None, threshold=None) -> Decision:
    class_start = class_start or config.CLASS_START
    grace_min = config.GRACE_MINUTES if grace_min is None else grace_min
    window_min = config.DUPLICATE_WINDOW_MIN if window_min is None else window_min

    if person_id is None or not is_match(distance, threshold):
        return Decision("Unknown", None, distance)
    if is_duplicate(last_scan_iso, now, window_min):
        return Decision("Duplicate", person_id, distance, datetime.fromisoformat(last_scan_iso))
    return Decision(status_for(now, class_start, grace_min), person_id, distance)
