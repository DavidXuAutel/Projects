from __future__ import annotations

import logging
import time
from typing import List, Optional, Tuple

import numpy as np

from fastwam_g01_bridge.adapters.base import ObservationSnapshot

logger = logging.getLogger(__name__)


class G01SdkAdapter:
    """Reads state and sends arm commands via a2d_sdk (single RobotDds session)."""

    def __init__(
        self,
        *,
        camera_names: Tuple[str, str, str] = ("head", "hand_left", "hand_right"),
        warmup_frames: int = 2,
        control_backend: str = "move_arm",
        trajectory_reference_time: float = 1.0,
    ) -> None:
        try:
            from a2d_sdk.robot import CosineCamera, RobotDds
        except ImportError as e:  # pragma: no cover
            raise ImportError(
                "a2d_sdk not importable. Install GDK per manual and run: source env.sh"
            ) from e

        self._RobotDds = RobotDds
        self._CosineCamera = CosineCamera
        self._camera_group = list(camera_names)
        self._warmup_frames = max(0, int(warmup_frames))
        self._control_backend = control_backend
        self._trajectory_reference_time = float(trajectory_reference_time)
        self._robot: Optional[object] = None
        self._camera: Optional[object] = None
        self._rc: Optional[object] = None

    def warmup(self) -> None:
        self._robot = self._RobotDds()
        self._camera = self._CosineCamera(self._camera_group)
        if self._control_backend == "trajectory_abs_joint":
            from a2d_sdk.robot import RobotController

            self._rc = RobotController()
        time.sleep(0.5)
        for i in range(self._warmup_frames):
            _ = self._safe_latest_images()
            logger.debug("camera warmup frame %s", i + 1)

    def _safe_latest_images(self):
        cam = self._camera
        out = {}
        for key, name in (
            ("rgb_head", self._camera_group[0]),
            ("rgb_left_wrist", self._camera_group[1]),
            ("rgb_right_wrist", self._camera_group[2]),
        ):
            img, _ts = cam.get_latest_image(name)
            out[key] = img
        return out

    def read(self) -> ObservationSnapshot:
        if self._robot is None or self._camera is None:
            raise RuntimeError("call warmup() before read()")

        robot = self._robot
        arm14, arm_ts = robot.arm_joint_states()
        head, _ = robot.head_joint_states()
        waist, _ = robot.waist_joint_states()

        imgs = self._safe_latest_images()
        rgb_head = imgs["rgb_head"]
        rgb_left = imgs["rgb_left_wrist"]
        rgb_right = imgs["rgb_right_wrist"]

        if rgb_head is None or rgb_left is None or rgb_right is None:
            logger.warning("one or more camera frames None; skipping None fields")

        arm14_list = [float(x) for x in arm14]
        if len(arm14_list) != 14:
            raise RuntimeError(f"expected 14 arm joints, got {len(arm14_list)}")

        head_list = [float(x) for x in head]
        if len(head_list) != 2:
            raise RuntimeError(f"expected 2 head joints, got {len(head_list)}")

        waist_list = [float(x) for x in waist]
        if len(waist_list) != 2:
            raise RuntimeError(f"expected 2 waist values, got {len(waist_list)}")

        return ObservationSnapshot(
            timestamp_ns=int(arm_ts) if arm_ts is not None else time.time_ns(),
            arm_joint_positions=arm14_list,
            head_joint_states=head_list,
            waist_joint_states=waist_list,
            rgb_head=rgb_head if isinstance(rgb_head, np.ndarray) else None,
            rgb_left_wrist=rgb_left if isinstance(rgb_left, np.ndarray) else None,
            rgb_right_wrist=rgb_right if isinstance(rgb_right, np.ndarray) else None,
        )

    def apply_arm14(
        self, snapshot: ObservationSnapshot, target14: List[float], *, dry_run: bool = False
    ) -> None:
        if len(target14) != 14:
            raise ValueError("target14 must have length 14")
        if self._robot is None:
            raise RuntimeError("warmup() before apply_arm14()")
        if dry_run:
            logger.info("dry_run: skip apply_arm14")
            return
        if self._control_backend == "move_arm":
            self._robot.move_arm(target14)
            return
        if self._control_backend != "trajectory_abs_joint":
            raise ValueError(f"unknown control backend {self._control_backend!r}")
        if self._rc is None:
            raise RuntimeError("RobotController not initialized")

        infer_ts = int(snapshot.timestamp_ns)
        robot_states = {
            "head": list(snapshot.head_joint_states),
            "waist": list(snapshot.waist_joint_states),
            "arm": list(snapshot.arm_joint_positions),
        }
        left = list(target14[:7])
        right = list(target14[7:])
        robot_actions = [
            {
                "left_arm": {"action_data": left, "control_type": "ABS_JOINT"},
                "right_arm": {"action_data": right, "control_type": "ABS_JOINT"},
            }
        ]
        self._rc.trajectory_tracking_control(
            infer_ts,
            robot_states,
            robot_actions,
            robot_link="base_link",
            trajectory_reference_time=self._trajectory_reference_time,
        )

    def close(self) -> None:
        if self._camera is not None:
            try:
                self._camera.close()
            except Exception as e:  # pragma: no cover
                logger.warning("CosineCamera.close failed: %s", e)
            self._camera = None
        if self._robot is not None:
            try:
                self._robot.shutdown()
            except Exception as e:  # pragma: no cover
                logger.warning("RobotDds.shutdown failed: %s", e)
            self._robot = None
