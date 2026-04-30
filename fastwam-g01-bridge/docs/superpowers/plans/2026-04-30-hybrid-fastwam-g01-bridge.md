# Hybrid FastWAM G01 Bridge Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a selectable hybrid backend to `fastwam-g01-bridge`: keep the existing HTTP + `a2d_sdk` path and add a ROS2 Humble local-policy path that runs the existing FastWAM G01 deployment code inside the prepared Ubuntu 22.04 container.

**Architecture:** Keep current HTTP bridge modules intact and make them explicit as the `http_a2d` backend. Add a focused ROS2 backend module that validates ROS2/FastWAM prerequisites, builds the `run_g1_policy.py` command, supports non-motion smoke checks, and delegates live policy execution to FastWAM's existing `experiments/genie_g1` stack.

**Tech Stack:** Python 3.10, pytest, `a2d_sdk`, ROS2 Humble (`rclpy`, `sensor_msgs`), Docker image `g01-gdk:ubuntu22.04`, FastWAM `experiments/genie_g1/run_g1_policy.py`.

---

## File Structure

- Modify `fastwam_g01_bridge/config.py`: add backend selector and ROS2 local policy config fields.
- Modify `fastwam_g01_bridge/__main__.py`: route CLI execution by backend and add ROS2 flags.
- Create `fastwam_g01_bridge/backends/__init__.py`: package marker for backend modules.
- Create `fastwam_g01_bridge/backends/ros2_local_policy.py`: ROS2 local policy backend validation, command construction, smoke checks, and execution.
- Modify `.env.example`: document backend variables.
- Modify `README.md`: document both run modes and container usage.
- Add `tests/test_ros2_local_policy_backend.py`: unit tests for ROS2 backend command building and smoke checks.
- Extend `tests/test_config.py`: backend parsing and ROS2 config validation.
- Extend `tests/test_integration_main.py`: assert default backend remains HTTP/GDK mock path and ROS2 backend delegates correctly.

## Task 1: Backend Configuration

**Files:**
- Modify: `fastwam_g01_bridge/config.py`
- Test: `tests/test_config.py`

- [ ] **Step 1: Write failing tests for backend config**

Add tests:

```python
def test_default_backend_is_http_a2d(monkeypatch):
    monkeypatch.delenv("BRIDGE_BACKEND", raising=False)
    cfg = BridgeConfig.from_env()
    assert cfg.backend == "http_a2d"


def test_ros2_backend_config(monkeypatch):
    monkeypatch.setenv("BRIDGE_BACKEND", "ros2_local_policy")
    monkeypatch.setenv("FASTWAM_ROOT", "/opt/FastWAM")
    monkeypatch.setenv("FASTWAM_CKPT", "/models/policy.pt")
    monkeypatch.setenv("FASTWAM_DATASET_STATS", "/models/dataset_stats.json")
    monkeypatch.setenv("FASTWAM_INSTRUCTION", "pick up the cup")
    monkeypatch.setenv("G01_IP", "10.229.66.60")
    cfg = BridgeConfig.from_env()
    assert cfg.backend == "ros2_local_policy"
    assert cfg.fastwam_root == "/opt/FastWAM"
    assert cfg.fastwam_ckpt == "/models/policy.pt"
    assert cfg.fastwam_dataset_stats == "/models/dataset_stats.json"
    assert cfg.fastwam_instruction == "pick up the cup"
    assert cfg.g01_ip == "10.229.66.60"


def test_invalid_backend(monkeypatch):
    monkeypatch.setenv("BRIDGE_BACKEND", "bad")
    with pytest.raises(ValueError, match="BRIDGE_BACKEND"):
        BridgeConfig.from_env()
```

- [ ] **Step 2: Run tests and confirm failure**

Run:

```bash
cd /Users/xudazhong/Projects/fastwam-g01-bridge
python -m pytest tests/test_config.py -v
```

Expected: tests fail because `BridgeConfig` has no `backend` or ROS2 fields.

- [ ] **Step 3: Add config fields and parsing**

Add frozen dataclass fields:

```python
backend: str
fastwam_root: str
fastwam_ckpt: str
fastwam_dataset_stats: str
fastwam_instruction: str
g01_ip: str
g01_camera_profile: str
ros_remote_dds: str
```

In `from_env()` parse:

