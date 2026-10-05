"""Validation: image decoding, quality, exactly one face, and form fields."""
import re

import cv2
import numpy as np

import config
import vision

log = config.get_logger("validation")


class ValidationError(Exception):
    """The message is written for the end user."""


def decode_image(raw: bytes) -> np.ndarray:
    """JPEG/PNG bytes -> RGB uint8 array (H, W, 3). Rejects non-images."""
    bgr = None
    if raw:
        try:
            bgr = cv2.imdecode(np.frombuffer(raw, dtype=np.uint8), cv2.IMREAD_COLOR)
        except cv2.error:
            bgr = None
    if bgr is None:
        raise ValidationError("Invalid image file. Please capture a new photo.")
    return np.ascontiguousarray(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB))


def check_quality(rgb: np.ndarray) -> None:
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    brightness = float(gray.mean())
    sharpness = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    if brightness < config.MIN_BRIGHTNESS or sharpness < config.MIN_BLUR:
        log.info("Quality rejected: brightness=%.1f sharpness=%.1f", brightness, sharpness)
        raise ValidationError("Image quality too low. Improve lighting and hold still.")


def require_single_face(locations: list) -> tuple:
    if len(locations) == 0:
        raise ValidationError("No face found. Face the camera directly.")
    if len(locations) > 1:
        raise ValidationError("Multiple faces detected. Only one person at a time.")
    return locations[0]


def validate_image(raw: bytes):
    """bytes -> (rgb array, face location). Raises ValidationError with a user message."""
    rgb = decode_image(raw)
    check_quality(rgb)
    location = require_single_face(vision.detect_faces(rgb))
    return rgb, location


def validate_enrollment_form(student_no, full_name, consent) -> list:
    errors = []
    sn = (student_no or "").strip()
    if not sn:
        errors.append("Student number is required.")
    elif not re.match(config.STUDENT_NO_PATTERN, sn):
        errors.append("Student number may only contain letters, digits and hyphens (4 to 20 characters).")
    if not (full_name or "").strip():
        errors.append("Full name is required.")
    if not consent:
        errors.append("Consent is required to enroll.")
    return errors
