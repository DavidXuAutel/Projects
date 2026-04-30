from __future__ import annotations

import argparse
import logging
import sys

from fastwam_g01_bridge.bridge import run_loop
from fastwam_g01_bridge.config import BridgeConfig


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="FastWAM to G01 bridge")
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Call infer but do not send motion commands to the robot",
    )
    p.add_argument(
        "--once",
        action="store_true",
        help="Run a single infer+apply cycle then exit",
    )
    p.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="DEBUG logging",
    )
    args = p.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    cfg = BridgeConfig.from_env()
    if args.once:
        from fastwam_g01_bridge.bridge import build_actuator, snapshot_to_observation_json
        from fastwam_g01_bridge.action_mapper import expand_action_to_arm14
        from fastwam_g01_bridge.infer_client import normalize_action, post_infer
        from fastwam_g01_bridge.safety import clip_joint_step

        actuator = build_actuator(cfg)
        actuator.warmup()
        try:
            snap = actuator.read()
            payload = {
                "instruction": cfg.instruction,
                "observation": snapshot_to_observation_json(snap, cfg),
            }
            raw = post_infer(cfg.fastwam_infer_url, payload, timeout_s=cfg.infer_timeout_s)
            action = normalize_action(raw["action"])
            target14 = expand_action_to_arm14(
                action, mode=cfg.action_7dof_mode, current_arm14=snap.arm_joint_positions
            )
            safe14 = clip_joint_step(
                snap.arm_joint_positions, target14, cfg.max_joint_step_rad
            )
            actuator.apply_arm14(snap, safe14, dry_run=args.dry_run)
        finally:
            actuator.close()
        return 0

    try:
        run_loop(cfg, dry_run=args.dry_run)
    except KeyboardInterrupt:
        logging.info("stopped by user")
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
