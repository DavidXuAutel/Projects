from __future__ import annotations

import time
from typing import List

import numpy as np

from fastwam_g01_bridge.adapters.base import ObservationSnapshot


class MockAdapter:
    """Synthetic observations for FastWAM integration tests without hardware."""

    def __init__(self, *, seed: int = 0) -> None:
        self._rng = np.random.default_rng(seed)
        self._arm = [0.0] * 14

    def warmup(self) -> None:
        return

    def read(self) -> ObservationSnapshot:
        ts = time.time_ns()
        noise = self._rng.normal(scale=0.01, size=14)
        self._arm = (np.asarray(self._arm) + noise).tolist()
        h, w = 120, 160
        def _img():
            return self._rng.integers(0, 255, size=(h, w, 3), dtype=np.uint8)

        return ObservationSnapshot(
            timestamp_ns=ts,
            arm_joint_positions=list(self._arm),
            head_joint_states=[0.0, 0.0],
            waist_joint_states=[0.5, 30.0],
            rgb_head=_img(),
            rgb_left_wrist=_img(),
            rgb_right_wrist=_img(),
        )

    def apply_arm14(self, snapshot: ObservationSnapshot, target14: List[float], *, dry_run: bool = False) -> None:
        self._arm = list(target14)
        if dry_run:
            return

    def close(self) -> None:
        return
