
from datetime import datetime
import math

import numpy as np
from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from database import get_db
from face_engine import process_face_image, recognize_face


router = APIRouter(
    prefix="/api/attendance",
    tags=["Attendance"]
)


MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10 MB
ENCODING_SIZE = 128


# ---------------------------------------------------------
# GET ATTENDANCE RECORDS
# ---------------------------------------------------------

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

        return [dict(row) for row in rows]


# ---------------------------------------------------------
# FACIAL RECOGNITION AND ATTENDANCE RECORDING
# ---------------------------------------------------------

@router.post("/recognize")
async def recognize_attendance(
    image: UploadFile = File(...),
    session_label: str = Form("Default")
):
    # 1. Validate uploaded file type.

    if image.content_type not in ("image/jpeg", "image/png"):
        raise HTTPException(
            status_code=400,
            detail="Please upload a JPEG or PNG image."
        )

    # 2. Read and validate image size.

    raw_image = await image.read()

    if not raw_image:
        raise HTTPException(
            status_code=400,
            detail="The uploaded image is empty."
        )

    if len(raw_image) > MAX_IMAGE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="Image exceeds the 10 MB upload limit."
        )

    # 3. Generate facial encoding using original engine.

    try:
        encoding = process_face_image(raw_image)

    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc)
        )

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Face processing is currently unavailable."
        )

    now = datetime.now()
    scanned_at = now.isoformat(timespec="seconds")

    session_label = session_label.strip() or "Default"

    if len(session_label) > 100:
        raise HTTPException(
            status_code=400,
            detail="Session label must not exceed 100 characters."
        )

    # 4. Load enrolled encodings and apply attendance rules.

    with get_db() as connection:

        # Prevent concurrent recognition requests from creating
        # duplicate attendance records for the same student.

        connection.execute("BEGIN IMMEDIATE")

        rows = connection.execute("""
            SELECT
                person_id,
                encoding
            FROM face_encodings
        """).fetchall()

        known_encodings = []

        for row in rows:
            stored_encoding = np.frombuffer(
                row["encoding"],
                dtype=np.float64
            )

            if (
                stored_encoding.shape == (ENCODING_SIZE,)
                and np.isfinite(stored_encoding).all()
            ):
                known_encodings.append((
                    row["person_id"],
                    stored_encoding
                ))

        # 5. Find the closest enrolled student.

        result = recognize_face(
            encoding=encoding,
            known_encodings=known_encodings,
            now=now
        )

        person_id = result["person_id"]

        # 6. Check the student's previous attendance scan.

        if person_id is not None:

            previous = connection.execute("""
                SELECT scanned_at
                FROM attendance
                WHERE person_id = ?
                ORDER BY scanned_at DESC
                LIMIT 1
            """, (person_id,)).fetchone()

            last_scan_iso = (
                previous["scanned_at"]
                if previous else None
            )

            # Apply duplicate detection and attendance rules.

            result = recognize_face(
                encoding=encoding,
                known_encodings=known_encodings,
                last_scan_iso=last_scan_iso,
                now=now
            )

        outcome = result["outcome"]
        person_id = result["person_id"]
        distance = result["distance"]

        safe_distance = (
            distance if math.isfinite(distance) else None
        )

        # 7. Return an unknown face without recording attendance.

        if outcome == "Unknown":
            connection.commit()

            return {
                "success": False,
                "outcome": "Unknown",
                "message": "No matching enrolled student was found.",
                "person": None,
                "distance": safe_distance,
                "recorded": False
            }

        # 8. Retrieve recognized student's information.

        student = connection.execute("""
            SELECT
                person_id,
                student_no,
                full_name,
                section
            FROM persons
            WHERE person_id = ?
        """, (person_id,)).fetchone()

        if student is None:
            connection.commit()

            return {
                "success": False,
                "outcome": "Unknown",
                "message": "The matched student record could not be found.",
                "person": None,
                "distance": safe_distance,
                "recorded": False
            }

        person_data = dict(student)

        # 9. Handle duplicate scans.

        if outcome == "Duplicate":
            connection.commit()

            return {
                "success": True,
                "outcome": "Duplicate",
                "message": "Attendance has already been recorded recently.",
                "person": person_data,
                "distance": safe_distance,
                "recorded": False
            }

        # 10. Save valid attendance records.

        if outcome in ("Present", "Late"):

            connection.execute("""
                INSERT INTO attendance (
                    person_id,
                    scanned_at,
                    status,
                    distance,
                    session_label
                )
                VALUES (?, ?, ?, ?, ?)
            """, (
                person_id,
                scanned_at,
                outcome,
                distance,
                session_label
            ))

            connection.commit()

            return {
                "success": True,
                "outcome": outcome,
                "message": f"{person_data['full_name']} marked {outcome}.",
                "person": person_data,
                "distance": safe_distance,
                "scanned_at": scanned_at,
                "session_label": session_label,
                "recorded": True
            }

        connection.commit()

        return {
            "success": False,
            "outcome": outcome,
            "message": "Attendance was not recorded.",
            "person": person_data,
            "distance": safe_distance,
            "recorded": False
        }
