import json
from pathlib import Path

NB = Path(__file__).resolve().parent.parent / "examples" / "demo.ipynb"


def test_notebook_is_clean_and_executes(capsys):
    nb = json.loads(NB.read_text(encoding="utf-8"))
    assert nb["nbformat"] == 4
    scope: dict = {}
    for cell in nb["cells"]:
        if cell["cell_type"] == "code":
            assert cell["outputs"] == [] and cell["execution_count"] is None
            exec("".join(cell["source"]), scope)  # the repository's own notebook
    out = capsys.readouterr().out.splitlines()
    assert out[:3] == [
        "40.4461 -79.9822",
        "40°26.7667'N 79°58.9333'W",
        "40°26'46\"N 79°58'56\"W",
    ]
    assert "Eiffel Tower: 48.8583, 2.2944" in out
    assert "Sydney Opera House: -33.8569, 151.2153" in out
    assert len(out) == 9
