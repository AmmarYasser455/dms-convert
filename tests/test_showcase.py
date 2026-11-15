import json
import runpy
from pathlib import Path

import pytest

SHOWCASE = Path(__file__).resolve().parent.parent / "showcase"
mod = runpy.run_path(str(SHOWCASE / "make_showcase.py"))


def test_geojson_is_current(tmp_path):
    mod["write_all"](tmp_path, with_png=False)
    fresh = json.loads((tmp_path / "map.geojson").read_text(encoding="utf-8"))
    committed = json.loads((SHOWCASE / "map.geojson").read_text(encoding="utf-8"))
    assert fresh == committed


def test_known_positions_and_distance():
    feats = {f["properties"]["name"]: f for f in mod["build"]()["features"]}
    lon, lat = feats["Sydney Opera House"]["geometry"]["coordinates"]  # [lon, lat]
    assert lon == pytest.approx(151.2153, abs=1e-4)
    assert lat == pytest.approx(-33.8569, abs=1e-4)
    # Giza to Taj Mahal is roughly 4,560 km along the great circle
    assert feats["Taj Mahal"]["properties"]["km_from_giza"] == pytest.approx(4560, rel=0.01)
    assert feats["Great Pyramid of Giza"]["properties"]["km_from_giza"] == 0


def test_notebook_executes_offline():
    nbformat = pytest.importorskip("nbformat")
    nbclient = pytest.importorskip("nbclient")
    pytest.importorskip("matplotlib")
    pytest.importorskip("ipykernel")
    nb = nbformat.read(str(SHOWCASE / "showcase.ipynb"), as_version=4)
    nbclient.NotebookClient(
        nb, timeout=120, kernel_name="python3",
        resources={"metadata": {"path": str(SHOWCASE)}},
    ).execute()
    outputs = [o for c in nb.cells if c.cell_type == "code" for o in c.get("outputs", [])]
    assert not [o for o in outputs if o.output_type == "error"]
    assert any("image/png" in o.get("data", {}) for o in outputs)


def test_png_is_produced(tmp_path):
    pytest.importorskip("matplotlib")
    mod["write_all"](tmp_path)
    png = tmp_path / "map.png"
    assert png.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
    assert (tmp_path / "index.html").exists()
