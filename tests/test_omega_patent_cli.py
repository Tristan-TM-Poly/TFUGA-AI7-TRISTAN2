from omega_patent_thesis_t.cli import main


def test_cli_demo(capsys):
    assert main(["demo"]) == 0
    out = capsys.readouterr().out
    assert "EXAMPLE-PATENT-T" in out


def test_cli_summary(capsys):
    assert main(["summary"]) == 0
    out = capsys.readouterr().out
    assert "Technical Record Summary" in out
