import pytest

from dms_convert import format_coordinate, parse_angle, parse_coordinate, to_dd, to_ddm, to_dms
from dms_convert.cli import main

LAT, LON = 40.446111111, -79.982222222


@pytest.mark.parametrize("text", [
    "40°26'46\"N 79°58'56\"W",
    "40 26 46 N, 79 58 56 W",
    "N 40° 26' 46\" W 79° 58' 56\"",
    "40d26m46sN 79d58m56sW",
    "W79 58 56, N40 26 46",
    "40°26.7667'N 79°58.9333'W",
    "40.446111, -79.982222",
    "40.446111 -79.982222",
    "40°26′46″N, 79°58′56″W",
    "40:26:46 N, 79:58:56 W",
    "40:26:46, -79:58:56",
    "N40:26:46 W79:58:56",
])
def test_formats_parse_to_same_point(text):
    lat, lon = parse_coordinate(text)
    assert lat == pytest.approx(LAT, abs=1e-4)
    assert lon == pytest.approx(LON, abs=1e-4)


@pytest.mark.parametrize("text", ["40°30", "40:30", "40° 30"])
def test_incomplete_angle_is_one_value_not_a_pair(text):
    assert parse_angle(text) == pytest.approx(40.5)
    with pytest.raises(ValueError):
        parse_coordinate(text)


def test_dms_output():
    assert to_dms(LAT, "lat") == "40°26'46.00\"N"
    assert to_dms(LON, "lon", 0) == "79°58'56\"W"


def test_ddm_output():
    assert to_ddm(LAT, "lat") == "40°26.7667'N"


def test_rounding_carries_into_minutes():
    assert to_dms(29.99999999, "lat") == "30°00'00.00\"N"
    assert to_ddm(-0.99999999, "lon") == "1°00.0000'W"


@pytest.mark.parametrize("text", [
    "40 S, 10 E", "40.5 S 10 E", "40 30 S, 10 E", "40 30 0 S, 10 E", "S40 E10",
])
def test_spaced_south_letter_is_hemisphere(text):
    lat, lon = parse_coordinate(text)
    assert lat < 0 and lon == pytest.approx(10)


def test_positive_sign_with_hemisphere_rejected():
    with pytest.raises(ValueError):
        parse_angle("+40 N")


def test_small_negative_keeps_sign():
    assert parse_angle("-0 30 0") == -0.5
    assert parse_angle("0°30'S") == -0.5


@pytest.mark.parametrize("text", [
    "91 0 0 N 10 E", "40 26 61 N 10 E", "40 N 10", "garbage", "1 2 3",
    "-40 N 10 E", "40 N 50 N", "190, 10",
    "+40 N, 10 E", "40? 10", "40 -10!",
])
def test_invalid_input(text):
    with pytest.raises(ValueError):
        parse_coordinate(text)


@pytest.mark.parametrize("text, lat", [
    ("40S, 10E", -40), ("40.5S 10E", -40.5), ("40S10E", -40), ("S40, E10", -40), ("40°30S 10E", -40.5),
])
def test_attached_south_letter_is_hemisphere(text, lat):
    assert parse_coordinate(text) == (pytest.approx(lat), pytest.approx(10))


def test_attached_lowercase_s_without_minutes_is_rejected():
    # "40s" could be 40 seconds or 40 south; refuse rather than guess.
    with pytest.raises(ValueError, match="ambiguous"):
        parse_coordinate("40s, 10e")


@pytest.mark.parametrize("text", ["40\tN 10\tE", "40\tN\t10\tE", "40 N 10 E", "40 N\n10 E"])
def test_any_whitespace_separates(text):
    assert parse_coordinate(text) == (40, 10)


@pytest.mark.parametrize("text, expected", [
    ("46\"", 46 / 3600),
    ("46 sec", 46 / 3600),
    ("30'", 0.5),
    ("59.5'", 59.5 / 60),
    ("59\"", 59 / 3600),
    ("40°30\"", 40 + 30 / 3600),
    ("40d 30 sec", 40 + 30 / 3600),
    ("40d26m46s", 40 + 26 / 60 + 46 / 3600),
    ("40°26'46s", 40 + 26 / 60 + 46 / 3600),
    ("40°30'S", -40.5),
    ("40°30S", -40.5),
])
def test_explicit_units_are_respected(text, expected):
    assert parse_angle(text) == pytest.approx(expected)


