import subprocess
import os
import shutil
from ..core import BaseCleaner, CleanResult


class DockerCleaner(BaseCleaner):
    @property
    def name(self) -> str:
        return "docker"

    @property
    def description(self) -> str:
        return "Cleans unused Docker images, containers, and volumes"

    def is_installed(self) -> bool:
        return shutil.which("docker") is not None

    def check_space(self) -> int:
        # Docker doesn't give a simple "potential savings" without running prune -n
        # For simplicity, we'll return 0 or a placeholder, or try to parse 'docker system df'
        output = self.run_command(["docker", "system", "df", "--format", "{{.Size}}"])
        # Parsing this is complex across OS, returning 0 for now as 'unknown'
        return 0

    def clean(self, dry_run: bool = False) -> CleanResult:
        if dry_run:
            return CleanResult(
                self.name, 0, True, "Would run 'docker system prune -af'"
            )

        # Run docker system prune -af --volumes
        process = subprocess.run(
            ["docker", "system", "prune", "-af", "--volumes"],
            capture_output=True,
            text=True,
        )
        if process.returncode == 0:
            return CleanResult(self.name, 0, True, "Docker system pruned successfully")
        return CleanResult(self.name, 0, False, f"Error: {process.stderr}")


class NixCleaner(BaseCleaner):
    @property
    def name(self) -> str:
        return "nix"

    @property
    def description(self) -> str:
        return "Cleans Nix store and NixOS generations"

    def is_installed(self) -> bool:
        return shutil.which("nix-collect-garbage") is not None

    def check_space(self) -> int:
        return 0  # Nix doesn't easily report potential savings without running GC

    def clean(self, dry_run: bool = False) -> CleanResult:
        if dry_run:
            return CleanResult(self.name, 0, True, "Would run 'nix-collect-garbage -d'")

        process = subprocess.run(
            ["nix-collect-garbage", "-d"], capture_output=True, text=True
        )
        if process.returncode == 0:
            return CleanResult(self.name, 0, True, "Nix garbage collected")
        return CleanResult(self.name, 0, False, f"Error: {process.stderr}")
