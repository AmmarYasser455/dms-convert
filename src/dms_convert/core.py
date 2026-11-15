"""Tolerant coordinate parsing and formatting."""

from __future__ import annotations

import math
import re

_LIMITS = {"lat": 90.0, "lon": 180.0}
_HEMI = {"N": ("lat", 1), "S": ("lat", -1), "E": ("lon", 1), "W": ("lon", -1)}
_DEG, _MIN, _SEC = 0, 1, 2
_UNIT_WORDS = {
    **dict.fromkeys(["d", "deg", "degs", "degree", "degrees"], _DEG),
    **dict.fromkeys(["m", "min", "mins", "minute", "minutes"], _MIN),
    **dict.fromkeys(["sec", "secs", "second", "seconds"], _SEC),
}
_TOKEN = re.compile(
    r"(?P<num>[-+]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+))"
    r"|(?P<sec>″|''|’’|′′|\"|”|“)"
    r"|(?P<min>′|'|’|‘)"
    r"|(?P<deg>°|º|˚)"
    r"|(?P<word>[A-Za-z]+)"
    r"|(?P<sep>[,;/|])"
    r"|(?P<colon>:)"
    r"|(?P<space>\s+)"
)


def _tokenize(text: str) -> list[tuple[str, object]]:
    """Split text into ("num", str), ("unit", int), ("hemi", letter) and ("sep", str) tokens.

    Unit identity is kept so values are not interpreted by position alone.
    A glued lowercase ``s`` is seconds only after a minutes mark (``40d26m46s``);
    a spaced or uppercase ``S`` is always the southern hemisphere.
    """
    if not isinstance(text, str):
        raise TypeError(f"expected a string, got {type(text).__name__}")
    tokens: list[tuple[str, object]] = []
    last_unit = None  # last explicit unit since the previous separator/hemisphere
    pos, prev_end_num = 0, -1
    while pos < len(text):
        m = _TOKEN.match(text, pos)
        if not m:
            raise ValueError(f"cannot parse {text!r}: unexpected character {text[pos]!r}")
        kind, value = m.lastgroup, m.group()
        glued = m.start() == prev_end_num
        pos = m.end()
        if kind == "num" and glued:
            raise ValueError(f"cannot parse {text!r}: malformed number near {value!r}")
        if kind == "space":
            continue
        if kind in ("sec", "min", "deg"):
            unit = {"deg": _DEG, "min": _MIN, "sec": _SEC}[kind]
            tokens.append(("unit", unit))
            last_unit = unit
        elif kind == "word":
            if glued and value in ("e", "E") and text[pos : pos + 1] in tuple("0123456789.+-") \
                    and pos < len(text):
                raise ValueError(
                    f"cannot parse {text!r}: ambiguous 'E' (exponent or east) after a number"
                )
            for k, v in _read_word(value, glued, last_unit, text):
                tokens.append((k, v))
                if k == "unit":
                    last_unit = v
                else:
                    last_unit = None
        else:
            tokens.append((kind, value))
            if kind == "sep":
                last_unit = None
        prev_end_num = pos if kind == "num" else -1
    return tokens


def _read_word(word: str, glued: bool, last_unit: int | None, text: str) -> list[tuple[str, object]]:
    low = word.lower()
    if low in _UNIT_WORDS:
        return [("unit", _UNIT_WORDS[low])]
    if word == "s" and glued:
        if last_unit == _MIN:
            return [("unit", _SEC)]
        raise ValueError(f"cannot parse {text!r}: ambiguous 's' (seconds or south); use \" or S")
    if word.upper() in _HEMI and len(word) == 1:
        return [("hemi", word.upper())]
    # unit letter/word glued to a hemisphere letter, e.g. "46sN"
    if len(word) > 1 and word[-1].upper() in _HEMI:
        head = word[:-1]
        if head.lower() in _UNIT_WORDS or (head == "s" and glued and last_unit == _MIN):
            unit = _UNIT_WORDS.get(head.lower(), _SEC)
            return [("unit", unit), ("hemi", word[-1].upper())]
    raise ValueError(f"cannot parse {text!r}: unknown word {word!r}")


