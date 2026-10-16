"""Create deliberately bad sample images for the validation tests (T04, T06, T07).

Run:  python 02_Data/generate_sample_images.py
Add your own GOOD photos (one clear face) and a 2-face photo to sample_images/ by hand.
"""
import sys
from pathlib import Path

import cv2
import numpy as np


def make_images(out_dir) -> None:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(42)
    # sharp, well lit, but no face: random texture (T04)
    cv2.imwrite(str(out / "no_face.jpg"), rng.integers(0, 256, (480, 640, 3), dtype=np.uint8))
    # too dark (T06)
    cv2.imwrite(str(out / "dark.jpg"), rng.integers(0, 20, (480, 640, 3), dtype=np.uint8))
    # bright enough but very blurry (T06)
    noise = rng.integers(90, 170, (480, 640, 3), dtype=np.uint8)
    cv2.imwrite(str(out / "blurry.jpg"), cv2.GaussianBlur(noise, (61, 61), 0))
    # a PDF renamed to .jpg (T07)
    (out / "not_an_image.jpg").write_bytes(b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\n")


if __name__ == "__main__":
    target = Path(__file__).resolve().parent / "sample_images"
    make_images(target)
    print(f"Wrote sample images to {target}", file=sys.stderr)
