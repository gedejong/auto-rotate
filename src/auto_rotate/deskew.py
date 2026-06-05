"""Fine-skew correction wrapping the ``jdeskew`` package."""

from __future__ import annotations

import cv2
import numpy as np
from jdeskew.estimator import get_angle
from jdeskew.utility import rotate
from numpy.typing import NDArray

DEFAULT_ANGLE_MAX = 15.0
# White fill for the triangular corners exposed by rotation. jdeskew's rotate()
# defaults border_value to None, which produces black corners on a document scan.
WHITE = (255, 255, 255)


def estimate_skew(image: NDArray[np.uint8], angle_max: float = DEFAULT_ANGLE_MAX) -> float:
    """Estimate the skew angle (degrees) of ``image`` within ±``angle_max``.

    jdeskew greys the image internally for its FFT/radial-projection estimate and
    returns ``0.0`` when it finds no clear skew.
    """
    return float(get_angle(image, angle_max=angle_max))


def estimate_and_deskew(
    image: NDArray[np.uint8], angle_max: float = DEFAULT_ANGLE_MAX
) -> tuple[NDArray[np.uint8], float]:
    """Deskew ``image`` and return ``(corrected_image, estimated_angle)``.

    ``warpAffine`` is channel-agnostic, so the RGB image is rotated in place with
    its colour preserved; the corners exposed by the rotation are filled white.
    """
    angle = estimate_skew(image, angle_max=angle_max)
    if angle == 0.0:
        return image, 0.0
    corrected: NDArray[np.uint8] = rotate(
        image,
        angle,
        border_mode=cv2.BORDER_CONSTANT,
        border_value=WHITE,
    )
    return corrected, angle