@pytest.mark.parametrize("text", ["46s", "40°30s", "40\"30'", "40'30°", "40°30°"])
def test_ambiguous_or_misordered_units_rejected(text):
    with pytest.raises(ValueError):
        parse_angle(text)


BAD_INPUTS = [
    (parse_coordinate, (None,), TypeError),
    (parse_coordinate, (40.5,), TypeError),
    (parse_coordinate, ({"lat": 1, "lon": 2},), TypeError),
    (parse_coordinate, ([40, 10],), TypeError),
    (parse_coordinate, (b"40 N 10 E",), TypeError),
    (parse_coordinate, ("",), ValueError),
    (parse_coordinate, ("   ",), ValueError),
    (parse_coordinate, ("nan, 10",), ValueError),
    (parse_coordinate, ("inf, 10",), ValueError),
    (parse_coordinate, ("1e5, 10",), ValueError),
    (parse_coordinate, ("1" * 400 + ", 10",), ValueError),
    (parse_coordinate, ("40, 10, 5",), ValueError),
    (parse_coordinate, ("40 N, ",), ValueError),
    (parse_coordinate, ("N E",), ValueError),
    (parse_coordinate, ("40 north 10 east",), ValueError),
    (parse_coordinate, ("٤٠, 10",), ValueError),
    (parse_angle, (None,), TypeError),
    (parse_angle, (12,), TypeError),
    (parse_angle, ("",), ValueError),
    (parse_angle, ("nan",), ValueError),
    (parse_angle, ("40, 10",), ValueError),
    (parse_angle, ("40 N", "lon"), ValueError),
    (parse_angle, ("40", "x"), ValueError),
    (parse_angle, ("40 26.5 10",), ValueError),
    (parse_angle, ("40 N 5",), ValueError),
    (parse_angle, ("60'",), ValueError),
    (parse_angle, ("75.5'",), ValueError),
    (parse_angle, ("3600\"",), ValueError),
    (parse_angle, ("60 sec",), ValueError),
    (parse_angle, ("59' 60\"",), ValueError),
    (parse_angle, ("40° 60\"",), ValueError),
    (parse_coordinate, ("60' N, 10 E",), ValueError),
    (to_dms, (None,), TypeError),
    (to_dms, ("40",), TypeError),
    (to_dms, (True,), TypeError),
    (to_dms, (float("nan"),), ValueError),
    (to_dms, (float("inf"), "lon"), ValueError),
    (to_dms, (95, "lat"), ValueError),
    (to_dms, (10, "x"), ValueError),
    (to_dms, (10, "lat", -1), ValueError),
    (to_dms, (10, "lat", 1.5), TypeError),
    (to_dd, (200, "lon"), ValueError),
    (to_ddm, ({}, "lat"), TypeError),
    (format_coordinate, (0, 0, None), ValueError),
    (format_coordinate, (0, 0, ["dd"]), ValueError),
    (format_coordinate, (float("nan"), 0), ValueError),
]


@pytest.mark.parametrize("func, args, exc", BAD_INPUTS)
def test_boundary_validation(func, args, exc):
    with pytest.raises(exc):
        func(*args)


def test_tiny_negative_rounds_without_south():
    assert to_dd(-1e-9, "lat", 2) == "0.00°N"
    assert to_dms(-1e-9, "lon") == "0°00'00.00\"E"


def test_format_coordinate_and_bad_format():
    assert format_coordinate(0, 0, "dd", 2) == "0.00°N 0.00°E"
    with pytest.raises(ValueError):
        format_coordinate(0, 0, "xyz")


@pytest.mark.parametrize("argv, out, err, code", [
    (["40°26'46\"N 79°58'56\"W", "--to", "ddm"], "40°26.7667'N 79°58.9333'W", "", 0),
    (["40.7128, -74.006", "--to", "dms"], "40°42'46.08\"N 74°00'21.60\"W", "", 0),
    (["W 74 0 21.6, N 40 42 46.08"], "40.712800°N 74.006000°W", "", 0),
    (["40S, 10E"], "40.000000°S 10.000000°E", "", 0),
    (["N 40.7128 74.006 W"], "40.712800°N 74.006000°W", "", 0),
    (["-33.8688, 151.2093", "--to", "ddm"], "33°52.1280'S 151°12.5580'E", "", 0),
    (["95 N 10 E"], "", "error: lat 95.0 out of range (±90)", 1),
])
def test_readme_cli_examples(capsys, argv, out, err, code):
    assert main(argv) == code
    captured = capsys.readouterr()
    assert captured.out.strip() == out
    assert captured.err.strip() == err


