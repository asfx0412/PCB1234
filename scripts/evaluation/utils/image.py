"""Image loading helpers for multimodal API calls."""

from __future__ import annotations

import base64
from typing import Optional, Tuple


def encode_image_base64(path: str) -> Optional[str]:
    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    except OSError:
        return None


def image_size(path: str) -> Tuple[Optional[int], Optional[int]]:
    try:
        from PIL import Image

        with Image.open(path) as img:
            return img.size
    except (ImportError, OSError):
        return None, None
