# Hybrid FastWAM G01 Bridge Design

## Goal

Build `fastwam-g01-bridge` into a deployable bridge that supports both existing operation modes:

- `http_a2d`: collect G01 observations through `a2d_sdk`, call a FastWAM-compatible HTTP `/infer` endpoint, and apply arm commands through GDK.
- `ros2_local_policy`: run inside the prepared Ubuntu 22.04 + ROS2 Humble container, use G01 ROS2 topics for observations/actions, and execute a local FastWAM policy checkpoint.

The first mode preserves the existing standalone package behavior. The second mode makes the bridge usable with the current container environment and the existing `FastWAM/experiments/genie_g1` ROS2 deployment code.

## Architecture

The package should expose one CLI with a selectable backend. The existing `fastwam-g01-bridge` loop remains the default HTTP/GDK backend, while the ROS2 backend becomes a thin orchestrator around the proven FastWAM `GenieG1TaskEnv` and policy runner code. The bridge should not duplicate model-loading or ROS topic conversion logic already present in `FastWAM/experiments/genie_g1`; it should wrap it with stable configuration, launch checks, and tests.

The design keeps backend-specific code isolated:

- Common CLI/config validates backend choice, dry-run/smoke-test behavior, and user-facing options.
- HTTP/GDK backend owns `a2d_sdk` observation and action application.
- ROS2/local-policy backend owns ROS2 environment checks, FastWAM path discovery, and invocation of the existing G01 policy runner.

## Components

### Existing HTTP/GDK Backend

The existing modules remain responsible for this path:

- `fastwam_g01_bridge.bridge`: loop orchestration.
- `fastwam_g01_bridge.adapters.g01_sdk`: `RobotDds`, `CosineCamera`, and optional `RobotController`.
- `fastwam_g01_bridge.infer_client`: HTTP `/infer`.
- `fastwam_g01_bridge.action_mapper` and `fastwam_g01_bridge.safety`: action expansion and clipping.

The implementation should add only the configuration and test coverage needed to make this backend explicit as `http_a2d`.

### New ROS2 Local Policy Backend

The ROS2 backend should be a separate module, for example `fastwam_g01_bridge/backends/ros2_local_policy.py`. It should:

- Validate that `ros2`, `rclpy`, and required ROS messages are importable.
- Validate that the FastWAM repository path exists.
- Build the command/environment needed to run `FastWAM/experiments/genie_g1/run_g1_policy.py`.
- Support a smoke-test mode that imports ROS2/GDK/FastWAM integration modules without moving the robot.

The backend should not implement a second ROS2 bridge unless tests reveal an unavoidable gap. The existing FastWAM files already handle DDS setup, topic selection, camera profiles, policy loading, and WBC command publishing.

## Configuration

Add a backend selector:

- `BRIDGE_BACKEND=http_a2d` by default.
- `BRIDGE_BACKEND=ros2_local_policy` for the ROS2 Humble container path.

For ROS2 local policy, support environment variables and matching CLI flags for:

- `FASTWAM_ROOT`: path to the FastWAM checkout, default `/home/yao/FastWAM` inside the container if present.
- `FASTWAM_CKPT`: required checkpoint path.
- `FASTWAM_DATASET_STATS`: required dataset statistics path.
- `FASTWAM_INSTRUCTION`: language instruction.
- `G01_IP`: default `10.229.66.60`.
- `G01_CAMERA_PROFILE`: default `gdk`, with `hdas` supported.
- `ROS_DOMAIN_ID`: passed through unchanged.
- `ROS_REMOTE_DDS`: default `fastrtps`.

The existing HTTP/GDK variables remain valid, including `FASTWAM_INFER_URL`, `CONTROL_BACKEND`, `INCLUDE_IMAGES`, and safety limits.

## Data Flow

### HTTP/GDK

1. `G01SdkAdapter` reads arm, head, waist, and camera data from `a2d_sdk`.
2. The bridge encodes observations as JSON and JPEG base64.
3. The infer client posts to `/infer`.
4. The response action is normalized, mapped to 14 arm joints, clipped, and applied.

### ROS2 Local Policy

1. The container starts with host networking and ROS2 Humble sourced.
2. The backend configures FastWAM/G01 DDS environment through the existing FastWAM runner.
3. `GenieG1TaskEnv` subscribes to G01 ROS2 topics and publishes WBC commands.
4. The local FastWAM policy runs in-process through `run_g1_policy.py`.

## Safety

The HTTP/GDK path keeps the existing `MAX_JOINT_STEP_RAD` safety clamp and dry-run option.

The ROS2 path should expose `--dry-run` or smoke-test behavior separately from live policy execution. Live motion requires explicit checkpoint and dataset stats paths. The implementation should not make a best guess about model files or start motion if required paths are absent.

## Error Handling

Configuration errors should fail before robot motion starts:

- Missing `a2d_sdk` for `http_a2d`.
- Missing ROS2 Humble imports for `ros2_local_policy`.
- Missing FastWAM root, checkpoint, or dataset stats for live local policy.
- Unreachable G01 network in smoke tests.

Runtime errors should include the selected backend and the command/configuration that failed, without printing credentials.

## Testing

The implementation should keep existing unit tests passing and add focused tests for:

- Backend selection and validation.
- ROS2 backend command construction.
- ROS2 smoke-test behavior using monkeypatched imports/subprocess calls.
- Existing HTTP/GDK mock integration.

Remote/container verification should run on `10.229.20.125`:

- `ros2 --help`
- `python3 -c "import rclpy"`
- `python3 -c "from a2d_sdk.robot import RobotDds, RobotController, CosineCamera"`
- `python3 -m pytest` for `fastwam-g01-bridge`
- Optional ROS2 smoke command that does not move the robot.

## Out Of Scope

- Training or modifying FastWAM policy checkpoints.
- Rewriting `FastWAM/experiments/genie_g1/ros_g1_bridge.py`.
- Solving intermittent G01 network packet loss beyond reporting it in tests.
- Adding a production HTTP `/infer` server to FastWAM.
