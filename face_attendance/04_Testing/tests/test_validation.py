import pytest

import validation
import vision


def read(images, name):
    return (images / name).read_bytes()


def test_T07_pdf_renamed_to_jpg(images):
    with pytest.raises(validation.ValidationError, match="Invalid image"):
        validation.validate_image(read(images, "not_an_image.jpg"))


def test_empty_bytes_rejected():
    with pytest.raises(validation.ValidationError, match="Invalid image"):
        validation.decode_image(b"")


@pytest.mark.parametrize("name", ["dark.jpg", "blurry.jpg"])
def test_T06_dark_and_blurry(images, name):
    with pytest.raises(validation.ValidationError, match="quality too low"):
        validation.validate_image(read(images, name))


def test_T04_no_face(images, monkeypatch):
    monkeypatch.setattr(vision, "detect_faces", lambda rgb: [])
    with pytest.raises(validation.ValidationError, match="No face found"):
        validation.validate_image(read(images, "no_face.jpg"))


def test_T05_multiple_faces(images, monkeypatch):
    monkeypatch.setattr(vision, "detect_faces", lambda rgb: [(0, 10, 10, 0), (20, 30, 30, 20)])
    with pytest.raises(validation.ValidationError, match="Multiple faces"):
        validation.validate_image(read(images, "no_face.jpg"))


def test_single_face_passes(images, monkeypatch):
    monkeypatch.setattr(vision, "detect_faces", lambda rgb: [(5, 50, 50, 5)])
    rgb, loc = validation.validate_image(read(images, "no_face.jpg"))
    assert rgb.shape == (480, 640, 3) and loc == (5, 50, 50, 5)


def test_T02_missing_consent():
    errors = validation.validate_enrollment_form("2023-00123", "Juan", False)
    assert "Consent is required to enroll." in errors


def test_form_required_fields_and_format():
    assert validation.validate_enrollment_form("", "", True) == [
        "Student number is required.", "Full name is required."]
    assert any("letters, digits" in e for e in validation.validate_enrollment_form("a b!", "Juan", True))
    assert validation.validate_enrollment_form("2023-00123", "Juan", True) == []
