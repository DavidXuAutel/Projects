from __future__ import annotations

import base64
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

try:
    import cv2
except ImportError:  # pragma: no cover
    cv2 = None


def encode_jpeg_b64(
    rgb: np.ndarray, resize: Optional[Tuple[int, int]] = None, quality: int = 85
) -> str:
    """Encode HxWx3 RGB uint8 image as JPEG base64 string."""
    if cv2 is None:
        raise RuntimeError("opencv-python-headless is required for JPEG encoding")
    img = rgb
    if resize is not None:
        w, h = resize
        img = cv2.resize(img, (w, h), interpolation=cv2.INTER_AREA)
    ok, buf = cv2.imencode(".jpg", cv2.cvtColor(img, cv2.COLOR_RGB2BGR), [int(cv2.IMWRITE_JPEG_QUALITY), quality])
    if not ok:
        raise RuntimeError("cv2.imencode failed")
    return base64.b64encode(buf.tobytes()).decode("ascii")


def encode_ndarray_dict(arr: np.ndarray) -> Dict[str, Any]:
    """FastWAM-style ndarray JSON wrapper."""
    return {
        "__ndarray__": base64.b64encode(np.ascontiguousarray(arr).tobytes()).decode("ascii"),
        "dtype": str(arr.dtype),
        "shape": list(arr.shape),
    }


def floats_to_observation_fields(
    left7: List[float],
    right7: List[float],
    *,
    use_ndarray: bool = False,
) -> Dict[str, Any]:
    if use_ndarray:
        return {
            "left_state": encode_ndarray_dict(np.asarray(left7, dtype=np.float32)),
            "right_state": encode_ndarray_dict(np.asarray(right7, dtype=np.float32)),
        }
    return {"left_state": list(left7), "right_state": list(right7)}
