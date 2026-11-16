
from datetime import date, datetime, timedelta

from fastapi import APIRouter
from database import get_db

router = APIRouter(
    prefix="/api/reports",
    tags=["Reports"]
)


@router.get("")
def get_reports(
    start_date: str = None,
    end_date: str = None,
    status: str = None,
    group_by: str = "daily"
):
    # Validate grouping option
    if group_by not in ("daily", "weekly", "monthly"):
        group_by = "daily"

    query = """
        SELECT
            p.person_id,
            p.student_no,
            p.full_name,
            p.section,
            a.attendance_id,
            a.scanned_at,
            a.status,
            a.distance,
            a.session_label
        FROM attendance a
        JOIN persons p ON a.person_id = p.person_id
        WHERE 1 = 1
    """

    parameters = []

    if start_date:
        query += " AND DATE(a.scanned_at) >= ?"
        parameters.append(start_date)

    if end_date:
        query += " AND DATE(a.scanned_at) <= ?"
        parameters.append(end_date)

    if status in ("Present", "Late"):
        query += " AND a.status = ?"
        parameters.append(status)

    query += " ORDER BY a.scanned_at DESC"

    with get_db() as connection:
        rows = connection.execute(
            query,
            parameters
        ).fetchall()

        records = [dict(row) for row in rows]

    # Calculate summary statistics
    total = len(records)

    present = sum(
        1 for row in records
        if row["status"] == "Present"
    )

    late = sum(
        1 for row in records
        if row["status"] == "Late"
    )

    unique_students = len({
        row["person_id"]
        for row in records
    })

    # Prepare chart grouping
    grouped = {}

    for row in records:
        scanned_at = row["scanned_at"]

        try:
            scan_date = date.fromisoformat(scanned_at[:10])
        except (ValueError, TypeError):
            continue

        if group_by == "daily":
            bucket_date = scan_date

        elif group_by == "weekly":
            bucket_date = scan_date - timedelta(
                days=scan_date.weekday()
            )

        else:
            bucket_date = scan_date.replace(day=1)

        key = bucket_date.isoformat()

        if key not in grouped:
            grouped[key] = {
                "date": key,
                "present": 0,
                "late": 0,
                "total": 0
            }

        grouped[key]["total"] += 1

        if row["status"] == "Present":
            grouped[key]["present"] += 1

        elif row["status"] == "Late":
            grouped[key]["late"] += 1

    # Format chart labels
    trend = []

    for key in sorted(grouped):
        item = grouped[key]
        bucket_date = date.fromisoformat(key)

        if group_by == "daily":
            label = bucket_date.strftime("%b %d")

        elif group_by == "weekly":
            week_end = bucket_date + timedelta(days=6)
            label = (
                f"{bucket_date.strftime('%b %d')} - "
                f"{week_end.strftime('%b %d')}"
            )

        else:
            label = bucket_date.strftime("%b %Y")

        trend.append({
            **item,
            "label": label
        })

    return {
        "summary": {
            "total_check_ins": total,
            "present": present,
            "late": late,
            "unique_students": unique_students
        },
        "group_by": group_by,
        "trend": trend,
        "records": records
    }
