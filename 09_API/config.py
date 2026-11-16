from pathlib import Path
import os

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DEFAULT_DB = PROJECT_ROOT / "02_Data" / "attendance.db"

DATABASE_PATH = Path(
    os.getenv("FACETRACK_DATABASE", str(DEFAULT_DB))
)