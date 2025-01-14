from pathlib import Path

import tomlkit

from betterproto import __version__


PROJECT_TOML = Path(__file__).joinpath("..", "..", "pyproject.toml").resolve()


def test_version():
    with PROJECT_TOML.open() as toml_file:
        project_config = tomlkit.loads(toml_file.read())
    assert __version__ == project_config["project"]["version"], (
        "Project version should match in package and package config"
    )