def test_cli(capsys):
    assert main(["--to", "dms", "-p", "1", "40.5, -79.25"]) == 0
    assert capsys.readouterr().out.strip() == "40°30'00.0\"N 79°15'00.0\"W"
    assert main(["bad"]) == 1


@pytest.mark.parametrize("argv, out", [
    (["-40.5, 10"], "40.500000°S 10.000000°E"),
    (["-33.8688, 151.2093", "--to", "ddm"], "33°52.1280'S 151°12.5580'E"),
    (["-p", "1", "-.5 -.4"], "0.5°S 0.4°W"),
    (["--", "-40.5, 10"], "40.500000°S 10.000000°E"),
])
def test_cli_negative_leading_coordinate(capsys, argv, out):
    assert main(argv) == 0
    assert capsys.readouterr().out.strip() == out


def test_cli_negative_precision_still_rejected(capsys):
    with pytest.raises(SystemExit):
        main(["-p", "-3", "40, 10"])


NYC = (40.7128, -74.006)


@pytest.mark.parametrize("text", [
    "N 40.7128 74.006 W",          # prefix, then suffix
    "40.7128 N W 74.006",          # suffix, then prefix
    "W 74.006 40.7128 N",          # longitude first, prefix then suffix
    "74.006 W N 40.7128",          # longitude first, suffix then prefix
    "N 40°42'46.08\" 74°0'21.6\" W",
    "40 42 46.08 N W 74 0 21.6",
    "N40.7128 74.006W",
])
def test_mixed_hemisphere_placement(text):
    assert parse_coordinate(text) == pytest.approx(NYC)


@pytest.mark.parametrize("text", [
    "N 40 W",            # one number between a prefix and a suffix
    "N 40 26 74 0 W",    # unclear where the second value starts
    "N W 40 74",         # two prefixes in a row
    "40 74 N W",         # two suffixes in a row
    "40 N 74",           # only one letter without a separator
    "N 40 74 S",         # both latitude
    "40 N S 10",
])
def test_mixed_hemisphere_placement_rejected(text):
    with pytest.raises(ValueError):
        parse_coordinate(text)


def test_format_extremes_poles_and_antimeridian():
    assert format_coordinate(90, 180, "dms") == '90°00\'00.00"N 180°00\'00.00"E'
    assert format_coordinate(-90, -180, "ddm") == "90°00.0000'S 180°00.0000'W"


@pytest.mark.parametrize("text, expected", [
    ("90N, 180E", (90.0, 180.0)),                                   # DD
    ("90S, 180W", (-90.0, -180.0)),
    ('90°00\'00.00"N 180°00\'00.00"E', (90.0, 180.0)),            # DMS
    ('90°00\'00"S 180°00\'00"W', (-90.0, -180.0)),
    ("90°00.0000'N 180°00.0000'E", (90.0, 180.0)),                # DDM
    ("90°00.0000'S 180°00.0000'W", (-90.0, -180.0)),
])
def test_parse_extremes_accepted(text, expected):
    assert parse_coordinate(text) == expected


@pytest.mark.parametrize("text", [
    "90.0001 N 0 E", "90.0001 S 0 E", "0 N 180.0001 E", "0 N 180.0001 W",          # DD
    '90°00\'01"N 0E', '90°00\'01"S 0E', '0N 180°00\'01"E', '0N 180°00\'01"W',      # DMS
    "90°00.01'N 0E", "90°00.01'S 0E", "0N 180°00.01'E", "0N 180°00.01'W",          # DDM
])
def test_parse_just_past_extremes_rejected(text):
    with pytest.raises(ValueError, match="out of range"):
        parse_coordinate(text)


@pytest.mark.parametrize("fn, value, axis, expected", [
    (to_dms, 40.99999999, "lat", '41°00\'00.00"N'),      # seconds carry into minutes and degrees
    (to_dms, 179.99999999, "lon", '180°00\'00.00"E'),
    (to_ddm, -33.99999999, "lat", "34°00.0000'S"),
    (to_dd, 59.9999999, "lat", "60.000000°N"),
    (to_dms, -0.0000001, "lon", '0°00\'00.00"E'),        # rounds to zero: no minus hemisphere
    (to_ddm, -0.0000001, "lat", "0°00.0000'N"),
    (to_dd, -0.0000001, "lat", "0.000000°N"),
])
def test_rounding_carry_and_negative_zero(fn, value, axis, expected):
    assert fn(value, axis) == expected
