from superclean.core import CleanerRegistry, BaseCleaner, CleanResult


class MockCleaner(BaseCleaner):
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