```python
backend = os.environ.get("BRIDGE_BACKEND", "http_a2d").strip().lower()
if backend not in ("http_a2d", "ros2_local_policy"):
    raise ValueError("BRIDGE_BACKEND must be http_a2d|ros2_local_policy")

camera_profile = os.environ.get("G01_CAMERA_PROFILE", "gdk").strip().lower()
if camera_profile not in ("gdk", "hdas"):
    raise ValueError("G01_CAMERA_PROFILE must be gdk|hdas")
```

Set defaults:

```python
fastwam_root=os.environ.get("FASTWAM_ROOT", "/home/yao/FastWAM").strip()
fastwam_ckpt=os.environ.get("FASTWAM_CKPT", "").strip()
fastwam_dataset_stats=os.environ.get("FASTWAM_DATASET_STATS", "").strip()
fastwam_instruction=os.environ.get("FASTWAM_INSTRUCTION", "").strip()
g01_ip=os.environ.get("G01_IP", "10.229.66.60").strip()
g01_camera_profile=camera_profile
ros_remote_dds=os.environ.get("ROS_REMOTE_DDS", "fastrtps").strip().lower()
```

- [ ] **Step 4: Verify config tests pass**

Run:

```bash
python -m pytest tests/test_config.py -v
```

Expected: all config tests pass.

## Task 2: ROS2 Local Policy Backend

**Files:**
- Create: `fastwam_g01_bridge/backends/__init__.py`
- Create: `fastwam_g01_bridge/backends/ros2_local_policy.py`
- Test: `tests/test_ros2_local_policy_backend.py`

- [ ] **Step 1: Write failing tests for command construction**

Create tests:

```python
from fastwam_g01_bridge.config import BridgeConfig
from fastwam_g01_bridge.backends.ros2_local_policy import build_run_command


def make_cfg(**overrides):
    data = dict(
        fastwam_infer_url="http://unused/infer",
        instruction="perform the task",
        adapter="mock",
        control_backend="move_arm",
        rate_hz=2.0,
        max_joint_step_rad=0.25,
        include_images=False,
        image_resize=None,
        action_7dof_mode="duplicate",
        camera_warmup_frames=0,
        infer_timeout_s=60.0,
        trajectory_reference_time=1.0,
        backend="ros2_local_policy",
        fastwam_root="/opt/FastWAM",
        fastwam_ckpt="/models/policy.pt",
        fastwam_dataset_stats="/models/dataset_stats.json",
        fastwam_instruction="pick up the cup",
        g01_ip="10.229.66.60",
        g01_camera_profile="hdas",
        ros_remote_dds="fastrtps",
    )
    data.update(overrides)
    return BridgeConfig(**data)


def test_build_run_command_contains_required_fastwam_args():
    cmd = build_run_command(make_cfg(), max_steps=3, dry_run=False)
    assert cmd[:2] == ["python", "experiments/genie_g1/run_g1_policy.py"]
    assert "--ckpt" in cmd
    assert "/models/policy.pt" in cmd
    assert "--dataset-stats" in cmd
    assert "/models/dataset_stats.json" in cmd
    assert "--g1-ip" in cmd
    assert "10.229.66.60" in cmd
    assert "--camera-profile" in cmd
    assert "hdas" in cmd
    assert "--max-steps" in cmd
    assert "3" in cmd
```

- [ ] **Step 2: Write failing tests for validation**

Add:

```python
import pytest

from fastwam_g01_bridge.backends.ros2_local_policy import validate_live_config


def test_validate_live_config_requires_ckpt():
    with pytest.raises(ValueError, match="FASTWAM_CKPT"):
        validate_live_config(make_cfg(fastwam_ckpt=""))


def test_validate_live_config_requires_dataset_stats():
    with pytest.raises(ValueError, match="FASTWAM_DATASET_STATS"):
        validate_live_config(make_cfg(fastwam_dataset_stats=""))
```

- [ ] **Step 3: Implement backend module**

Create:

