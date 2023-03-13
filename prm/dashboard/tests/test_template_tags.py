from ..templatetags.dashboard_extras import clean_phone_number, strip_zeros


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


def test_clean_phone_number():
    test_data = [
        ("001-702-571-1212", "0017025711212"),
        ("(395)738-9875x6503", "39573898756503"),
        ("9756445345", "9756445345"),
        ("+1-761-982-8443x4156", "176198284434156"),
        ("8 (999) 999-99-99", "89999999999"),
    ]
    for case, result in test_data:
        assert clean_phone_number(case) == result