def _parse_tokens(tokens: list[tuple[str, object]], text: str) -> tuple[float, str | None]:
    """Parse the tokens of one angle; return (signed value, axis or None)."""
    hemis = [i for i, (k, _) in enumerate(tokens) if k == "hemi"]
    axis, sign = None, 1
    if len(hemis) > 1:
        raise ValueError(f"cannot parse {text!r}: more than one hemisphere letter")
    if hemis:
        if hemis[0] not in (0, len(tokens) - 1):
            raise ValueError(f"cannot parse {text!r}: hemisphere letter in the middle")
        axis, sign = _HEMI[tokens[hemis[0]][1]]
        tokens = tokens[1:] if hemis[0] == 0 else tokens[:-1]
    nums: list[tuple[str, int | None]] = []
    for i, (kind, value) in enumerate(tokens):
        if kind == "colon":
            # "40:26:46" -- a colon may only join two unmarked numbers
            if not (0 < i < len(tokens) - 1 and tokens[i - 1][0] == "num"
                    and tokens[i + 1][0] == "num"):
                raise ValueError(f"cannot parse {text!r}: misplaced ':'")
        elif kind == "num":
            nums.append((value, None))
        elif kind == "unit" and nums and nums[-1][1] is None:
            nums[-1] = (nums[-1][0], value)
        else:
            raise ValueError(f"cannot parse {text!r}")
    if not 1 <= len(nums) <= 3:
        raise ValueError(f"cannot parse {text!r}: expected 1 to 3 numbers")
    if any(n[0] in "+-" for n, _ in nums[1:]):
        raise ValueError(f"cannot parse {text!r}: sign inside the value")
    if nums[0][0][0] in "+-" and axis is not None:
        raise ValueError(f"cannot parse {text!r}: sign and hemisphere letter both given")
    units, prev = [], -1
    for _, unit in nums:
        unit = prev + 1 if unit is None else unit
        if unit <= prev or unit > _SEC:
            raise ValueError(f"cannot parse {text!r}: units out of order")
        units.append(unit)
        prev = unit
    vals = [abs(float(n)) for n, _ in nums]
    if not all(math.isfinite(v) for v in vals):
        raise ValueError(f"cannot parse {text!r}: value is not finite")
    if any(v >= 60 for v, u in zip(vals, units) if u != _DEG):
        raise ValueError(f"cannot parse {text!r}: minutes/seconds must be below 60")
    if any(v != int(v) for v in vals[:-1]):
        raise ValueError(f"cannot parse {text!r}: only the last number may have decimals")
    value = sum(v / 60 ** u for v, u in zip(vals, units))
    return (-value if nums[0][0].startswith("-") else value) * sign, axis


def _check_axis(axis: object, allow_none: bool = False) -> None:
    if axis is None and allow_none:
        return
    if not isinstance(axis, str) or axis not in _LIMITS:
        raise ValueError(f"axis must be 'lat' or 'lon', got {axis!r}")


def _check(value: float, axis: str | None) -> None:
    if axis and abs(value) > _LIMITS[axis]:
        raise ValueError(f"{axis} {value} out of range (±{_LIMITS[axis]:g})")


def parse_angle(text: str, axis: str | None = None) -> float:
    """Parse one angle to decimal degrees. ``axis`` ("lat"/"lon") enables range checks."""
    _check_axis(axis, allow_none=True)
    tokens = _tokenize(text)
    if any(k == "sep" for k, _ in tokens):
        raise ValueError(f"cannot parse {text!r}: separator in a single angle")
    value, found = _parse_tokens(tokens, text)
    if axis is not None and found not in (None, axis):
        raise ValueError(f"{text!r} is a {found} value, expected {axis}")
    _check(value, axis or found)
    return value


def _number_split(tokens: list[tuple[str, object]]) -> int | None:
    """Index where the second value starts in letter-free tokens, or None if unclear.

    A value starts at the first number, at a signed number, or at a number marked
    with a degree unit. With exactly two numbers and no unit marks at all, each
    number is a value. A number after ':' always continues the current angle, so
    incomplete single angles such as ``40°30`` or ``40:30`` are never split.
    """
    nums = [i for i, (k, _) in enumerate(tokens) if k == "num"]

    def after(i: int) -> tuple[str, object] | None:
        return tokens[i + 1] if i + 1 < len(tokens) else None

    unmarked = all(after(i) is None or after(i)[0] != "unit" for i in nums)
    starts = [i for n, i in enumerate(nums) if n == 0
              or (tokens[i - 1][0] != "colon"
                  and (str(tokens[i][1])[0] in "+-"
                       or after(i) == ("unit", _DEG)
                       or (len(nums) == 2 and unmarked)))]
    if len(starts) == 2 and starts[0] == 0:
        return starts[1]
    return None


