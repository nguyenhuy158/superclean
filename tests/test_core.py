from superclean.core import (
    BaseCleaner,
    CacheTarget,
    CleanerRegistry,
    CleanResult,
    delete_cache_target,
    format_size,
    scan_cache_targets,
)


class MockCleaner(BaseCleaner):
    def __init__(self, cache_paths=None):
        self._cache_paths = cache_paths or []

    @property
    def name(self):
        return "mock"

    @property
    def category(self):
        return "mock category"

    @property
    def description(self):
        return "mock description"

    def check_space(self):
        return 1024

    def clean(self, dry_run=False):
        return CleanResult(self.name, 1024, True)

    def is_installed(self):
        return True

    def get_cache_paths(self):
        return self._cache_paths


def test_registry():
    registry = CleanerRegistry()
    cleaner = MockCleaner()
    registry.register(cleaner)
    assert len(registry.get_all()) == 1
    assert registry.get_by_name("mock") == cleaner


def test_clean_result():
    result = CleanResult("test", 100, True, "msg")
    assert result.name == "test"
    assert result.space_reclaimed == 100
    assert result.success is True
    assert result.message == "msg"


def test_base_cleaner_get_cache_paths_defaults_to_empty():
    """Cleaners driven by external commands (docker/nix/brew/conda) opt out by default."""

    class SubprocessCleaner(BaseCleaner):
        @property
        def name(self):
            return "subprocess-only"

        @property
        def category(self):
            return "x"

        @property
        def description(self):
            return "x"

        def check_space(self):
            return 0

        def clean(self, dry_run=False):
            return CleanResult(self.name, 0, True)

    assert SubprocessCleaner().get_cache_paths() == []


def test_format_size():
    assert format_size(0) == "0 B"
    assert format_size(1024) == "1.0 KB"
    assert format_size(1024 * 1024) == "1.0 MB"


def test_scan_cache_targets_reads_real_dirs_and_sorts_by_size_desc(tmp_path):
    small = tmp_path / "small"
    small.mkdir()
    (small / "f.bin").write_bytes(b"x" * 100)

    big = tmp_path / "big"
    big.mkdir()
    (big / "f.bin").write_bytes(b"x" * 10_000)

    missing = tmp_path / "does-not-exist"

    cleaner = MockCleaner(
        cache_paths=[
            ("small-target", str(small)),
            ("big-target", str(big)),
            ("missing-target", str(missing)),
        ]
    )
    registry = CleanerRegistry()
    registry.register(cleaner)

    targets = scan_cache_targets(registry)

    # missing paths are skipped entirely
    assert [t.label for t in targets] == ["big-target", "small-target"]
    assert all(t.cleaner == "mock" for t in targets)
    assert targets[0].size > targets[1].size


def test_delete_cache_target_removes_directory(tmp_path):
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    (cache_dir / "f.bin").write_bytes(b"x" * 500)

    target = CacheTarget(cleaner="mock", label="cache", path=str(cache_dir), size=500)
    freed = delete_cache_target(target)

    assert freed == 500
    assert not cache_dir.exists()


def test_delete_cache_target_dry_run_does_not_touch_disk(tmp_path):
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    (cache_dir / "f.bin").write_bytes(b"x" * 500)

    target = CacheTarget(cleaner="mock", label="cache", path=str(cache_dir), size=500)
    freed = delete_cache_target(target, dry_run=True)

    assert freed == 500
    assert cache_dir.exists()
