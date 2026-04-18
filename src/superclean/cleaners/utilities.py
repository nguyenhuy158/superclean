import os
import shutil
from ..core import BaseCleaner, CleanResult

class LazyGitCleaner(BaseCleaner):
    @property
    def name(self) -> str:
        return "lazygit"

    @property
    def category(self) -> str:
        return "Tools"

    @property
    def description(self) -> str:
        return "Cleans Lazygit logs"

    def is_installed(self) -> bool:
        return shutil.which("lazygit") is not None

    def _get_log_dir(self):
        if os.uname().sysname == "Darwin":
            return os.path.expanduser("~/Library/Caches/lazygit")
        return os.path.expanduser("~/.cache/lazygit")

    def check_space(self) -> int:
        return self.get_dir_size(self._get_log_dir())

    def clean(self, dry_run: bool = False) -> CleanResult:
        reclaimed = self.check_space()
        path = self._get_log_dir()
        if not dry_run and os.path.exists(path):
            shutil.rmtree(path, ignore_errors=True)
        return CleanResult(self.name, reclaimed, True)

class LazyDockerCleaner(BaseCleaner):
    @property
    def name(self) -> str:
        return "lazydocker"

    @property
    def category(self) -> str:
        return "Tools"

    @property
    def description(self) -> str:
        return "Cleans Lazydocker logs"

    def is_installed(self) -> bool:
        return shutil.which("lazydocker") is not None

    def _get_log_dir(self):
        if os.uname().sysname == "Darwin":
            return os.path.expanduser("~/Library/Caches/lazydocker")
        return os.path.expanduser("~/.cache/lazydocker")

    def check_space(self) -> int:
        return self.get_dir_size(self._get_log_dir())

    def clean(self, dry_run: bool = False) -> CleanResult:
        reclaimed = self.check_space()
        path = self._get_log_dir()
        if not dry_run and os.path.exists(path):
            shutil.rmtree(path, ignore_errors=True)
        return CleanResult(self.name, reclaimed, True)
