from datetime import date

import sqlite3

from fastapi import APIRouter, HTTPException

from database import get_db
from schemas import StudentCreate


router = APIRouter(
    prefix="/api/students",
    tags=["Students"]
)



@router.get("")
def get_students():
    from face_engine import get_sample_limits

    min_samples, _ = get_sample_limits()

    with get_db() as connection:
        rows = connection.execute("""
            SELECT
                p.person_id,
                p.student_no,
                p.full_name,
                p.section,
                p.consent_given,
                p.consent_date,
                p.created_at,
                COUNT(e.encoding_id) AS biometric_samples
            FROM persons p
            LEFT JOIN face_encodings e
                ON e.person_id = p.person_id
            GROUP BY p.person_id
            ORDER BY p.full_name ASC
        """).fetchall()

        return [
            {
                "person_id": row["person_id"],
                "student_id": row["student_no"],
                "full_name": row["full_name"],
                "section": row["section"],
                "consent_given": bool(row["consent_given"]),
                "consent_date": row["consent_date"],
                "created_at": row["created_at"],
                "biometric_samples": row["biometric_samples"],
                "biometric_enrolled": (
                    row["biometric_samples"] >= min_samples
                ),
            }
            for row in rows
        ]


@router.post("", status_code=201)
def create_student(student: StudentCreate):

    if not student.consent_given:
        raise HTTPException(
            status_code=400,
            detail="Student consent is required."
        )

    full_name = (
        f"{student.first_name.strip()} "
        f"{student.last_name.strip()}"
    )

    consent_date = (
        student.consent_date.isoformat()
        if student.consent_date
        else date.today().isoformat()
    )

    try:
        with get_db() as connection:

            cursor = connection.execute("""
                INSERT INTO persons (
                    student_no,
                    full_name,
                    section,
                    consent_given,
                    consent_date
                )
                VALUES (?, ?, ?, ?, ?)
            """, (
                student.student_id.strip(),
                full_name,
                student.section,
                1,
                consent_date
            ))

            person_id = cursor.lastrowid
            connection.commit()

            return {
                "person_id": person_id,
                "student_id": student.student_id,
                "full_name": full_name,
                "section": student.section,
                "consent_given": True,
                "consent_date": consent_date,
                "biometric_enrolled": False,
                "message": "Student profile created successfully."
            }

    except sqlite3.IntegrityError:
        raise HTTPException(
            status_code=409,
            detail="Student ID already exists."
        )