import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "01_Source_Code"))
sys.path.insert(0, str(ROOT / "02_Data"))

import config  # noqa: E402
import db  # noqa: E402


@pytest.fixture
def tmp_db(tmp_path, monkeypatch):
    """A throwaway database so tests never touch the real one."""
    monkeypatch.setattr(config, "DB_PATH", tmp_path / "test.db")
    monkeypatch.setattr(config, "DB_TIMEOUT_SECONDS", 0.2)
    db.init_db()
    return config.DB_PATH


@pytest.fixture(scope="session")
def images(tmp_path_factory):
    import generate_sample_images
    folder = tmp_path_factory.mktemp("sample_images")
    generate_sample_images.make_images(folder)
    return folder


@pytest.fixture
def enc():
    """Factory for reproducible fake 128-d encodings."""
    import numpy as np
    return lambda seed: np.random.default_rng(seed).random(128)
