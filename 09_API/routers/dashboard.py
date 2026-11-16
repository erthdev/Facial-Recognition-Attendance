from datetime import date

from fastapi import APIRouter

from database import get_db


router = APIRouter(
    prefix="/api/dashboard",
    tags=["Dashboard"]
)


@router.get("")
def get_dashboard():

    today = date.today().isoformat()

    with get_db() as connection:

        total_students = connection.execute("""
            SELECT COUNT(*) FROM persons
        """).fetchone()[0]

        present_today = connection.execute("""
            SELECT COUNT(DISTINCT person_id)
            FROM attendance
            WHERE DATE(scanned_at) = ?
              AND status = 'Present'
        """, (today,)).fetchone()[0]

        late_today = connection.execute("""
            SELECT COUNT(DISTINCT person_id)
            FROM attendance
            WHERE DATE(scanned_at) = ?
              AND status = 'Late'
        """, (today,)).fetchone()[0]

        attended_today = connection.execute("""
            SELECT COUNT(DISTINCT person_id)
            FROM attendance
            WHERE DATE(scanned_at) = ?
        """, (today,)).fetchone()[0]

        absent_today = max(
            0,
            total_students - attended_today
        )

        return {
            "total_students": total_students,
            "present_today": present_today,
            "late_today": late_today,
            "absent_today": absent_today
        }