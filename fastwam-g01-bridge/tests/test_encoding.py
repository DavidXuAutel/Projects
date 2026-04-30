import numpy as np

from fastwam_g01_bridge.encoding import encode_jpeg_b64, encode_ndarray_dict, floats_to_observation_fields


def test_floats_to_observation_fields():
    d = floats_to_observation_fields([0.1] * 7, [0.2] * 7, use_ndarray=False)
    assert d["left_state"] == [0.1] * 7
    assert d["right_state"] == [0.2] * 7


def test_encode_ndarray_dict_roundtrip_shape():
    arr = np.array([0.1, -0.2], dtype=np.float32)
    d = encode_ndarray_dict(arr)
    assert d["dtype"] == "float32"
    assert d["shape"] == [2]
    assert isinstance(d["__ndarray__"], str)


def test_encode_jpeg_b64_smoke():
    img = np.zeros((16, 24, 3), dtype=np.uint8)
    img[:, :, 0] = 200
    b64 = encode_jpeg_b64(img)
    assert len(b64) > 32
