from __future__ import annotations

from typing import List

import numpy as np


def clip_joint_step(
    current: List[float],
    target: List[float],
    max_step: float,
) -> List[float]:
    """Clamp each joint so |delta| <= max_step."""
    c = np.asarray(current, dtype=np.float64)
    t = np.asarray(target, dtype=np.float64)
    if c.shape != t.shape:
        raise ValueError(f"shape mismatch current {c.shape} vs target {t.shape}")
    delta = np.clip(t - c, -max_step, max_step)
    return (c + delta).tolist()
