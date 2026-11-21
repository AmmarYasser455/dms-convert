import re
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

BRAND = Path(__file__).resolve().parent.parent / "assets" / "brand"
ACCENT = "#F2552C"
LOGOS = [("logo.svg", "#121417"), ("logo-dark.svg", "#F3EEE4")]
FORBIDDEN_TAGS = {"text", "image", "filter", "linearGradient", "radialGradient", "style"}
FORBIDDEN_ATTRS = {"opacity", "fill-opacity", "stroke-opacity", "filter", "style"}


def _root(name):
    path = BRAND / name
    assert path.exists(), path
    return ET.parse(path).getroot()


def _local(tag):
    return tag.rsplit("}", 1)[-1]


@pytest.mark.parametrize("name,ink", LOGOS)
def test_logo_canvas_and_colours(name, ink):
    root = _root(name)
    assert root.get("viewBox") == "0 0 100 100"
    assert root.get("width") == "100" and root.get("height") == "100"
    text = (BRAND / name).read_text(encoding="utf-8")
    colours = set(re.findall(r"#[0-9A-Fa-f]{6}\b", text))
    assert colours == {ink, ACCENT}


@pytest.mark.parametrize("name,ink", LOGOS)
def test_logo_has_no_forbidden_features(name, ink):
    for el in _root(name).iter():
        assert _local(el.tag) not in FORBIDDEN_TAGS, el.tag
        assert not FORBIDDEN_ATTRS & set(el.attrib), el.attrib


@pytest.mark.parametrize("name,ink", LOGOS)
def test_logo_circles_stay_inside_viewbox(name, ink):
    for el in _root(name).iter():
        if _local(el.tag) == "circle":
            cx, cy, r = (float(el.get(k)) for k in ("cx", "cy", "r"))
            assert 0 <= cx - r and cx + r <= 100, el.attrib
            assert 0 <= cy - r and cy + r <= 100, el.attrib
