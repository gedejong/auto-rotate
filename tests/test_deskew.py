"""Tests for fine-skew estimation and correction."""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from auto_rotate.deskew import estimate_and_deskew, estimate_skew
from conftest import make_text_image, skew_image


def test_estimate_skew_detects_known_tilt() -> None:
    skewed: NDArray[np.uint8] = np.asarray(skew_image(make_text_image(), 7.0))
    angle = estimate_skew(skewed)
    assert abs(abs(angle) - 7.0) < 1.5


def test_estimate_and_deskew_reduces_residual_skew() -> None:
    skewed: NDArray[np.uint8] = np.asarray(skew_image(make_text_image(), 7.0))
    original = estimate_skew(skewed)

    corrected, applied = estimate_and_deskew(skewed)
    residual = estimate_skew(corrected)

    assert applied != 0.0
    assert abs(residual) < abs(original)
    assert abs(residual) < 1.5


def test_corners_are_filled_white() -> None:
    skewed: NDArray[np.uint8] = np.asarray(skew_image(make_text_image(), 7.0))
    corrected, _ = estimate_and_deskew(skewed)
    # The top-left corner is exposed by the correcting rotation and must be white,
    # not the black that jdeskew's default border would produce.
    assert tuple(corrected[0, 0]) == (255, 255, 255)


def test_zero_skew_returns_input_unchanged() -> None:
    flat: NDArray[np.uint8] = np.full((200, 200, 3), 255, dtype=np.uint8)
    corrected, applied = estimate_and_deskew(flat)
    assert applied == 0.0
    assert corrected is flat