```python
from __future__ import annotations

import importlib.util
import os
import subprocess
from pathlib import Path
from typing import Sequence

from fastwam_g01_bridge.config import BridgeConfig


def validate_live_config(cfg: BridgeConfig) -> None:
    if not cfg.fastwam_ckpt:
        raise ValueError("FASTWAM_CKPT is required for ros2_local_policy live runs")
    if not cfg.fastwam_dataset_stats:
        raise ValueError("FASTWAM_DATASET_STATS is required for ros2_local_policy live runs")
    root = Path(cfg.fastwam_root)
    if not root.exists():
        raise ValueError(f"FASTWAM_ROOT does not exist: {root}")
    runner = root / "experiments" / "genie_g1" / "run_g1_policy.py"
    if not runner.exists():
        raise ValueError(f"FastWAM G01 runner not found: {runner}")


def build_run_command(cfg: BridgeConfig, *, max_steps: int | None = None, dry_run: bool = False) -> list[str]:
    cmd = [
        "python",
        "experiments/genie_g1/run_g1_policy.py",
        "--ckpt",
        cfg.fastwam_ckpt,
        "--dataset-stats",
        cfg.fastwam_dataset_stats,
        "--instruction",
        cfg.fastwam_instruction or cfg.instruction,
        "--g1-ip",
        cfg.g01_ip,
        "--camera-profile",
        cfg.g01_camera_profile,
        "--remote-dds",
        cfg.ros_remote_dds,
    ]
    if max_steps is not None:
        cmd += ["--max-steps", str(int(max_steps))]
    if dry_run:
        cmd += ["--max-steps", "0"]
    return cmd


def smoke_check() -> None:
    if importlib.util.find_spec("rclpy") is None:
        raise RuntimeError("rclpy is not importable; source ROS2 Humble or use the prepared container")
    if importlib.util.find_spec("a2d_sdk") is None:
        raise RuntimeError("a2d_sdk is not importable in this environment")


def run_ros2_local_policy(cfg: BridgeConfig, *, max_steps: int | None = None, dry_run: bool = False) -> int:
    smoke_check()
    validate_live_config(cfg)
    env = os.environ.copy()
    env.setdefault("G1_ROBOT_IP", cfg.g01_ip)
    env.setdefault("G01_IP", cfg.g01_ip)
    cmd = build_run_command(cfg, max_steps=max_steps, dry_run=dry_run)
    return subprocess.call(cmd, cwd=cfg.fastwam_root, env=env)
```

- [ ] **Step 4: Run backend tests**

Run:

```bash
python -m pytest tests/test_ros2_local_policy_backend.py -v
```

Expected: tests pass.

## Task 3: CLI Backend Routing

**Files:**
- Modify: `fastwam_g01_bridge/__main__.py`
- Test: `tests/test_integration_main.py`

- [ ] **Step 1: Add failing CLI delegation test**

Add:

```python
def test_main_ros2_backend_smoke(monkeypatch):
    monkeypatch.setenv("BRIDGE_BACKEND", "ros2_local_policy")
    monkeypatch.setenv("FASTWAM_CKPT", "/models/policy.pt")
    monkeypatch.setenv("FASTWAM_DATASET_STATS", "/models/dataset_stats.json")

    calls = []

    def fake_smoke_check():
        calls.append("smoke")

    monkeypatch.setattr(
        "fastwam_g01_bridge.backends.ros2_local_policy.smoke_check",
        fake_smoke_check,
    )

    from fastwam_g01_bridge.__main__ import main

    assert main(["--smoke-check"]) == 0
    assert calls == ["smoke"]
```

- [ ] **Step 2: Add CLI args and routing**

In `__main__.py`, add:

```python
p.add_argument("--smoke-check", action="store_true", help="Validate selected backend environment and exit")
p.add_argument("--max-steps", type=int, default=None, help="Limit live ROS2 local policy steps")
```

After config load:

```python
if cfg.backend == "ros2_local_policy":
    from fastwam_g01_bridge.backends.ros2_local_policy import run_ros2_local_policy, smoke_check

    if args.smoke_check:
        smoke_check()
        return 0
    return int(run_ros2_local_policy(cfg, max_steps=args.max_steps, dry_run=args.dry_run))
```

Ensure existing `--once` behavior only applies to `http_a2d`.

- [ ] **Step 3: Verify CLI tests**

Run:

```bash
python -m pytest tests/test_integration_main.py -v
```

Expected: existing mock tests and new ROS2 smoke test pass.

## Task 4: Documentation And Examples

**Files:**
- Modify: `.env.example`
- Modify: `README.md`

- [ ] **Step 1: Update `.env.example`**

