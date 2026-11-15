import json
import runpy
from pathlib import Path

import pytest

from dms_convert import parse_coordinate

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"
build = runpy.run_path(str(EXAMPLES / "make_geojson.py"))["build"]

# Reference positions (lat, lon) of the landmarks, to about 1e-3 degrees; same
# source as the data (see README, "Data source and license").
KNOWN = {
    "Eiffel Tower": (48.8584, 2.2945),
    "Statue of Liberty": (40.6892, -74.0445),
    "Sydney Opera House": (-33.8568, 151.2153),
    "Christ the Redeemer": (-22.9519, -43.2105),
    "Great Pyramid of Giza": (29.9792, 31.1342),
    "Taj Mahal": (27.1751, 78.0421),
}


def test_checked_in_geojson_matches_tool_output():
    with open(EXAMPLES / "landmarks.geojson", encoding="utf-8") as fh:
        assert json.load(fh) == build(EXAMPLES / "landmarks.csv")


def test_demo_notebook_executes_and_prints_expected_output(capsys):
    nb = json.loads((EXAMPLES / "demo.ipynb").read_text(encoding="utf-8"))
    scope: dict = {}
    for cell in nb["cells"]:
        if cell["cell_type"] == "code":
            exec("".join(cell["source"]), scope)  # the repository's own notebook
    assert capsys.readouterr().out.splitlines() == [
        "40.4461 -79.9822",
        "40°26.7667'N 79°58.9333'W",
        "40°26'46\"N 79°58'56\"W",
    ]


def test_demo_points_are_lon_lat_at_known_places():
    features = build(EXAMPLES / "landmarks.csv")["features"]
    assert {f["properties"]["name"] for f in features} == set(KNOWN)
    for f in features:
        lon, lat = f["geometry"]["coordinates"]
        assert (lat, lon) == pytest.approx(KNOWN[f["properties"]["name"]], abs=1e-3)
        assert parse_coordinate(f["properties"]["dms"]) == pytest.approx((lat, lon), abs=1e-3)
