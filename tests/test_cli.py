from agentic_doc.cli import app


def test_version(runner):
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Agentic AI" in result.stdout


def test_init_help(runner):
    result = runner.invoke(app, ["init", "--help"])
    assert result.exit_code == 0
    assert "Initialize the project" in result.stdout
