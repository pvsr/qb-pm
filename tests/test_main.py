from os import chdir, environ
from pathlib import Path

from click.testing import CliRunner

from qbpm.main import main

no_desktop = "--no-desktop-file"


def test_profile_dir_option(tmp_path: Path):
    (tmp_path / "config.py").touch()
    runner = CliRunner()
    result = runner.invoke(
        main, ["-C", str(tmp_path), "-P", str(tmp_path), "new", no_desktop, "test"]
    )
    assert result.exit_code == 0
    assert result.output.strip() == str(tmp_path / "test")
    assert tmp_path / "test" in list(tmp_path.iterdir())


def test_profile_dir_env(tmp_path: Path):
    environ["QBPM_PROFILE_DIR"] = str(tmp_path)
    (tmp_path / "config.py").touch()
    runner = CliRunner()
    result = runner.invoke(main, ["-C", str(tmp_path), "new", no_desktop, "test"])
    assert result.exit_code == 0
    assert result.output.strip() == str(tmp_path / "test")
    assert tmp_path / "test" in list(tmp_path.iterdir())


def test_config_dir_option(tmp_path: Path):
    environ["QBPM_PROFILE_DIR"] = str(tmp_path)
    config = tmp_path / "config.py"
    config.touch()
    runner = CliRunner()
    result = runner.invoke(main, ["-C", str(tmp_path), "new", no_desktop, "test"])
    assert result.exit_code == 0
    assert str(config) in (tmp_path / "test/config/config.py").read_text()


def test_relative_config_dir(tmp_path: Path):
    environ["QBPM_PROFILE_DIR"] = str(tmp_path)
    config = tmp_path / "config.py"
    config.touch()
    chdir(tmp_path)
    runner = CliRunner()
    result = runner.invoke(main, ["-C", ".", "new", no_desktop, "test"])
    assert result.exit_code == 0
    assert str(config) in (tmp_path / "test/config/config.py").read_text()


def test_from_session(tmp_path: Path):
    environ["QBPM_PROFILE_DIR"] = str(tmp_path)
    (tmp_path / "config.py").touch()
    session = tmp_path / "test.yml"
    session.write_text("windows:\n")
    runner = CliRunner()
    result = runner.invoke(
        main, ["-C", str(tmp_path), "from-session", no_desktop, str(session)]
    )
    assert result.exit_code == 0
    assert result.output.strip() == str(tmp_path / "test")
    assert (tmp_path / "test/data/sessions/_autosave.yml").read_text() == ("windows:\n")
