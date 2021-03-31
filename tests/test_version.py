from betterproto import __version__
from pathlib import Path
import toml

PROJECT_TOML = Path(__file__).joinpath("..", "..", "pyproject.toml").resolve()


def test_version():
    with PROJECT_TOML.open() as toml_file:
        project_config = toml.load(toml_file)
    assert (
        __version__ == project_config["tool"]["poetry"]["version"]
    ), "Project version should match in package and package config"
