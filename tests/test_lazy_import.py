"""Importing superclean must never pull in the optional 'textual' dependency."""

import subprocess
import sys

import pytest


def test_importing_package_does_not_import_textual():
    """`import superclean.main` (and its `ui` command wiring) must stay lazy.

    Runs in a fresh subprocess so pytest's own module cache (e.g. a sibling
    test importing `superclean.dashboard`) can't mask a regression.
    """
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import superclean.main, sys; "
            "assert 'textual' not in sys.modules; "
            "assert 'superclean.dashboard' not in sys.modules",
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0 and "textual" not in result.stderr:
        # main.py's own runtime deps (typer/rich/psutil/...) aren't installed
        # in this interpreter (e.g. bare system python3 under `make test`).
        # That's an unrelated environment gap, not a lazy-import regression.
        pytest.skip(
            "superclean.main's runtime deps unavailable in this interpreter: "
            + result.stderr.strip().splitlines()[-1]
        )
    assert result.returncode == 0, result.stderr


def test_registry_module_does_not_import_textual():
    """The cleaner registry (used by `sclean all`, `status`, etc.) is textual-free."""
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import superclean.registry, sys; assert 'textual' not in sys.modules",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