def _split(tokens: list[tuple[str, object]], text: str) -> list[list[tuple[str, object]]]:
    seps = [i for i, (k, _) in enumerate(tokens) if k == "sep"]
    hemis = [i for i, (k, _) in enumerate(tokens) if k == "hemi"]
    parts: list[list[tuple[str, object]]] = []
    last = len(tokens) - 1
    if seps:
        if len(seps) == 1:
            parts = [tokens[: seps[0]], tokens[seps[0] + 1 :]]
    elif len(hemis) == 2:
        h0, h1 = hemis
        if h0 == 0 and h1 == last:
            # prefix + suffix ("N 40.7 74.0 W"): split the numbers between them
            cut = _number_split(tokens[1:-1])
            if cut is not None:
                parts = [tokens[: cut + 1], tokens[cut + 1 :]]
        elif h1 == h0 + 1:
            # suffix + prefix ("40.7 N W 74.0"): split between the letters
            parts = [tokens[:h1], tokens[h1:]]
        elif h0 == 0:
            parts = [tokens[:h1], tokens[h1:]]  # both prefixes
        elif h1 == last:
            parts = [tokens[: h0 + 1], tokens[h0 + 1 :]]  # both suffixes
    elif not hemis:
        cut = _number_split(tokens)
        if cut is not None:
            parts = [tokens[:cut], tokens[cut:]]
    if len(parts) != 2 or not all(parts):
        raise ValueError(f"cannot find exactly two coordinates in {text!r}")
    return parts


def parse_coordinate(text: str) -> tuple[float, float]:
    """Parse a latitude/longitude pair to ``(lat, lon)`` in decimal degrees.

    Without hemisphere letters the order is latitude, longitude. Letters
    (N/S/E/W) may prefix or suffix each part and may put longitude first.
    """
    first, second = _split(_tokenize(text), text)
    (a, ax_a), (b, ax_b) = _parse_tokens(first, text), _parse_tokens(second, text)
    if ax_a == "lon" or ax_b == "lat":
        if ax_a == "lat" or ax_b == "lon":
            raise ValueError(f"conflicting hemisphere letters in {text!r}")
        a, b = b, a
    elif ax_a is not None and ax_a == ax_b:
        raise ValueError(f"both values are {ax_a} in {text!r}")
    _check(a, "lat")
    _check(b, "lon")
    return a, b


def _value(value: object, axis: str) -> float:
    _check_axis(axis)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"expected a number, got {type(value).__name__}")
    value = float(value)
    if not math.isfinite(value):
        raise ValueError(f"{axis} value must be finite, got {value}")
    _check(value, axis)
    return value


def _precision(precision: object) -> int:
    if isinstance(precision, bool) or not isinstance(precision, int):
        raise TypeError(f"precision must be an int, got {type(precision).__name__}")
    if not 0 <= precision <= 12:
        raise ValueError(f"precision must be between 0 and 12, got {precision}")
    return precision


def _hemi(negative: bool, axis: str) -> str:
    return ("S" if negative else "N") if axis == "lat" else ("W" if negative else "E")


def to_dd(value: float, axis: str = "lat", precision: int = 6) -> str:
    """Format as decimal degrees with a hemisphere letter, e.g. ``40.446111°N``."""
    value, precision = _value(value, axis), _precision(precision)
    rounded = round(value, precision)
    return f"{abs(rounded):.{precision}f}°{_hemi(rounded < 0, axis)}"


def to_dms(value: float, axis: str = "lat", precision: int = 2) -> str:
    """Format as degrees, minutes, seconds, e.g. ``40°26'46.00"N``."""
    value, precision = _value(value, axis), _precision(precision)
    scale = 10 ** precision
    total = round(abs(value) * 3600 * scale)
    deg, rem = divmod(total, 3600 * scale)
    mins, secs = divmod(rem, 60 * scale)
    sec = f"{secs / scale:0{3 + precision if precision else 2}.{precision}f}"
    return f"{deg}°{mins:02d}'{sec}\"{_hemi(value < 0 and total > 0, axis)}"


def to_ddm(value: float, axis: str = "lat", precision: int = 4) -> str:
    """Format as degrees and decimal minutes, e.g. ``40°26.7667'N``."""
    value, precision = _value(value, axis), _precision(precision)
    scale = 10 ** precision
    total = round(abs(value) * 60 * scale)
    deg, mins = divmod(total, 60 * scale)
    m = f"{mins / scale:0{3 + precision if precision else 2}.{precision}f}"
    return f"{deg}°{m}'{_hemi(value < 0 and total > 0, axis)}"


_FORMATS = {"dd": to_dd, "dms": to_dms, "ddm": to_ddm}


def format_coordinate(lat: float, lon: float, fmt: str = "dd", precision: int | None = None) -> str:
    """Format a (lat, lon) pair as ``dd``, ``dms`` or ``ddm``."""
    if not isinstance(fmt, str) or fmt not in _FORMATS:
        raise ValueError(f"unknown format {fmt!r}; choose from {', '.join(_FORMATS)}")
    f = _FORMATS[fmt]
    kw = {} if precision is None else {"precision": precision}
    return f"{f(lat, 'lat', **kw)} {f(lon, 'lon', **kw)}"
