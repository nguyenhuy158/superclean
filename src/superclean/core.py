import shutil
import os
from abc import ABC, abstractmethod
from typing import List, Optional
import subprocess


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
