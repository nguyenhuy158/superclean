import subprocess
import os
import shutil
from ..core import BaseCleaner, CleanResult


class BrewCleaner(BaseCleaner):
    @property
    def name(self) -> str:
        return "brew"

    @property
    def description(self) -> str:
        return "Cleans old Homebrew versions and cache"

    def is_installed(self) -> bool:
        return shutil.which("brew") is not None

    def check_space(self) -> int:
        return 0  # Brew doesn't easily report potential savings

    def clean(self, dry_run: bool = False) -> CleanResult:
        if dry_run:
            return CleanResult(self.name, 0, True, "Would run 'brew cleanup'")

        process = subprocess.run(["brew", "cleanup"], capture_output=True, text=True)
        if process.returncode == 0:
            return CleanResult(self.name, 0, True, "Homebrew cleaned")
        return CleanResult(self.name, 0, False, f"Error: {process.stderr}")


class XcodeCleaner(BaseCleaner):
    @property
    def name(self) -> str:
        return "xcode"

    @property
    def description(self) -> str:
        return "Cleans Xcode DerivedData and DeviceSupport"

    def is_installed(self) -> bool:
        return os.path.exists(os.path.expanduser("~/Library/Developer/Xcode"))

    def _get_derived_data(self):
        return os.path.expanduser("~/Library/Developer/Xcode/DerivedData")

    def _get_device_support(self):
        return os.path.expanduser("~/Library/Developer/Xcode/iOS DeviceSupport")

    def check_space(self) -> int:
        total = self.get_dir_size(self._get_derived_data())
        total += self.get_dir_size(self._get_device_support())
        return total

    def clean(self, dry_run: bool = False) -> CleanResult:
        reclaimed = self.check_space()
        if not dry_run:
            shutil.rmtree(self._get_derived_data(), ignore_errors=True)
            # Maybe don't delete DeviceSupport entirely as it can be slow to recreate,
            # but usually it's safe if you don't mind redownloading/re-indexing.
            # Let's just do DerivedData for now to be safe, or both.
            shutil.rmtree(self._get_device_support(), ignore_errors=True)
        return CleanResult(self.name, reclaimed, True)


class CargoCleaner(BaseCleaner):
    @property
    def name(self) -> str:
        return "cargo"

    @property
    def description(self) -> str:
        return "Cleans Cargo registry and git caches"

    def is_installed(self) -> bool:
        return os.path.exists(os.path.expanduser("~/.cargo"))

    def _get_registry(self):
        return os.path.expanduser("~/.cargo/registry")

    def _get_git_cache(self):
        return os.path.expanduser("~/.cargo/git")

    def check_space(self) -> int:
        total = self.get_dir_size(self._get_registry())
        total += self.get_dir_size(self._get_git_cache())
        return total

    def clean(self, dry_run: bool = False) -> CleanResult:
        reclaimed = self.check_space()
        if not dry_run:
            shutil.rmtree(self._get_registry(), ignore_errors=True)
            shutil.rmtree(self._get_git_cache(), ignore_errors=True)
        return CleanResult(self.name, reclaimed, True)


class CondaCleaner(BaseCleaner):
    @property
    def name(self) -> str:
        return "conda"

    @property
    def description(self) -> str:
        return "Cleans Conda packages and caches"

    def is_installed(self) -> bool:
        return shutil.which("conda") is not None

    def check_space(self) -> int:
        return 0

    def clean(self, dry_run: bool = False) -> CleanResult:
        if dry_run:
            return CleanResult(self.name, 0, True, "Would run 'conda clean --all -y'")

        process = subprocess.run(
            ["conda", "clean", "--all", "-y"], capture_output=True, text=True
        )
        if process.returncode == 0:
            return CleanResult(self.name, 0, True, "Conda cleaned")
        return CleanResult(self.name, 0, False, f"Error: {process.stderr}")
