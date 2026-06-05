"""Tests for cardinal-orientation detection and application."""

from __future__ import annotations

import numpy as np
import pytesseract
import pytest
from numpy.typing import NDArray

from auto_rotate import orientation
from auto_rotate.errors import TesseractMissing
from auto_rotate.orientation import (
    apply_cardinal,
    detect_cardinal_rotation,
    tesseract_available,
)


def _sample() -> NDArray[np.uint8]:
    rng = np.arange(2 * 3 * 3, dtype=np.uint8).reshape(2, 3, 3)
    return rng


def test_apply_cardinal_zero_is_identity() -> None:
    image = _sample()
    assert np.array_equal(apply_cardinal(image, 0), image)


def test_apply_cardinal_is_lossless_round_trip() -> None:
    image = _sample()
    # 90° CW then 270° CW == 360° == identity, exactly (no resampling).
    once = apply_cardinal(image, 90)
    back = apply_cardinal(once, 270)
    assert np.array_equal(back, image)


def test_apply_cardinal_90_is_clockwise() -> None:
    image = _sample()
    rotated = apply_cardinal(image, 90)
    # Clockwise 90°: original top-left pixel lands in the top-right corner.
    assert np.array_equal(rotated[0, -1], image[0, 0])


def test_detect_cardinal_rotation_reads_osd(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(orientation, "tesseract_available", lambda: True)
    monkeypatch.setattr(pytesseract, "image_to_osd", lambda *a, **k: {"rotate": 90})
    assert detect_cardinal_rotation(_sample()) == 90


def test_detect_cardinal_rotation_falls_back_on_osd_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(orientation, "tesseract_available", lambda: True)

    def _raise(*_a: object, **_k: object) -> dict[str, int]:
        raise pytesseract.TesseractError(1, "no text")

    monkeypatch.setattr(pytesseract, "image_to_osd", _raise)
    assert detect_cardinal_rotation(_sample()) == 0


def test_detect_cardinal_rotation_ignores_unexpected_value(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(orientation, "tesseract_available", lambda: True)
    monkeypatch.setattr(pytesseract, "image_to_osd", lambda *a, **k: {"rotate": 45})
    assert detect_cardinal_rotation(_sample()) == 0


def test_detect_cardinal_rotation_requires_tesseract(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(orientation, "tesseract_available", lambda: False)
    with pytest.raises(TesseractMissing):
        detect_cardinal_rotation(_sample())


@pytest.mark.skipif(not tesseract_available(), reason="tesseract binary not installed")
def test_detect_cardinal_rotation_runs_against_real_tesseract() -> None:
    # Real OSD on a synthetic page: must return a valid cardinal value without error.
    from conftest import make_text_image

    result = detect_cardinal_rotation(np.asarray(make_text_image()))
    assert result in orientation.VALID_ROTATIONS
