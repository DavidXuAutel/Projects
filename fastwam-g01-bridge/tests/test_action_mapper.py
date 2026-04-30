from fastwam_g01_bridge.action_mapper import expand_action_to_arm14


def test_expand_14_passthrough():
    a = list(range(14))
    cur = [0.0] * 14
    assert expand_action_to_arm14(a, mode="duplicate", current_arm14=cur) == a


def test_expand_7_duplicate():
    cur = [0.1] * 14
    out = expand_action_to_arm14([0.0] * 7, mode="duplicate", current_arm14=cur)
    assert len(out) == 14
    assert out[:7] == [0.0] * 7
    assert out[7:] == [0.0] * 7


def test_expand_7_left_only():
    cur = [1.0] * 7 + [2.0] * 7
    out = expand_action_to_arm14([0.5] * 7, mode="left_only", current_arm14=cur)
    assert out[:7] == [0.5] * 7
    assert out[7:] == [2.0] * 7
