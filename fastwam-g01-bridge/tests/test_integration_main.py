"""End-to-end CLI path with mock robot and local fake FastWAM."""

import pytest

from tests.fake_infer_server import FakeInferHandler


def test_main_once_mock_and_fake_infer(monkeypatch, infer_url):
    FakeInferHandler.response_body = {
        "action": [0.05] * 7,
        "latency_ms": 1.0,
        "inference_time": 0.5,
    }
    FakeInferHandler.status_code = 200

    monkeypatch.setenv("FASTWAM_INFER_URL", infer_url)
    monkeypatch.setenv("BRIDGE_ADAPTER", "mock")
    monkeypatch.setenv("INCLUDE_IMAGES", "false")
    monkeypatch.setenv("BRIDGE_INSTRUCTION", "test task")

    from fastwam_g01_bridge.__main__ import main

    assert main(["--once"]) == 0


def test_main_once_dry_run(monkeypatch, infer_url):
    FakeInferHandler.response_body = {"action": [0.0] * 14}
    FakeInferHandler.status_code = 200

    monkeypatch.setenv("FASTWAM_INFER_URL", infer_url)
    monkeypatch.setenv("BRIDGE_ADAPTER", "mock")
    monkeypatch.setenv("INCLUDE_IMAGES", "false")

    from fastwam_g01_bridge.__main__ import main

    assert main(["--once", "--dry-run"]) == 0


def test_build_actuator_invalid(monkeypatch):
    monkeypatch.setenv("BRIDGE_ADAPTER", "not_a_mode")
    from fastwam_g01_bridge.bridge import build_actuator
    from fastwam_g01_bridge.config import BridgeConfig

    with pytest.raises(ValueError, match="unknown BRIDGE_ADAPTER"):
        build_actuator(BridgeConfig.from_env())
