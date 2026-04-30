# FastWAM G01 Bridge

Connects Zhiyuan G01 GDK (Copilot) camera and arm state to a FastWAM `POST /infer` server, then applies returned `action` via `RobotDds.move_arm` or `RobotController.trajectory_tracking_control`.

## Requirements

- Python 3.10+ (matches GDK; 3.9 may work for the bridge only)
- On the robot PC: `a2d_sdk`, `source env.sh`, `robot-service -s -c ./conf/copilot.pbtxt` (optional `--no-ros`)
- Network reachability to `FASTWAM_INFER_URL` and the robot controller

## Install

```bash
cd fastwam-g01-bridge
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Configuration

Copy `.env.example` to `.env` or export variables. See `.env.example` for `FASTWAM_INFER_URL`, `BRIDGE_ADAPTER` (`g01_sdk` or `mock`), `CONTROL_BACKEND`, and safety limits.

## Run

```bash
source /path/to/a2d_sdk/env.sh
export FASTWAM_INFER_URL=http://136.114.111.201:8000/infer
fastwam-g01-bridge
```

Mock (no robot): `export BRIDGE_ADAPTER=mock`. Single cycle: `python -m fastwam_g01_bridge --once`. No motion: add `--dry-run`.

## Layout

Package `fastwam_g01_bridge`: `config`, `encoding`, `infer_client`, `safety`, `action_mapper`, `bridge`, `adapters/g01_sdk`, `adapters/mock`.
