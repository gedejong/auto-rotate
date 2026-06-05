"""Cardinal-orientation detection (0/90/180/270) via Tesseract OSD.

``jdeskew`` only resolves fine tilt (±15° by default), so a page that is
upside-down or rotated a quarter turn needs a coarse correction first. Tesseract's
"orientation and script detection" (OSD) reports how far the page is rotated; we
snap it back losslessly with :func:`numpy.rot90` before fine-skew correction.
"""

from __future__ import annotations

import contextlib
import logging
import os
import tempfile
from typing import Any, cast

import numpy as np
import pytesseract
from numpy.typing import NDArray
from PIL import Image

from .binaries import find_binary
from .errors import TesseractMissing

logger = logging.getLogger(__name__)

VALID_ROTATIONS = (0, 90, 180, 270)


def tesseract_available() -> bool:
    """Return whether the ``tesseract`` binary can be found (PATH or common dirs)."""
    return find_binary("tesseract") is not None


def detect_cardinal_rotation(image: NDArray[np.uint8]) -> int:
    """Return the clockwise rotation in degrees (one of 0/90/180/270) to upright ``image``.

    Falls back to ``0`` when Tesseract cannot determine orientation (e.g. a blank
    or text-sparse page). Raises :class:`TesseractMissing` if the binary is absent.
    """
    tesseract = find_binary("tesseract")
    if tesseract is None:
        raise TesseractMissing(
            "Cardinal-orientation detection requires the `tesseract` binary. "
            "Install it (e.g. `brew install tesseract`) or pass --no-orient."
        )
    # Pin the resolved path so pytesseract works even when PATH is minimal (GUI apps).
    pytesseract.pytesseract.tesseract_cmd = tesseract
    # Write a temp PNG and pass its path to Tesseract. Letting pytesseract handle
    # an in-memory image relies on its own NamedTemporaryFile plumbing, which is
    # fragile (Windows, sandboxed temp dirs); a closed file path is portable.
    fd, tmp_path = tempfile.mkstemp(suffix=".png", prefix="auto_rotate_osd_")
    os.close(fd)
    try:
        Image.fromarray(image).save(tmp_path, format="PNG")
        # output_type=DICT yields a dict; the stub models only the str/bytes overloads.
        osd = cast(
            dict[str, Any],
            pytesseract.image_to_osd(tmp_path, output_type=pytesseract.Output.DICT),
        )
    except pytesseract.TesseractError as exc:
        logger.warning("OSD failed (%s); assuming page is already upright.", exc)
        return 0
    finally:
        with contextlib.suppress(OSError):
            os.unlink(tmp_path)

    rotate = int(osd.get("rotate", 0)) % 360
    if rotate not in VALID_ROTATIONS:
        logger.warning("OSD returned unexpected rotate=%s; ignoring.", rotate)
        return 0
    return rotate


def apply_cardinal(image: NDArray[np.uint8], degrees: int) -> NDArray[np.uint8]:
    """Rotate ``image`` clockwise by ``degrees`` (0/90/180/270) without resampling."""
    if degrees % 360 == 0:
        return image
    # np.rot90 rotates counter-clockwise; negate k to rotate clockwise.
    rotated = np.rot90(image, k=-(degrees // 90))
    return np.ascontiguousarray(rotated)
