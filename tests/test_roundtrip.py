import pytest

from dms_convert import format_coordinate, parse_coordinate

# Real places (lat, lon) in all four hemisphere combinations, plus the
# extremes of the valid range: poles, antimeridian and the equator/prime meridian.
PLACES = [
    (40.7128, -74.0060),     # New York (N, W)
    (-33.8688, 151.2093),    # Sydney (S, E)
    (30.0131, 31.2089),      # Giza (N, E)
    (-34.6037, -58.3816),    # Buenos Aires (S, W)
    (51.4779, -0.0015),      # Greenwich observatory, just west of 0
    (-0.1807, -78.4678),     # Quito, just south of the equator
    (90.0, 180.0),
    (-90.0, -180.0),
    (0.0, 0.0),
]


@pytest.mark.parametrize("fmt,precision", [("dd", 6), ("dms", 4), ("ddm", 6)])
@pytest.mark.parametrize("lat,lon", PLACES)
def test_format_then_parse_round_trips(lat, lon, fmt, precision):
    text = format_coordinate(lat, lon, fmt, precision)
    back_lat, back_lon = parse_coordinate(text)
    # 1e-6 deg is about 0.1 m; a swapped axis or sign error is far larger.
    assert back_lat == pytest.approx(lat, rel=0, abs=1e-6)
    assert back_lon == pytest.approx(lon, rel=0, abs=1e-6)


def test_hemisphere_letters_follow_signs():
    assert format_coordinate(-0.1807, -78.4678, "dd", 4) == "0.1807°S 78.4678°W"
    assert format_coordinate(51.4779, -0.0015, "dd", 4) == "51.4779°N 0.0015°W"
