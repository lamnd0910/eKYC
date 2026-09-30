"""Safe image decoding helpers."""

from __future__ import annotations

from io import BytesIO

import cv2
import numpy as np
from PIL import Image, UnidentifiedImageError

from ekyc.common.config import AppSettings


class ImageInputError(Exception):
    """A sanitized image-boundary error with a stable public code."""

    def __init__(self, code: str, status_code: int = 422) -> None:
        self.code = code
        self.status_code = status_code
        super().__init__(code)


def decode_bgr_image(content: bytes, settings: AppSettings) -> np.ndarray:
    """Check encoded format and header dimensions before full BGR decoding."""
    if len(content) > settings.max_file_bytes:
        raise ImageInputError("FILE_TOO_LARGE", 413)
    if not (content.startswith(b"\x89PNG\r\n\x1a\n") or content.startswith(b"\xff\xd8")):
        raise ImageInputError("UNSUPPORTED_FORMAT")
    try:
        with Image.open(BytesIO(content)) as header:
            if header.format not in settings.allowed_formats:
                raise ImageInputError("UNSUPPORTED_FORMAT")
            width, height = header.size
            if width * height > settings.max_pixels:
                raise ImageInputError("IMAGE_TOO_LARGE")
    except ImageInputError:
        raise
    except Image.DecompressionBombError as exc:
        raise ImageInputError("IMAGE_TOO_LARGE") from exc
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise ImageInputError("IMAGE_DECODE_FAILED") from exc

    encoded = np.frombuffer(content, dtype=np.uint8)
    try:
        image = cv2.imdecode(encoded, cv2.IMREAD_COLOR)
    except cv2.error as exc:
        raise ImageInputError("IMAGE_DECODE_FAILED") from exc
    if image is None:
        raise ImageInputError("IMAGE_DECODE_FAILED")
    return image
