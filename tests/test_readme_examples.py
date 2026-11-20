"""The CLI examples shown in the README must produce exactly the documented output.

Pittsburgh (40.44 N, 79.98 W), New York (40.71 N, 74.01 W) and Sydney
(33.87 S, 151.21 E) lie in different hemisphere quadrants, so a swapped axis
or a dropped sign changes the output.
"""

import pytest

from dms_convert.cli import main

EXAMPLES = [
    (["40°26'46\"N 79°58'56\"W", "--to", "ddm"], "40°26.7667'N 79°58.9333'W"),
    (["40.7128, -74.006", "--to", "dms"], "40°42'46.08\"N 74°00'21.60\"W"),
    (["W 74 0 21.6, N 40 42 46.08"], "40.712800°N 74.006000°W"),
    (["40S, 10E"], "40.000000°S 10.000000°E"),
    (["N 40.7128 74.006 W"], "40.712800°N 74.006000°W"),
    (["--to", "ddm", "--", "-33.8688, 151.2093"], "33°52.1280'S 151°12.5580'E"),
    (["-33.8688, 151.2093", "--to", "ddm"], "33°52.1280'S 151°12.5580'E"),
]


@pytest.mark.parametrize("argv,expected", EXAMPLES)
def test_readme_cli_example(capsys, argv, expected):
    assert main(argv) == 0
    assert capsys.readouterr().out.strip() == expected


def test_readme_error_example(capsys):
    assert main(["95 N 10 E"]) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err.strip() == "error: lat 95.0 out of range (±90)"


def test_one_bad_line_does_not_stop_the_rest(capsys):
    assert main(["95 N 10 E", "40S, 10E"]) == 1
    assert capsys.readouterr().out.strip() == "40.000000°S 10.000000°E"
