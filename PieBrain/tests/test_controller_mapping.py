from PieBrain.controller_mapping import apply_deadzone, differential_mix, compute_drive


def test_apply_deadzone_zero_inside():
    assert apply_deadzone(0.03, 0.05) == 0.0
    assert apply_deadzone(-0.04, 0.05) == 0.0


def test_apply_deadzone_rescale():
    # value just outside deadzone should be small but non-zero
    v = apply_deadzone(0.06, 0.05)
    assert 0.0 < v < 0.1


def test_differential_mix_clamps():
    l, r = differential_mix(0.8, 0.5)  # 1.3 -> clamp
    assert l == 1.0 and r == 0.30000000000000004


def test_compute_drive_pipeline():
    drive = compute_drive(0.5, 0.2, deadzone=0.0)
    (ldir, lspeed), (rdir, rspeed) = drive.as_direction_speed()
    assert ldir == "FORWARD" and rdir == "FORWARD"
    assert abs(lspeed - 0.7) < 1e-6
    assert abs(rspeed - 0.3) < 1e-6
