from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Protocol

import numpy as np


@dataclass
class ObservationSnapshot:
    """Aligned robot state for one infer step."""

    timestamp_ns: int
    arm_joint_positions: List[float]  # length 14, radians
    head_joint_states: List[float]  # yaw, pitch radians (best effort)
    waist_joint_states: List[float]  # pitch rad, height cm per GDK docs
    rgb_head: Optional[np.ndarray]
    rgb_left_wrist: Optional[np.ndarray]
    rgb_right_wrist: Optional[np.ndarray]


class RobotObservationSource(Protocol):
    def warmup(self) -> None:
        """Prime sensors (e.g. drop first camera frames)."""

    def read(self) -> ObservationSnapshot:
        ...

    def close(self) -> None:
        ...
