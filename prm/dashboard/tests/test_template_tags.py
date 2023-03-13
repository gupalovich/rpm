from ..templatetags.dashboard_extras import strip_zeros


def test_strip_zeros():
    test_data = [
        (0.001, "0.001"),
        (0.0050, "0.005"),
        (0.0100, "0.01"),
        (0.0500, "0.05"),
        (0.06, "0.06"),
        (0.070, "0.07"),
        (0.08000, "0.08"),
        (0.1, "0.1"),
    ]
    for case, result in test_data:
        assert strip_zeros(case) == result
