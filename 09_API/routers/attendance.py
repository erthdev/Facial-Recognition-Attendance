from fastapi import APIRouter

from database import get_db


router = APIRouter(
    prefix="/api/attendance",
    tags=["Attendance"]
)


@router.get("")
def get_attendance(
    start_date: str = None,
    end_date: str = None,
    status: str = None
):

    query = """
        SELECT
            a.attendance_id,
            a.person_id,
            p.student_no,
            p.full_name,
            p.section,
            a.scanned_at,
            a.status,
            a.distance,
            a.session_label
        FROM attendance a
        JOIN persons p
            ON a.person_id = p.person_id
        WHERE 1 = 1
    """

    parameters = []

    if start_date:
        query += " AND DATE(a.scanned_at) >= ?"
        parameters.append(start_date)

    if end_date:
        query += " AND DATE(a.scanned_at) <= ?"
        parameters.append(end_date)

    if status:
        query += " AND a.status = ?"
        parameters.append(status)

    query += " ORDER BY a.scanned_at DESC"

    with get_db() as connection:

        rows = connection.execute(
            query,
            parameters
        ).fetchall()

        return [
            dict(row)
            for row in rows
        ]