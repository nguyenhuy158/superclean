import math
import shutil
import os
from abc import ABC, abstractmethod
from typing import List, Optional, Tuple
import subprocess


def format_size(size_bytes: int) -> str:
    """Format a byte count as a human-readable string (e.g. '1.23 GB')."""
    if size_bytes == 0:
        return "0 B"
    size_name = ("B", "KB", "MB", "GB", "TB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_name[i]}"


class CleanResult:
    def __init__(
        self, name: str, space_reclaimed: int, success: bool, message: str = ""
    ):
        self.name = name
        self.space_reclaimed = space_reclaimed
        self.success = success
        self.message = message


class BaseCleaner(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def category(self) -> str:
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        pass

    @abstractmethod
    def check_space(self) -> int:
        """Returns potential space to reclaim in bytes."""
        pass

    @abstractmethod
    def clean(self, dry_run: bool = False) -> CleanResult:
        """Performs the cleaning operation."""
        pass

    def is_installed(self) -> bool:
        """Checks if the tool associated with this cleaner is installed."""
        return True

    def get_cache_paths(self) -> List[Tuple[str, str]]:
        """Labeled (label, path) pairs this cleaner manages as concrete on-disk paths.

        Used by path-level UIs (e.g. the TUI dashboard) that display and
        selectively delete individual cache locations, as opposed to cleaning
        everything a cleaner owns at once via `clean()`. Cleaners driven by
        external commands with no deterministic path (docker, nix, brew,
        conda) return an empty list.
        """
        return []

    def get_dir_size(self, path: str) -> int:
        """Helper to calculate directory size."""
        total = 0
        if not os.path.exists(path):
            return 0
        try:
            for entry in os.scandir(path):
                if entry.is_file():
                    total += entry.stat().st_size
                elif entry.is_dir():
                    total += self.get_dir_size(entry.path)
        except (PermissionError, OSError):
            pass
        return total

    def run_command(self, cmd: List[str]) -> Optional[str]:
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            if result.returncode == 0:
                return result.stdout.strip()
        except FileNotFoundError:
            pass
        return None


class CleanerRegistry:
    def __init__(self):
        self.cleaners: List[BaseCleaner] = []

    def register(self, cleaner: BaseCleaner):
        if cleaner.is_installed():
            self.cleaners.append(cleaner)

    def get_all(self) -> List[BaseCleaner]:
        return self.cleaners

    def get_by_name(self, name: str) -> Optional[BaseCleaner]:
        for c in self.cleaners:
            if c.name.lower() == name.lower():
                return c
        return None


class CacheTarget:
    """A single on-disk cache location discovered by a cleaner.

    Used by path-level UIs (e.g. the TUI dashboard) that need to display and
    selectively delete individual cache locations, as opposed to cleaning an
    entire cleaner's caches at once via `BaseCleaner.clean()`.
    """

    def __init__(self, cleaner: str, label: str, path: str, size: int):
        self.cleaner = cleaner
        self.label = label
        self.path = path
        self.size = size


def scan_cache_targets(registry: CleanerRegistry) -> List[CacheTarget]:
    """Scan all registered cleaners for concrete on-disk cache paths and compute sizes.

    This walks the filesystem (via `BaseCleaner.get_dir_size`) and can be slow;
    callers on a UI thread should run it in a background worker. Returns targets
    sorted by size, largest first. Cleaners with no deterministic path (e.g.
    those driven by external commands like docker/nix/brew/conda) contribute
    nothing, since `get_cache_paths()` defaults to an empty list.
    """
    targets: List[CacheTarget] = []
    for cleaner in registry.get_all():
        for label, path in cleaner.get_cache_paths():
            if not path or not os.path.isdir(path):
                continue
            size = cleaner.get_dir_size(path)
            if size <= 0:
                continue
            targets.append(CacheTarget(cleaner.name, label, path, size))
    targets.sort(key=lambda t: t.size, reverse=True)
    return targets


def delete_cache_target(target: CacheTarget, dry_run: bool = False) -> int:
    """Delete a single cache target's directory. Returns bytes freed (0 on dry run)."""
    if dry_run:
        return target.size
    if os.path.isdir(target.path):
        shutil.rmtree(target.path, ignore_errors=True)
    return target.size
