import pytest

from fastwam_g01_bridge.infer_client import normalize_action, post_infer

from tests.fake_infer_server import FakeInferHandler


def test_post_infer_ok(infer_url):
    FakeInferHandler.response_body = {"action": [0.5] * 14, "latency_ms": 2.0}
    FakeInferHandler.status_code = 200
    out = post_infer(infer_url, {"instruction": "x", "observation": {}}, timeout_s=5.0)
    assert out["action"] == [0.5] * 14


def test_post_infer_rejects_error_field(infer_url):
    FakeInferHandler.response_body = {"error": "Bad", "detail": "x"}
    FakeInferHandler.status_code = 200
    with pytest.raises(RuntimeError, match="Infer error payload"):
        post_infer(infer_url, {}, timeout_s=5.0)


def test_post_infer_http_error(infer_url):
    FakeInferHandler.response_body = {"action": [0.0] * 7}
    FakeInferHandler.status_code = 500
    with pytest.raises(RuntimeError, match="Infer HTTP 500"):
        post_infer(infer_url, {}, timeout_s=5.0)


def test_post_infer_missing_action(infer_url):
    FakeInferHandler.response_body = {"latency_ms": 1.0}
    FakeInferHandler.status_code = 200
    with pytest.raises(RuntimeError, match="missing 'action'"):
        post_infer(infer_url, {}, timeout_s=5.0)


def test_normalize_action_numpy():
    class Fake:
        def tolist(self):
            return [1.0, 2.0]

    assert normalize_action(Fake()) == [1.0, 2.0]


def test_normalize_action_bad_type():
    with pytest.raises(TypeError):
        normalize_action("not-a-list")
