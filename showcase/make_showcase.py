"""Build the dms-convert showcase from showcase/data/ (offline).

Usage (from the repository root): python showcase/make_showcase.py [output_dir]

Reads six landmark positions written in six different text styles, parses them
with dms_convert.parse_coordinate, measures the great-circle distance from the
Great Pyramid of Giza to each landmark, and writes map.geojson, map.png and
index.html. Coordinates are WGS84 (EPSG:4326); GeoJSON order is [lon, lat].
"""

from __future__ import annotations

import csv
import json
import math
import sys
from pathlib import Path

from dms_convert import parse_coordinate, to_dms

HERE = Path(__file__).resolve().parent
DATA = HERE / "data" / "landmarks.csv"
ORIGIN = "Great Pyramid of Giza"
EARTH_RADIUS_KM = 6371.0088  # IAU/IUGG mean radius; spherical model, error up to ~0.5 %
CREDIT = "Data: Wikidata (CC0), positions rounded to ~1e-4 deg"
REPO = "https://github.com/AmmarYasser455/dms-convert"


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in kilometres between two lat/lon points in degrees."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    a = (math.sin((p2 - p1) / 2) ** 2
         + math.cos(p1) * math.cos(p2) * math.sin(math.radians(lon2 - lon1) / 2) ** 2)
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))


def build(csv_path: Path = DATA) -> dict:
    """Parse the table and return a GeoJSON FeatureCollection (WGS84, [lon, lat])."""
    rows = []
    with open(csv_path, encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            lat, lon = parse_coordinate(row["coordinate"])
            rows.append((row["name"], row["coordinate"], lat, lon))
    olat, olon = next((r[2], r[3]) for r in rows if r[0] == ORIGIN)
    features = []
    for name, raw, lat, lon in rows:
        dist = haversine_km(olat, olon, lat, lon)
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [round(lon, 6), round(lat, 6)]},
            "properties": {
                "name": name,
                "input": raw,
                "dms": f"{to_dms(lat, 'lat', 0)} {to_dms(lon, 'lon', 0)}",
                "lat": round(lat, 6),
                "lon": round(lon, 6),
                "km_from_giza": round(dist, 1),
            },
        })
    return {"type": "FeatureCollection", "features": features}


def plot(collection: dict, path: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(9, 5.2), dpi=150)
    ax.set_xlim(-180, 180)
    ax.set_ylim(-90, 90)
    ax.set_aspect("equal")
    ax.grid(True, color="#d0d0d0", linewidth=0.6)
    ax.set_xlabel("Longitude (deg, WGS84 / EPSG:4326, east positive)")
    ax.set_ylabel("Latitude (deg, north up)")
    feats = collection["features"]
    origin = next(f for f in feats if f["properties"]["name"] == ORIGIN)
    ox, oy = origin["geometry"]["coordinates"]
    for f in feats:
        x, y = f["geometry"]["coordinates"]
        p = f["properties"]
        if p["name"] == ORIGIN:
            ax.scatter([x], [y], s=110, marker="*", color="#c0392b", zorder=3, label="Reference: " + ORIGIN)
            ax.annotate(p["name"], (x, y), xytext=(6, 8), textcoords="offset points", fontsize=8)
            continue
        ax.plot([ox, x], [oy, y], color="#9bb7d4", linewidth=0.8, zorder=1)
        ax.scatter([x], [y], s=40, color="#1f5f99", zorder=2)
        ax.annotate(f"{p['name']}\n{p['km_from_giza']:,.0f} km", (x, y), xytext=(6, 6),
                    textcoords="offset points", fontsize=7)
    ax.scatter([], [], s=40, color="#1f5f99", label="Landmark (labelled with km from Giza)")
    ax.legend(loc="lower left", fontsize=7)
    ax.set_title("Six landmarks, six coordinate formats, one map", fontsize=11)
    fig.text(0.99, 0.01, CREDIT + ". Lines are straight on this plot; km are great-circle.",
             ha="right", va="bottom", fontsize=6, color="#444444")
    fig.subplots_adjust(left=0.08, right=0.98, top=0.93, bottom=0.12)
    fig.savefig(path, dpi=150)
    plt.close(fig)


HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>dms-convert showcase: six landmarks, six coordinate formats</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
<style>
body { margin: 0; font-family: sans-serif; }
header { padding: 8px 14px; }
h1 { font-size: 1.2em; margin: 0 0 4px; }
p { margin: 2px 0; font-size: 0.9em; }
#map { height: calc(100vh - 110px); }
</style>
</head>
<body>
<header>
<h1>Six landmarks, six coordinate formats, one map</h1>
<p>Each position was written as text in a different style and parsed with dms-convert; popups show the original text and the distance from the Great Pyramid of Giza.</p>
<p>Distances are great-circle, in km. Data: Wikidata (CC0). <a href="__REPO__">dms-convert on GitHub</a></p>
</header>
<div id="map"></div>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
var map = L.map('map');
L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
  maxZoom: 19,
  attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
}).addTo(map);
function esc(s) { return String(s).replace(/[&<>"]/g, function (c) {
  return {'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'}[c]; }); }
fetch('map.geojson').then(function (r) { return r.json(); }).then(function (data) {
  var layer = L.geoJSON(data, {
    pointToLayer: function (f, ll) {
      var ref = f.properties.km_from_giza === 0;
      return L.circleMarker(ll, {radius: ref ? 9 : 6, color: ref ? '#c0392b' : '#1f5f99',
                                 fillOpacity: 0.8});
    },
    onEachFeature: function (f, l) {
      var p = f.properties;
      l.bindPopup('<b>' + esc(p.name) + '</b><br>input: ' + esc(p.input) +
        '<br>DMS: ' + esc(p.dms) + '<br>lat, lon: ' + p.lat + ', ' + p.lon +
        '<br>' + p.km_from_giza + ' km from Giza');
    }
  }).addTo(map);
  map.fitBounds(layer.getBounds().pad(0.1));
});
</script>
</body>
</html>
"""


def write_all(out: Path, with_png: bool = True) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    collection = build()
    (out / "map.geojson").write_text(
        json.dumps(collection, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out / "index.html").write_text(HTML.replace("__REPO__", REPO), encoding="utf-8")
    if with_png:
        plot(collection, out / "map.png")
    return collection


def main(argv: list[str]) -> None:
    write_all(Path(argv[0]) if argv else HERE)


if __name__ == "__main__":
    main(sys.argv[1:])
