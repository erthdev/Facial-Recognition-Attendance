
"""Biometric enrollment endpoints."""
import logging
import sqlite3

from fastapi import APIRouter, File, HTTPException, UploadFile

from database import get_db
from face_engine import (
    get_sample_limits,
    process_face_image,
    ENCODING_BYTES,
)

router = APIRouter(
    prefix="/api/students",
    tags=["Biometric Enrollment"],
)

log = logging.getLogger(__name__)


@router.get("/{person_id}/biometric-status")
def biometric_status(person_id: int):
    min_samples, max_samples = get_sample_limits()

    with get_db() as connection:
        student = connection.execute(
            """
            SELECT person_id, student_no, full_name, consent_given
            FROM persons
            WHERE person_id = ?
            """,
            (person_id,),
        ).fetchone()

        if student is None:
            raise HTTPException(
                status_code=404,
                detail="Student not found.",
            )

        count = connection.execute(
            """
            SELECT COUNT(*)
            FROM face_encodings
            WHERE person_id = ?
            """,
            (person_id,),
        ).fetchone()[0]

    return {
        "person_id": person_id,
        "student_id": student["student_no"],
        "full_name": student["full_name"],
        "consent_given": bool(student["consent_given"]),
        "samples": count,
        "minimum_samples": min_samples,
        "maximum_samples": max_samples,
        "biometric_enrolled": count >= min_samples,
    }


@router.post("/{person_id}/enroll-face", status_code=201)
async def enroll_face(
    person_id: int,
    images: list[UploadFile] = File(...),
):
    min_samples, max_samples = get_sample_limits()

    if not min_samples <= len(images) <= max_samples:
        raise HTTPException(
            status_code=400,
            detail=f"Submit between {min_samples} and {max_samples} face images.",
        )

    # Verify the existing student and consent before processing images.
    with get_db() as connection:
        student = connection.execute(
            """
            SELECT person_id, consent_given
            FROM persons
            WHERE person_id = ?
            """,
            (person_id,),
        ).fetchone()

        if student is None:
            raise HTTPException(
                status_code=404,
                detail="Student not found.",
            )

        if not student["consent_given"]:
            raise HTTPException(
                status_code=403,
                detail="Student consent is required for biometric enrollment.",
            )

        existing = connection.execute(
            """
            SELECT COUNT(*)
            FROM face_encodings
            WHERE person_id = ?
            """,
            (person_id,),
        ).fetchone()[0]

        if existing > 0:
            raise HTTPException(
                status_code=409,
                detail="This student already has biometric samples.",
            )

    # Validate and encode every image before writing anything.
    encodings = []

    for index, image in enumerate(images, start=1):
        try:
            if image.content_type not in ("image/jpeg", "image/png"):
                raise ValueError("Only JPEG and PNG images are accepted.")

            raw = await image.read()

            if not raw:
                raise ValueError("The uploaded image is empty.")

            if len(raw) > 10 * 1024 * 1024:
                raise ValueError("Image exceeds the 10 MB limit.")

            encoding = process_face_image(raw)
            encodings.append(encoding)

        except Exception as exc:
            log.warning(
                "Face enrollment validation failed for person_id=%s, sample=%s: %s",
                person_id,
                index,
                exc,
            )

            message = str(exc) or "Unable to process this face image."

            raise HTTPException(
                status_code=422,
                detail=f"Sample {index}: {message}",
            ) from exc

        finally:
            await image.close()

    # Save all encodings together. No partial enrollment.
    try:
        with get_db() as connection:
            student = connection.execute(
                """
                SELECT consent_given
                FROM persons
                WHERE person_id = ?
                """,
                (person_id,),
            ).fetchone()

            if student is None:
                raise HTTPException(
                    status_code=404,
                    detail="Student no longer exists.",
                )

            if not student["consent_given"]:
                raise HTTPException(
                    status_code=403,
                    detail="Student consent is required.",
                )

            existing = connection.execute(
                """
                SELECT COUNT(*)
                FROM face_encodings
                WHERE person_id = ?
                """,
                (person_id,),
            ).fetchone()[0]

            if existing > 0:
                raise HTTPException(
                    status_code=409,
                    detail="Biometric samples already exist.",
                )

            connection.executemany(
                """
                INSERT INTO face_encodings (person_id, encoding)
                VALUES (?, ?)
                """,
                [
                    (person_id, encoding.tobytes())
                    for encoding in encodings
                ],
            )

            connection.commit()

    except HTTPException:
        raise
    except sqlite3.Error as exc:
        log.exception("Database error during biometric enrollment.")
        raise HTTPException(
            status_code=500,
            detail="Could not save biometric samples.",
        ) from exc

    return {
        "message": "Facial enrollment completed successfully.",
        "person_id": person_id,
        "samples_saved": len(encodings),
        "encoding_size_bytes": ENCODING_BYTES,
        "biometric_enrolled": True,
    }
