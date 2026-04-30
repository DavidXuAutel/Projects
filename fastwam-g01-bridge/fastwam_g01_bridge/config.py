from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional, Tuple


def _bool(name: str, default: bool = False) -> bool:
    v = os.environ.get(name)
    if v is None:
        return default
    return v.strip().lower() in ("1", "true", "yes", "on")


def _float(name: str, default: float) -> float:
    v = os.environ.get(name)
    if v is None or v == "":
        return default
    return float(v)


def _int(name: str, default: int) -> int:
    v = os.environ.get(name)
    if v is None or v == "":
        return default
    return int(v)


def _optional_resize() -> Optional[Tuple[int, int]]:
    raw = os.environ.get("IMAGE_RESIZE", "").strip()
    if not raw:
        return None
    parts = [p.strip() for p in raw.replace("x", ",").split(",") if p.strip()]
    if len(parts) != 2:
        raise ValueError("IMAGE_RESIZE must be like 320,256 or 320x256")
    return int(parts[0]), int(parts[1])


@dataclass(frozen=True)
class BridgeConfig:
    fastwam_infer_url: str
    instruction: str
    adapter: str
    control_backend: str
    rate_hz: float
    max_joint_step_rad: float
    include_images: bool
    image_resize: Optional[Tuple[int, int]]
    action_7dof_mode: str
    camera_warmup_frames: int
    infer_timeout_s: float
    trajectory_reference_time: float

    @staticmethod
    def from_env() -> "BridgeConfig":
        if _bool("LOAD_DOTENV"):
            try:
                from dotenv import load_dotenv

                load_dotenv()
            except ImportError:
                pass

        raw = os.environ.get(
            "FASTWAM_INFER_URL", "http://136.114.111.201:8000/infer"
        ).strip().rstrip("/")
        if raw.endswith("/infer"):
            url = raw
        else:
            url = raw + "/infer"

        mode = os.environ.get("ACTION_7DOF_MODE", "duplicate").strip().lower()
        if mode not in ("duplicate", "left_only", "right_only"):
            raise ValueError("ACTION_7DOF_MODE must be duplicate|left_only|right_only")

        backend = os.environ.get("CONTROL_BACKEND", "move_arm").strip().lower()
        if backend not in ("move_arm", "trajectory_abs_joint"):
            raise ValueError("CONTROL_BACKEND must be move_arm|trajectory_abs_joint")

        return BridgeConfig(
            fastwam_infer_url=url,
            instruction=os.environ.get("BRIDGE_INSTRUCTION", "").strip()
            or "perform the task",
            adapter=os.environ.get("BRIDGE_ADAPTER", "g01_sdk").strip().lower(),
            control_backend=backend,
            rate_hz=_float("BRIDGE_RATE_HZ", 2.0),
            max_joint_step_rad=_float("MAX_JOINT_STEP_RAD", 0.25),
            include_images=_bool("INCLUDE_IMAGES", True),
            image_resize=_optional_resize(),
            action_7dof_mode=mode,
            camera_warmup_frames=_int("CAMERA_WARMUP_FRAMES", 2),
            infer_timeout_s=_float("INFER_TIMEOUT_S", 60.0),
            trajectory_reference_time=_float("TRAJECTORY_REFERENCE_TIME", 1.0),
        )
