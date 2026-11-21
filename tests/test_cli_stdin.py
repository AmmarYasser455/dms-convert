import io

from dms_convert.cli import main


def test_stdin_batch_continues_after_a_bad_line(monkeypatch, capsys):
    """One pair per line; a bad line is reported but later lines are still converted."""
    text = "40°26'46\"N 79°58'56\"W\n\n95 N 10 E\n-33.8688, 151.2093\n"
    monkeypatch.setattr("sys.stdin", io.StringIO(text))
    status = main(["--to", "ddm", "--precision", "2"])
    out, err = capsys.readouterr()
    assert status == 1
    # Pittsburgh (lat N, lon W) and Sydney (lat S, lon E): a swapped axis would fail
    assert out.splitlines() == ["40°26.77'N 79°58.93'W", "33°52.13'S 151°12.56'E"]
    assert err.count("error:") == 1 and "out of range" in err


def test_stdin_batch_all_good_returns_zero(monkeypatch, capsys):
    monkeypatch.setattr("sys.stdin", io.StringIO("40.7128, -74.006\n-33.8688, 151.2093\n"))
    assert main(["-t", "dms", "-p", "0"]) == 0
    out, err = capsys.readouterr()
    assert out.splitlines() == ["40°42'46\"N 74°00'22\"W", "33°52'08\"S 151°12'33\"E"]
    assert err == ""
