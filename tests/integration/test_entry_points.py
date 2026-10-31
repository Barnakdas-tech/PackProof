"""Both documented entry points, executed as real subprocesses.

These are integration tests because they cross a process boundary: interpreter startup,
the installed distribution metadata, and the packaging entry points all have to line up
for `python -m packproof` to work for someone who just cloned the repo.
"""

import subprocess
import sys
from importlib.metadata import entry_points

import pytest

import packproof

TIMEOUT_SECONDS = 60


def run(*argv: str) -> subprocess.CompletedProcess[str]:
    """Launch a real interpreter. Callers pass only `sys.executable` and literal
    arguments — never data derived from a scanned package — so the bandit warning
    about untrusted input does not apply here."""
    return subprocess.run(  # noqa: S603
        argv,
        capture_output=True,
        text=True,
        timeout=TIMEOUT_SECONDS,
    )


@pytest.mark.integration
def test_module_entry_point_prints_help() -> None:
    result = run(sys.executable, "-m", "packproof", "--help")

    assert result.returncode == 0, result.stderr
    assert "Usage: python -m packproof" in result.stdout
    assert "--version" in result.stdout


@pytest.mark.integration
def test_module_entry_point_reports_the_installed_version() -> None:
    result = run(sys.executable, "-m", "packproof", "--version")

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == f"packproof {packproof.__version__}"


@pytest.mark.integration
def test_console_script_target_and_module_execution_agree() -> None:
    """`packproof` calls `packproof.cli.main:main`; `python -m packproof` calls the same
    function. Invoking the script target directly proves the two cannot drift apart."""
    script_target = run(
        sys.executable,
        "-c",
        "from packproof.cli.main import main; main()",
        "--version",
    )
    module = run(sys.executable, "-m", "packproof", "--version")

    assert script_target.returncode == 0, script_target.stderr
    assert script_target.stdout == module.stdout


@pytest.mark.integration
def test_declared_console_script_entry_point_loads() -> None:
    """A renamed or moved `main` would break the installed command while the tests that
    import it directly stayed green. This test closes that gap."""
    scripts = [ep for ep in entry_points(group="console_scripts") if ep.name == "packproof"]

    assert len(scripts) == 1, f"expected exactly one `packproof` script, got {scripts}"
    assert scripts[0].value == "packproof.cli.main:main"

    loaded = scripts[0].load()
    assert loaded.__module__ == "packproof.cli.main"
    assert loaded.__name__ == "main"


@pytest.mark.integration
def test_module_entry_point_rejects_an_unimplemented_command() -> None:
    result = run(sys.executable, "-m", "packproof", "scan", "express@4.21.2")

    assert result.returncode == 2
    assert "No such command 'scan'" in result.stderr
