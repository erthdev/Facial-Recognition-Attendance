"""Vision module: detect faces, compute 128-d encodings, measure distances.

face_recognition (dlib) is imported lazily, so the rest of the app (and most tests)
work even if dlib is not installed. To swap to OpenCV YuNet/SFace, only this file changes.
"""
import cv2
import numpy as np

import config

log = config.get_logger("vision")
_fr = None


class VisionUnavailableError(Exception):
    """face_recognition/dlib could not be imported."""


def _lib():
    global _fr
    if _fr is None:
        try:
            import face_recognition as fr
        except (Exception, SystemExit) as exc:   # face_recognition calls quit() if its models are missing
            log.error("face_recognition import failed: %r", exc)
            raise VisionUnavailableError(
                "Face recognition library is not installed correctly. See README, Troubleshooting."
            ) from exc
        _fr = fr
    return _fr


def detect_faces(rgb: np.ndarray) -> list:
    """Return face boxes (top, right, bottom, left) in ORIGINAL image coordinates.
    The frame is downscaled first so detection stays fast on a dual-core CPU."""
    scale = config.DETECT_SCALE
    if scale < 1:
        small = cv2.resize(rgb, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
    else:
        small, scale = np.ascontiguousarray(rgb), 1.0
    boxes = _lib().face_locations(small, number_of_times_to_upsample=config.DETECT_UPSAMPLE, model="hog")
    return [(int(t / scale), int(r / scale), int(b / scale), int(l / scale)) for t, r, b, l in boxes]


def encode_face(rgb: np.ndarray, location: tuple) -> np.ndarray:
    """RGB image + face box -> numpy array shape (128,), dtype float64."""
    encodings = _lib().face_encodings(rgb, known_face_locations=[location], num_jitters=1)
    if not encodings:
        raise ValueError("Could not compute an encoding for the detected face")
    return np.asarray(encodings[0], dtype=np.float64)


def best_match(encoding: np.ndarray, known: list):
    """known = [(person_id, encoding)]. Returns (person_id, distance) of the closest
    stored encoding, or (None, inf) if nothing is enrolled. Euclidean distance, the same
    metric as face_recognition.face_distance. The threshold is applied by rules.py."""
    if not known:
        return None, float("inf")
    matrix = np.vstack([e for _, e in known])
    distances = np.linalg.norm(matrix - encoding, axis=1)
    best = int(np.argmin(distances))
    return known[best][0], float(distances[best])
