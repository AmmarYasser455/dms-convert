"""One table covering every public entry point with null/empty/wrong-type/NaN input."""

import io
import json
import math
from pathlib import Path

import pytest

from dms_convert import (
    format_coordinate, parse_angle, parse_coordinate, to_dd, to_ddm, to_dms,
)
from dms_convert.cli import main

BAD_TEXT = [None, 5, 4.5, b"40 N 10 E", ["40", "10"], {"lat": 40}, ("40", "10"), True,
            float("nan"), "", "   ", "\n", ",", "nan", "nan, nan", "inf, 10",
            "N E", "1e5, 10", "1e2N", "1e2 N", "1E2S", "1e+2N","40..5N", "40..5N, 10E", "40.5.5, 10", "40-10", "40,,10", "40, 10, 5", "\x00", "40° ° 10"]
BAD_NUM = [None, "40", [40], {"a": 1}, (40,), True, float("nan"), float("inf"),
           float("-inf"), 91, -91, b"1", 1 + 2j]

CASES = [(f, (t,)) for f in (parse_coordinate, parse_angle) for t in BAD_TEXT]
CASES += [(f, (v, "lat")) for f in (to_dd, to_dms, to_ddm) for v in BAD_NUM]
CASES += [(f, (40, ax)) for f in (to_dd, to_dms, to_ddm) for ax in (None, "", "x", 1, "LAT", ["lat"])]
CASES += [(f, (40, "lat", p)) for f in (to_dd, to_dms, to_ddm)
          for p in (None, "2", 2.0, True, -1, 13, float("nan"))]
CASES += [(format_coordinate, (lat, lon)) for lat in (None, "1", float("nan"))
          for lon in (1, None, float("inf"))]
CASES += [(format_coordinate, (1, 1, fmt)) for fmt in (None, "", "DD", "utm", 1, ["dd"])]
CASES += [(parse_coordinate, (t,)) for t in (
    "40", "40 N", "40°30'", "40°30'15\"", "40d30m", "40 30'", "40°30'N", "40°30'15\"N",
    # incomplete single angles must not become a (lat, lon) pair
    "40°30", "40° 30", "40:30", "40:30:15", "-40°30", "40d30", "40deg 30", "40:-30",
    "40: 30", ":40 10", "40 10:", "40°30.5", "N 40°30 W", "40:30°")]
CASES += [(parse_angle, (t,)) for t in (":40", "40:", "40::30", "40:°30", "40°:30", "40':30")]
CASES += [(parse_angle, ("40", ax)) for ax in ("", "x", 1, ["lat"])]


@pytest.mark.parametrize("func,args", CASES)
def test_bad_input_raises_cleanly(func, args):
    with pytest.raises((ValueError, TypeError)):
        func(*args)


@pytest.mark.parametrize("text", ["", "   ", "\n\n", "nan, nan", "garbage"])
def test_cli_bad_or_empty_stdin_never_crashes(monkeypatch, capsys, text):
    monkeypatch.setattr("sys.stdin", io.StringIO(text))
    try:
        code = main([])
    except SystemExit as exc:  # argparse usage error for empty input
        code = exc.code
    assert code != 0
    assert capsys.readouterr().out == ""


def test_cli_rejects_nan_precision():
    with pytest.raises(SystemExit):
        main(["-p", "nan", "40, 10"])


def test_geojson_coordinates_are_finite_lon_lat():
    path = Path(__file__).resolve().parent.parent / "examples" / "landmarks.geojson"
    data = json.loads(path.read_text(encoding="utf-8"))
    for f in data["features"]:
        lon, lat = f["geometry"]["coordinates"]
        assert math.isfinite(lon) and math.isfinite(lat)
        assert -180 <= lon <= 180 and -90 <= lat <= 90
