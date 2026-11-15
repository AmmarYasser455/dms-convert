"""Convert examples/landmarks.csv into a GeoJSON point layer (examples/landmarks.geojson).

Usage: python examples/make_geojson.py [input.csv] [output.geojson]
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

from dms_convert import parse_coordinate, to_dms

HERE = Path(__file__).resolve().parent


def build(csv_path: Path) -> dict:
    """Parse every row and return a GeoJSON FeatureCollection (RFC 7946, WGS84 lon/lat)."""
    features = []
    with open(csv_path, encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            lat, lon = parse_coordinate(row["coordinate"])
            features.append({
                "type": "Feature",
                # GeoJSON axis order is [longitude, latitude]
                "geometry": {"type": "Point", "coordinates": [round(lon, 6), round(lat, 6)]},
                "properties": {
                    "name": row["name"],
                    "input": row["coordinate"],
                    "dms": f"{to_dms(lat, 'lat', 0)} {to_dms(lon, 'lon', 0)}",
                },
            })
    return {"type": "FeatureCollection", "features": features}


def main(argv: list[str]) -> None:
    src = Path(argv[0]) if argv else HERE / "landmarks.csv"
    dst = Path(argv[1]) if len(argv) > 1 else HERE / "landmarks.geojson"
    text = json.dumps(build(src), ensure_ascii=False, indent=2) + "\n"
    dst.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main(sys.argv[1:])
