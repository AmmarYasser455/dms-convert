# Examples

- `landmarks.csv`: six landmarks, each position written in a different coordinate text style.
- `make_geojson.py`: parses the CSV with `dms_convert.parse_coordinate` and writes `landmarks.geojson` (WGS84, `[lon, lat]` order, RFC 7946). `docs/demo.geojson` is a copy of this output, shown on the map at https://ammaryasser455.github.io/dms-convert/.
- `demo.ipynb`: walkthrough of the Python API on the CSV (offline, outputs cleared).

## Data source and license

Positions are the coordinates of each landmark's Wikidata item (property P625); Wikidata structured data is CC0 1.0. They were entered by hand and rounded to about 1e-4 degrees, so they are approximate, not survey-grade. Everything here is under the repository's MIT license.
