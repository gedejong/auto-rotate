"""Local-threshold binarization for scanned pages.

A scan carries uneven lighting and a grey-ish paper tone, and thin features (staff
lines, note stems) often fade in and out along their length. A single global cutoff
(Otsu) drops those faint stretches and leaves gaps. Sauvola's *local* threshold
instead adapts per pixel from the neighbourhood mean and standard deviation, so it
keeps thin low-contrast strokes connected while still flattening the background to
pure white. This is the standard technique for binarizing degraded documents.
"""

from __future__ import annotations

import cv2
import numpy as np
from numpy.typing import NDArray

# Sauvola window diameter at 300 DPI. The window should span a few stroke widths;
# the pipeline scales it to the actual render DPI.
DEFAULT_WINDOW = 41

# Sauvola parameters: R is the dynamic range of the standard deviation (half of the
# 8-bit range), k biases the threshold — larger k keeps more (fainter) ink.
_SAUVOLA_R = 128.0
_SAUVOLA_K = 0.2


def binarize(
    image: NDArray[np.uint8], window: int = DEFAULT_WINDOW, k: float = _SAUVOLA_K
) -> NDArray[np.uint8]:
    """Return a single-channel image of ``image`` as pure black (0) on white (255).

    ``window`` is the (odd-forced) side length of the local neighbourhood; ``k``
    biases the Sauvola threshold (higher keeps fainter ink).
    """
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY) if image.ndim == 3 else image

    w = window | 1  # force odd
    g = gray.astype(np.float64)
    mean = cv2.boxFilter(g, -1, (w, w), borderType=cv2.BORDER_REPLICATE)
    mean_sq = cv2.boxFilter(g * g, -1, (w, w), borderType=cv2.BORDER_REPLICATE)
    std = np.sqrt(np.clip(mean_sq - mean * mean, 0.0, None))

    threshold = mean * (1.0 + k * (std / _SAUVOLA_R - 1.0))
    binary = np.where(g > threshold, np.uint8(255), np.uint8(0))
    return binary.astype(np.uint8)
