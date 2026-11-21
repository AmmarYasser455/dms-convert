import pytest

from dms_convert import format_coordinate, parse_angle, parse_coordinate, to_dd, to_ddm, to_dms
from dms_convert.cli import main


def test_unicode_minus_decimal_pair():
    # Sydney Opera House, pasted from typeset text with U+2212 minus signs.
    lat, lon = parse_coordinate("−33.8568, 151.2153")
    assert lat == pytest.approx(-33.8568)
    assert lon == pytest.approx(151.2153)


def test_unicode_minus_longitude():
    # Pittsburgh: western longitude written with a typographic minus.
    lat, lon = parse_coordinate("40.4461, −79.9822")
    assert (lat, lon) == pytest.approx((40.4461, -79.9822))


def test_unicode_hyphen_and_angle():
    assert parse_angle("−0°30'") == pytest.approx(-0.5)
    assert parse_angle("‐5.5") == pytest.approx(-5.5)


def test_unicode_minus_with_letter_still_rejected():
    with pytest.raises(ValueError):
        parse_coordinate("−33.8568 S, 151.2153 E")


_BAD_INPUTS = [
    # (callable, args, expected exception)
    (parse_angle, (None,), TypeError),
    (parse_angle, (b"-5",), TypeError),
    (parse_angle, ({"lat": -5},), TypeError),
    (parse_angle, (["-5"],), TypeError),
    (parse_angle, (float("nan"),), TypeError),
    (parse_angle, ("",), ValueError),
    (parse_angle, ("   ",), ValueError),
    (parse_angle, ("−",), ValueError),
    (parse_angle, ("−−5",), ValueError),
    (parse_angle, ("+−5",), ValueError),
    (parse_angle, ("5−",), ValueError),
    (parse_angle, ("40°−30'",), ValueError),
    (parse_angle, ("nan",), ValueError),
    (parse_angle, ("−inf",), ValueError),
    (parse_angle, ("−" + "9" * 400,), ValueError),
    (parse_angle, ("−91", "lat"), ValueError),
    (parse_angle, ("−5", {"axis": "lat"}), ValueError),
    (parse_coordinate, (None,), TypeError),
    (parse_coordinate, ({"lat": 1, "lon": 2},), TypeError),
    (parse_coordinate, ((1.0, 2.0),), TypeError),
    (parse_coordinate, (float("nan"),), TypeError),
    (parse_coordinate, ("",), ValueError),
    (parse_coordinate, ("−",), ValueError),
    (parse_coordinate, ("−91, 10",), ValueError),
    (parse_coordinate, ("10, −181",), ValueError),
    (parse_coordinate, ("−nan, 10",), ValueError),
    (parse_coordinate, ("−33.8568 S, 151.2153",), ValueError),
    (parse_coordinate, ("−33.8568",), ValueError),
    (to_dd, (None,), TypeError),
    (to_dd, ("−5",), TypeError),
    (to_dd, ({"value": 5},), TypeError),
    (to_dd, (True,), TypeError),
    (to_dd, (float("nan"),), ValueError),
    (to_dd, (float("-inf"),), ValueError),
    (to_dd, (-(10 ** 400),), ValueError),
    (to_dd, (-91,), ValueError),
    (to_dms, (None,), TypeError),
    (to_dms, (float("nan"), "lon"), ValueError),
    (to_dms, (10 ** 400, "lon"), ValueError),
    (to_dms, (5, None), ValueError),
    (to_ddm, ([5],), TypeError),
    (to_ddm, (5, "lat", 2.0), TypeError),
    (to_ddm, (5, "lat", -1), ValueError),
    (format_coordinate, (None, 0), TypeError),
    (format_coordinate, (0, float("nan")), ValueError),
    (format_coordinate, (0, 0, None), ValueError),
    (format_coordinate, (0, 0, {"fmt": "dd"}), ValueError),
    (format_coordinate, (0, 0, "dd", "2"), TypeError),
]


@pytest.mark.parametrize(
    "func, args, exc", _BAD_INPUTS, ids=[f"{f.__name__}{a!r}"[:60] for f, a, _ in _BAD_INPUTS]
)
def test_bad_inputs_raise_clean_errors(func, args, exc):
    with pytest.raises(exc):
        func(*args)


def test_cli_unicode_minus(capsys):
    assert main(["−33.8688, 151.2093", "--to", "ddm"]) == 0
    assert capsys.readouterr().out.strip() == "33°52.1280'S 151°12.5580'E"
