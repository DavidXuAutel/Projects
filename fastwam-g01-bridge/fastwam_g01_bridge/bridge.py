from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Protocol

from fastwam_g01_bridge.action_mapper import expand_action_to_arm14
from fastwam_g01_bridge.adapters.base import ObservationSnapshot
from fastwam_g01_bridge.config import BridgeConfig
from fastwam_g01_bridge.encoding import encode_jpeg_b64, floats_to_observation_fields
from fastwam_g01_bridge.infer_client import normalize_action, post_infer
from fastwam_g01_bridge.safety import clip_joint_step

logger = logging.getLogger(__name__)


class _Actuator(Protocol):
    def warmup(self) -> None: ...

    def read(self) -> ObservationSnapshot: ...

    def apply_arm14(
        self, snapshot: ObservationSnapshot, target14: List[float], *, dry_run: bool = False
    ) -> None: ...

    def close(self) -> None: ...


def build_actuator(cfg: BridgeConfig) -> _Actuator:
    if cfg.adapter == "mock":
        from fastwam_g01_bridge.adapters.mock import MockAdapter

        return MockAdapter()
    if cfg.adapter == "g01_sdk":
        from fastwam_g01_bridge.adapters.g01_sdk import G01SdkAdapter

        return G01SdkAdapter(
            warmup_frames=cfg.camera_warmup_frames,
            control_backend=cfg.control_backend,
            trajectory_reference_time=cfg.trajectory_reference_time,
        )
    raise ValueError(f"unknown BRIDGE_ADAPTER: {cfg.adapter!r}")


def snapshot_to_observation_json(
    snap: ObservationSnapshot,
    cfg: BridgeConfig,
) -> Dict[str, Any]:
    left7 = snap.arm_joint_positions[:7]
    right7 = snap.arm_joint_positions[7:14]
    obs = floats_to_observation_fields(left7, right7, use_ndarray=False)
    if cfg.include_images:
        resize = cfg.image_resize
        if snap.rgb_head is not None:
            obs["rgb_head"] = encode_jpeg_b64(snap.rgb_head, resize=resize)
        if snap.rgb_left_wrist is not None:
            obs["rgb_left_wrist"] = encode_jpeg_b64(snap.rgb_left_wrist, resize=resize)
        if snap.rgb_right_wrist is not None:
            obs["rgb_right_wrist"] = encode_jpeg_b64(snap.rgb_right_wrist, resize=resize)
    return obs


def run_loop(cfg: BridgeConfig, *, dry_run: bool = False) -> None:
    actuator = build_actuator(cfg)
    actuator.warmup()
    period = 1.0 / max(cfg.rate_hz, 0.1)
    try:
        while True:
            loop_start = time.monotonic()
            snap = actuator.read()
            obs = snapshot_to_observation_json(snap, cfg)
            payload = {"instruction": cfg.instruction, "observation": obs}
            raw = post_infer(cfg.fastwam_infer_url, payload, timeout_s=cfg.infer_timeout_s)
            action = normalize_action(raw["action"])
            target14 = expand_action_to_arm14(
                action, mode=cfg.action_7dof_mode, current_arm14=snap.arm_joint_positions
            )
            safe14 = clip_joint_step(
                snap.arm_joint_positions, target14, cfg.max_joint_step_rad
            )
            actuator.apply_arm14(snap, safe14, dry_run=dry_run)
            logger.info(
                "infer ok latency_ms=%s inference_time=%s",
                raw.get("latency_ms"),
                raw.get("inference_time"),
            )
            elapsed = time.monotonic() - loop_start
            sleep_s = period - elapsed
            if sleep_s > 0:
                time.sleep(sleep_s)
    finally:
        actuator.close()
