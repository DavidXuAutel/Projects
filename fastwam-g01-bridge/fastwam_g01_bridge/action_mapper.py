from __future__ import annotations

from typing import List


def expand_action_to_arm14(
    action: List[float],
    *,
    mode: str,
    current_arm14: List[float],
) -> List[float]:
    """Map FastWAM `action` to 14 joint targets (radians)."""
    n = len(action)
    if n == 14:
        return [float(x) for x in action]
    if n != 7:
        raise ValueError(f"FastWAM action dim {n} not supported (expected 7 or 14)")

    left = list(action[:7])
    right = list(action[:7])
    m = mode.lower()
    if m == "duplicate":
        return [float(x) for x in left + right]
    if m == "left_only":
        return [float(x) for x in left + list(current_arm14[7:14])]
    if m == "right_only":
        return [float(x) for x in list(current_arm14[0:7]) + right]
    raise ValueError(f"unknown ACTION_7DOF_MODE: {mode!r}")
