"""Default cleaner registration.

Kept separate from `core.py` so that `core.py` stays free of imports from the
`cleaners` package (those modules import `core`, so `core` importing them back
would be circular).
"""

from .cleaners.dev_tools import BrewCleaner, CargoCleaner, CondaCleaner, XcodeCleaner
from .cleaners.docker_nix import DockerCleaner, NixCleaner
from .cleaners.python_node import NodeCleaner, PythonCleaner
from .cleaners.system import SystemCleaner
from .cleaners.utilities import LazyDockerCleaner, LazyGitCleaner
from .core import CleanerRegistry


def build_registry() -> CleanerRegistry:
    """Construct the registry of all known cleaners (filtered to installed tools)."""
    registry = CleanerRegistry()
    registry.register(PythonCleaner())
    registry.register(NodeCleaner())
    registry.register(DockerCleaner())
    registry.register(NixCleaner())
    registry.register(SystemCleaner())
    registry.register(BrewCleaner())
    registry.register(XcodeCleaner())
    registry.register(CargoCleaner())
    registry.register(CondaCleaner())
    registry.register(LazyGitCleaner())
    registry.register(LazyDockerCleaner())
    return registry
