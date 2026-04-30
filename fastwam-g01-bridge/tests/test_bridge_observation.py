import numpy as np

from fastwam_g01_bridge.adapters.base import ObservationSnapshot
from fastwam_g01_bridge.bridge import snapshot_to_observation_json
from fastwam_g01_bridge.config import BridgeConfig


def _cfg(**kwargs):
    base = {
        "fastwam_infer_url": "http://127.0.0.1/infer",
        "instruction": "x",
        "adapter": "mock",
        "control_backend": "move_arm",
        "rate_hz": 2.0,
        "max_joint_step_rad": 0.25,
        "include_images": kwargs.get("include_images", False),
        "image_resize": None,
        "action_7dof_mode": "duplicate",
        "camera_warmup_frames": 0,
        "infer_timeout_s": 30.0,
        "trajectory_reference_time": 1.0,
    }
    base.update(kwargs)
    return BridgeConfig(**base)


def test_snapshot_to_observation_no_images():
    snap = ObservationSnapshot(
        timestamp_ns=1,
        arm_joint_positions=[float(i) for i in range(14)],
        head_joint_states=[0.0, 0.0],
        waist_joint_states=[0.5, 30.0],
        rgb_head=None,
        rgb_left_wrist=None,
        rgb_right_wrist=None,
    )
    obs = snapshot_to_observation_json(snap, _cfg(include_images=False))
    assert obs["left_state"] == list(range(7))
    assert obs["right_state"] == list(range(7, 14))
    assert "rgb_head" not in obs


def test_snapshot_to_observation_with_images():
    img = np.zeros((8, 8, 3), dtype=np.uint8)
    snap = ObservationSnapshot(
        timestamp_ns=1,
        arm_joint_positions=[0.0] * 14,
        head_joint_states=[0.0, 0.0],
        waist_joint_states=[0.5, 30.0],
        rgb_head=img,
        rgb_left_wrist=img,
        rgb_right_wrist=img,
    )
    obs = snapshot_to_observation_json(snap, _cfg(include_images=True))
    assert "rgb_head" in obs and isinstance(obs["rgb_head"], str)
    assert "rgb_left_wrist" in obs
    assert "rgb_right_wrist" in obs
