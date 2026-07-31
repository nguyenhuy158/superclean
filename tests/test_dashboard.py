"""Headless pilot smoke tests for the CacheDashboard Textual app.

These NEVER touch real caches: a fake CleanerRegistry with a MockCleaner
pointed at pytest's tmp_path is injected into the App, so scanning and
"clean" both operate purely on throwaway directories.
"""

import pytest

pytest.importorskip("textual")

from superclean.core import BaseCleaner, CleanerRegistry, CleanResult  # noqa: E402
from superclean.dashboard import CacheDashboard  # noqa: E402


class FakeCleaner(BaseCleaner):
    """Minimal cleaner exposing two fake cache paths under tmp_path."""

    def __init__(self, cache_paths):
        self._cache_paths = cache_paths

    @property
    def name(self):
        return "fake"

    @property
    def category(self):
        return "fake"

    @property
    def description(self):
        return "fake cleaner for tests"

    def check_space(self):
        return sum(self.get_dir_size(p) for _, p in self._cache_paths)

    def clean(self, dry_run=False):
        return CleanResult(self.name, 0, True)

    def get_cache_paths(self):
        return self._cache_paths


def _make_fake_dir(tmp_path, name, num_bytes):
    d = tmp_path / name
    d.mkdir()
    (d / "data.bin").write_bytes(b"x" * num_bytes)
    return d


def _fake_registry(tmp_path):
    small = _make_fake_dir(tmp_path, "small-cache", 100)
    big = _make_fake_dir(tmp_path, "big-cache", 5_000)
    registry = CleanerRegistry()
    registry.register(
        FakeCleaner([("small", str(small)), ("big", str(big))])
    )
    return registry, small, big


async def test_mount_scans_and_renders_rows_sorted_by_size_desc(tmp_path):
    registry, small, big = _fake_registry(tmp_path)
    app = CacheDashboard(registry=registry)

    async with app.run_test() as pilot:
        await app.workers.wait_for_complete()
        await pilot.pause()

        assert len(app._targets) == 2
        # Largest target first.
        assert app._targets[0].path == str(big)
        assert app._targets[1].path == str(small)

        table = app.query_one("#targets-table")
        assert table.row_count == 2


async def test_toggle_selection_with_space(tmp_path):
    registry, small, big = _fake_registry(tmp_path)
    app = CacheDashboard(registry=registry)

    async with app.run_test() as pilot:
        await app.workers.wait_for_complete()
        await pilot.pause()

        assert app._selected == set()
        await pilot.press("space")
        assert app._selected == {app._targets[0].path}

        await pilot.press("space")
        assert app._selected == set()


async def test_toggle_all_with_a(tmp_path):
    registry, small, big = _fake_registry(tmp_path)
    app = CacheDashboard(registry=registry)

    async with app.run_test() as pilot:
        await app.workers.wait_for_complete()
        await pilot.pause()

        await pilot.press("a")
        assert app._selected == {str(small), str(big)}

        await pilot.press("a")
        assert app._selected == set()


async def test_clean_selected_opens_confirm_modal_and_cancel_keeps_files(tmp_path):
    registry, small, big = _fake_registry(tmp_path)
    app = CacheDashboard(registry=registry)

    async with app.run_test() as pilot:
        await app.workers.wait_for_complete()
        await pilot.pause()

        await pilot.press("a")  # select all
        await pilot.press("x")  # open confirm modal
        await pilot.pause()

        assert len(app.screen_stack) == 2  # ConfirmScreen pushed on top

        await pilot.press("n")  # cancel
        await pilot.pause()

        assert len(app.screen_stack) == 1
        assert small.exists()
        assert big.exists()


async def test_clean_selected_confirm_deletes_and_rescans(tmp_path):
    registry, small, big = _fake_registry(tmp_path)
    app = CacheDashboard(registry=registry)

    async with app.run_test() as pilot:
        await app.workers.wait_for_complete()
        await pilot.pause()

        await pilot.press("a")  # select all
        await pilot.press("x")  # open confirm modal
        await pilot.pause()

        await pilot.press("y")  # confirm
        await app.workers.wait_for_complete()
        await pilot.pause()

        assert not small.exists()
        assert not big.exists()
        assert app._targets == []


async def test_dry_run_clean_does_not_delete(tmp_path):
    registry, small, big = _fake_registry(tmp_path)
    app = CacheDashboard(registry=registry, dry_run=True)

    async with app.run_test() as pilot:
        await app.workers.wait_for_complete()
        await pilot.pause()

        await pilot.press("a")
        await pilot.press("x")
        await pilot.pause()
        await pilot.press("y")
        await app.workers.wait_for_complete()
        await pilot.pause()

        # Dry run: nothing actually deleted, but rescan still finds them.
        assert small.exists()
        assert big.exists()
        assert len(app._targets) == 2


async def test_quit_action(tmp_path):
    registry, _, _ = _fake_registry(tmp_path)
    app = CacheDashboard(registry=registry)

    async with app.run_test() as pilot:
        await app.workers.wait_for_complete()
        await pilot.pause()
        await pilot.press("q")
        await pilot.pause()

    assert app.return_code == 0
