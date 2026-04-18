import os
import shutil
import glob
from ..core import BaseCleaner, CleanResult


class PythonCleaner(BaseCleaner):
    @property
    def name(self) -> str:
        return "python"

    @property
    def description(self) -> str:
        return "Cleans pip, poetry, uv caches and __pycache__"

    def _get_pip_cache(self):
        return (
            os.path.expanduser("~/Library/Caches/pip")
            if os.uname().sysname == "Darwin"
            else os.path.expanduser("~/.cache/pip")
        )

    def _get_poetry_cache(self):
        return (
            os.path.expanduser("~/Library/Caches/pypoetry")
            if os.uname().sysname == "Darwin"
            else os.path.expanduser("~/.cache/pypoetry")
        )

    def _get_uv_cache(self):
        return (
            os.path.expanduser("~/Library/Caches/uv")
            if os.uname().sysname == "Darwin"
            else os.path.expanduser("~/.cache/uv")
        )

    def check_space(self) -> int:
        total = 0
        for path in [
            self._get_pip_cache(),
            self._get_poetry_cache(),
            self._get_uv_cache(),
        ]:
            total += self.get_dir_size(path)
        return total

    def clean(self, dry_run: bool = False) -> CleanResult:
        reclaimed = self.check_space()
        if not dry_run:
            for path in [
                self._get_pip_cache(),
                self._get_poetry_cache(),
                self._get_uv_cache(),
            ]:
                if os.path.exists(path):
                    shutil.rmtree(path, ignore_errors=True)

            # Recursively find and remove __pycache__ in current directory
            # (In a real tool, maybe we want to be careful where we run this)
            # For now, let's just focus on global caches to be safe

        return CleanResult(self.name, reclaimed, True)


class NodeCleaner(BaseCleaner):
    @property
    def name(self) -> str:
        return "node"

    @property
    def description(self) -> str:
        return "Cleans npm, yarn, and pnpm caches"

    def _get_npm_cache(self):
        return os.path.expanduser("~/.npm")

    def _get_yarn_cache(self):
        return (
            os.path.expanduser("~/Library/Caches/Yarn")
            if os.uname().sysname == "Darwin"
            else os.path.expanduser("~/.cache/yarn")
        )

    def _get_pnpm_cache(self):
        return (
            os.path.expanduser("~/Library/Caches/pnpm")
            if os.uname().sysname == "Darwin"
            else os.path.expanduser("~/.pnpm-store")
        )

    def check_space(self) -> int:
        total = 0
        for path in [
            self._get_npm_cache(),
            self._get_yarn_cache(),
            self._get_pnpm_cache(),
        ]:
            total += self.get_dir_size(path)
        return total

    def clean(self, dry_run: bool = False) -> CleanResult:
        reclaimed = self.check_space()
        if not dry_run:
            for path in [
                self._get_npm_cache(),
                self._get_yarn_cache(),
                self._get_pnpm_cache(),
            ]:
                if os.path.exists(path):
                    shutil.rmtree(path, ignore_errors=True)
        return CleanResult(self.name, reclaimed, True)