Add:

```dotenv
# http_a2d | ros2_local_policy
BRIDGE_BACKEND=http_a2d

# ROS2 local policy backend
FASTWAM_ROOT=/home/yao/FastWAM
FASTWAM_CKPT=
FASTWAM_DATASET_STATS=
FASTWAM_INSTRUCTION=pick up the cup
G01_IP=10.229.66.60
G01_CAMERA_PROFILE=gdk
ROS_REMOTE_DDS=fastrtps
```

- [ ] **Step 2: Update README run section**

Document:

```bash
# HTTP + a2d_sdk mode
export BRIDGE_BACKEND=http_a2d
fastwam-g01-bridge --once --dry-run

# ROS2 Humble local policy mode inside prepared container
ssh yao@10.229.20.125
/home/yao/g01_ubuntu22_container/run_g01_container.sh
cd /home/yao/Projects/fastwam-g01-bridge
pip install -e .
export BRIDGE_BACKEND=ros2_local_policy
export FASTWAM_ROOT=/home/yao/FastWAM
export FASTWAM_CKPT=/path/to/model.pt
export FASTWAM_DATASET_STATS=/path/to/dataset_stats.json
fastwam-g01-bridge --smoke-check
fastwam-g01-bridge --max-steps 10
```

- [ ] **Step 3: Run README command syntax check manually**

Review examples for paths, missing variables, and commands that would move the robot. Confirm live-motion command requires explicit ckpt/stats.

## Task 5: Local Test Suite

**Files:**
- All modified package and test files.

- [ ] **Step 1: Run full local pytest**

Run:

```bash
cd /Users/xudazhong/Projects/fastwam-g01-bridge
python -m pytest -v
```

Expected: all tests pass.

- [ ] **Step 2: Run lints diagnostics**

Use IDE diagnostics for:

```text
fastwam_g01_bridge/config.py
fastwam_g01_bridge/__main__.py
fastwam_g01_bridge/backends/ros2_local_policy.py
tests/test_config.py
tests/test_integration_main.py
tests/test_ros2_local_policy_backend.py
```

Expected: no new diagnostics in touched files.

## Task 6: Remote Container Verification

**Files:**
- No source changes unless tests reveal issues.

- [ ] **Step 1: Copy or mount updated bridge package into the container**

Use the existing bind mount from `/home/yao` if the project is on the remote. If not present, copy the updated `fastwam-g01-bridge` directory to `/home/yao/fastwam-g01-bridge` with `rsync` or `scp`.

- [ ] **Step 2: Run container smoke checks**

Run on `10.229.20.125`:

```bash
sudo docker run --rm --net=host --ipc=host --privileged \
  -e G01_IP=10.229.66.60 \
  -v /home/yao:/home/yao \
  -w /home/yao/fastwam-g01-bridge \
  g01-gdk:ubuntu22.04 \
  bash -lc 'pip install -e . && BRIDGE_BACKEND=ros2_local_policy fastwam-g01-bridge --smoke-check'
```

Expected:

```text
ROS2 smoke check passes
a2d_sdk import passes
exit code 0
```

- [ ] **Step 3: Run package tests in the container**

Run:

```bash
sudo docker run --rm --net=host --ipc=host --privileged \
  -v /home/yao:/home/yao \
  -w /home/yao/fastwam-g01-bridge \
  g01-gdk:ubuntu22.04 \
  bash -lc 'pip install -e ".[dev]" && python3 -m pytest -v'
```

Expected: all package tests pass under Ubuntu 22.04 + ROS2 Humble.

- [ ] **Step 4: Verify G01 network from container**

Run:

```bash
sudo docker run --rm --net=host g01-gdk:ubuntu22.04 \
  bash -lc 'ping -c 1 -W 2 10.229.66.60 && curl -fsSI --connect-timeout 5 http://10.229.66.60:8849/install.sh >/dev/null'
```

Expected: both commands pass. If this fails but package tests pass, report G01 network instability separately.

## Self-Review

- Spec coverage: backend selection, HTTP/GDK preservation, ROS2 local policy orchestration, safety, docs, local tests, and container verification are covered by Tasks 1-6.
- Placeholder scan: no placeholder markers are present.
- Type consistency: the plan uses `BridgeConfig` fields consistently across config, backend, CLI, and tests.
