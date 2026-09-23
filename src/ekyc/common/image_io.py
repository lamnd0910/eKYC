"""Safe image decoding helpers."""

from __future__ import annotations

import cv2
import numpy as np


def decode_bgr_image(content: bytes) -> np.ndarray:
    """Decode uploaded bytes into a non-empty BGR uint8 image array."""
    encoded = np.frombuffer(content, dtype=np.uint8)
    image = cv2.imdecode(encoded, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("Uploaded file is not a supported image")
    return image
