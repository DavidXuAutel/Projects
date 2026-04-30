from fastwam_g01_bridge.safety import clip_joint_step


def test_clip_joint_step_within_limit():
    cur = [0.0] * 14
    tgt = [1.0] * 14
    out = clip_joint_step(cur, tgt, max_step=0.25)
    assert out == [0.25] * 14


def test_clip_no_clip_when_small_delta():
    cur = [0.0] * 14
    tgt = [0.1] * 14
    out = clip_joint_step(cur, tgt, max_step=0.25)
    assert out == [0.1] * 14


def test_clip_negative_delta():
    cur = [1.0] * 14
    tgt = [0.0] * 14
    out = clip_joint_step(cur, tgt, max_step=0.25)
    assert out == [0.75] * 14
