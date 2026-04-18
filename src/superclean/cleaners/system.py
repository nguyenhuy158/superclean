import os
import shutil
import tempfile
from ..core import BaseCleaner, CleanResult


class SystemCleaner(BaseCleaner):
    @property
    def name(self) -> str:
        return "system"

    @property
    def category(self) -> str:
        return "System"

    @property
    def description(self) -> str:
        return "Cleans system temporary files"

    def _get_temp_dir(self):
        return tempfile.gettempdir()

    def check_space(self) -> int:
        return self.get_dir_size(self._get_temp_dir())

    def clean(self, dry_run: bool = False) -> CleanResult:
        reclaimed = self.check_space()
        temp_dir = self._get_temp_dir()

        if not dry_run:
            for item in os.listdir(temp_dir):
                item_path = os.path.join(temp_dir, item)
                try:
                    if os.path.isfile(item_path) or os.path.islink(item_path):
                        os.unlink(item_path)
                    elif os.path.isdir(item_path):
                        shutil.rmtree(item_path, ignore_errors=True)
                except Exception:
                    # Some files might be in use
                    pass

        return CleanResult(self.name, reclaimed, True)
