import pytest

from fastwam_g01_bridge.config import BridgeConfig


def test_infer_url_appends_infer(monkeypatch):
    monkeypatch.setenv("FASTWAM_INFER_URL", "http://127.0.0.1:9999")
    cfg = BridgeConfig.from_env()
    assert cfg.fastwam_infer_url == "http://127.0.0.1:9999/infer"


def test_infer_url_keeps_infer_suffix(monkeypatch):
    monkeypatch.setenv("FASTWAM_INFER_URL", "http://127.0.0.1:9/infer")
    cfg = BridgeConfig.from_env()
    assert cfg.fastwam_infer_url == "http://127.0.0.1:9/infer"


def test_invalid_action_mode(monkeypatch):
    monkeypatch.setenv("ACTION_7DOF_MODE", "invalid")
    with pytest.raises(ValueError):
        BridgeConfig.from_env()


def test_image_resize_parsed(monkeypatch):
    monkeypatch.setenv("IMAGE_RESIZE", "320,256")
    cfg = BridgeConfig.from_env()
    assert cfg.image_resize == (320, 256)
