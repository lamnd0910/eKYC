"""Reusable synthetic image fixtures; no real identity data is used."""

from __future__ import annotations

import cv2
import numpy as np
import pytest


@pytest.fixture
def synthetic_image_bytes() -> bytes:
    """Create a small generated BGR image and encode it as PNG bytes."""
    image = np.zeros((32, 48, 3), dtype=np.uint8)
    image[:, :, 1] = 120
    success, encoded = cv2.imencode(".png", image)
    assert success
    return encoded.tobytes()
