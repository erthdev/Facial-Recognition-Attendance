"""Configuration: every threshold, path and cutoff lives here."""
import logging
import os
from datetime import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "02_Data"
DB_PATH = Path(os.environ.get("ATTENDANCE_DB", DATA_DIR / "attendance.db"))
SCHEMA_PATH = DATA_DIR / "schema.sql"
LOG_PATH = PROJECT_ROOT / "app.log"
DB_TIMEOUT_SECONDS = 10

# --- Recognition rules ---
MATCH_THRESHOLD = 0.5          # 0.5 strict, 0.6 library default. Tune with your own data.
DUPLICATE_WINDOW_MIN = 30      # ignore repeat scans of the same person in the same session
CLASS_START = time(9, 0)       # Present if scan <= CLASS_START + GRACE_MINUTES, else Late
GRACE_MINUTES = 15

# --- Enrollment ---
MIN_SAMPLES = 3
MAX_SAMPLES = 5
STUDENT_NO_PATTERN = r"^[A-Za-z0-9][A-Za-z0-9\-]{3,19}$"

# --- Image quality / performance ---
DETECT_SCALE = 0.5             # downscale before HOG detection (dual-core CPU)
DETECT_UPSAMPLE = 1
MIN_BLUR = 60.0                # variance of Laplacian; below = blurry (tune: 50-100)
MIN_BRIGHTNESS = 50.0          # mean gray level; below = too dark
ENCODING_BYTES = 1024          # 128 float64 values


def get_logger(name: str) -> logging.Logger:
    """Technical details go to app.log; users only see friendly messages."""
    root = logging.getLogger("attendance")
    if not root.handlers:
        root.setLevel(logging.INFO)
        try:
            handler = logging.FileHandler(LOG_PATH)
        except OSError:
            handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
        root.addHandler(handler)
    return logging.getLogger(f"attendance.{name}")
