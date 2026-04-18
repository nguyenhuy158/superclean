import subprocess
import os
import shutil
from ..core import BaseCleaner, CleanResult


class DockerCleaner(BaseCleaner):
    @property
    def name(self) -> str:
        return "docker"

    @property
    def category(self) -> str:
        return "Containers"

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
    def category(self) -> str:
        return "Tools"

    @property
    def description(self) -> str:
        return "Cleans Nix store and NixOS generations"

    def is_installed(self) -> bool:
        return shutil.which("nix-collect-garbage") is not None

    def check_space(self) -> int:
        return 0  # Nix doesn't easily report potential savings without running GC

    def clean(self, dry_run: bool = False) -> CleanResult:
        if dry_run:
            return CleanResult(
                self.name, 0, True, "Would run Nix GC, Profile wipe, and HM expire"
            )

        msgs = []
        # 1. Nix GC
        process = subprocess.run(
            ["nix-collect-garbage", "-d"], capture_output=True, text=True
        )
        if process.returncode == 0:
            msgs.append("Nix garbage collected")

        # 2. Nix Profile wipe
        if shutil.which("nix"):
            subprocess.run(
                ["nix", "profile", "wipe-generations"], capture_output=True, text=True
            )
            msgs.append("Nix profiles wiped")

        # 3. Home-manager expire
        if shutil.which("home-manager"):
            subprocess.run(
                ["home-manager", "expire-generations", "0"],
                capture_output=True,
                text=True,
            )
            msgs.append("Home-manager generations expired")

        # 4. Nix store optimise
        if shutil.which("nix-store"):
            subprocess.run(["nix-store", "--optimise"], capture_output=True, text=True)
            msgs.append("Nix store optimised")

        return CleanResult(self.name, 0, True, ". ".join(msgs))
