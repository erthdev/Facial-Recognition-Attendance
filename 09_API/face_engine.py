
"""FaceTrack bridge to the original facial recognition engine.

Loads the original source modules without allowing their config.py
to collide with 09_API/config.py.
"""
import importlib.util
import sys
from pathlib import Path

import numpy as np

API_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = API_DIR.parent
SOURCE_DIR = PROJECT_ROOT / "01_Source_Code"

MIN_SAMPLES = 3
MAX_SAMPLES = 5
ENCODING_BYTES = 1024

_original_config = None
_original_vision = None
_original_validation = None


def _load_module(module_name: str, file_path: Path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)

    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module: {file_path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _load_original_engine():
    global _original_config, _original_vision, _original_validation

    if _original_validation is not None:
        return

    required_files = [
        SOURCE_DIR / "config.py",
        SOURCE_DIR / "vision.py",
        SOURCE_DIR / "validation.py",
    ]

    for path in required_files:
        if not path.is_file():
            raise RuntimeError(f"Required recognition file is missing: {path}")

    # Preserve any API modules already imported under these names.
    previous_config = sys.modules.get("config")
    previous_vision = sys.modules.get("vision")

    try:
        # Load original configuration under a private module name.
        original_config = _load_module(
            "_facetrack_source_config",
            SOURCE_DIR / "config.py",
        )

        # Original vision.py uses: import config
        sys.modules["config"] = original_config

        original_vision = _load_module(
            "vision",
            SOURCE_DIR / "vision.py",
        )

        # Original validation.py uses: import config; import vision
        sys.modules["config"] = original_config

        original_validation = _load_module(
            "_facetrack_source_validation",
            SOURCE_DIR / "validation.py",
        )

        _original_config = original_config
        _original_vision = original_vision
        _original_validation = original_validation

    finally:
        # Restore the API's module names after original modules
        # have captured references to their own dependencies.
        if previous_config is None:
            sys.modules.pop("config", None)
        else:
            sys.modules["config"] = previous_config

        if previous_vision is None:
            sys.modules.pop("vision", None)
        else:
            sys.modules["vision"] = previous_vision


def get_sample_limits():
    _load_original_engine()

    return (
        int(_original_config.MIN_SAMPLES),
        int(_original_config.MAX_SAMPLES),
    )


def process_face_image(raw: bytes) -> np.ndarray:
    """Validate an uploaded image and return its 128D encoding."""

    _load_original_engine()

    rgb, location = _original_validation.validate_image(raw)

    encoding = _original_vision.encode_face(rgb, location)

    encoding = np.asarray(encoding, dtype=np.float64)

    if encoding.shape != (128,):
        raise ValueError("The recognition engine returned an invalid encoding.")

    if not np.isfinite(encoding).all():
        raise ValueError("The recognition engine returned invalid numeric values.")

    blob = encoding.tobytes()

    if len(blob) != ENCODING_BYTES:
        raise ValueError("The generated encoding has an invalid size.")

    return encoding
