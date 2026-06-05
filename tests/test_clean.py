"""Tests for background flattening + binarization."""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from auto_rotate.clean import binarize


def _shaded_page_with_mark() -> NDArray[np.uint8]:
    # A page with a left-to-right lighting gradient (grey background, never pure
    # white) carrying a thin dark "staff line" — thinner than the background kernel,
    # so background estimation removes it and the threshold keeps it black.
    gradient = np.linspace(150, 220, 200, dtype=np.uint8)
    page = np.tile(gradient, (200, 1))
    page[98:103, 40:160] = 20  # 5px-tall dark line
    return np.stack([page] * 3, axis=-1)


def test_binarize_is_strictly_bilevel() -> None:
    result = binarize(_shaded_page_with_mark())
    assert set(np.unique(result).tolist()) <= {0, 255}


def test_binarize_whitens_shaded_background_and_blackens_ink() -> None:
    result = binarize(_shaded_page_with_mark())
    # Shaded background corners must come out pure white despite the gradient.
    assert result[0, 0] == 255
    assert result[-1, -1] == 255
    # The ink line must come out black.
    assert result[100, 100] == 0


def test_binarize_accepts_single_channel_input() -> None:
    gray = _shaded_page_with_mark()[:, :, 0]
    result = binarize(gray)
    assert result.ndim == 2
    assert result[100, 100] == 0
