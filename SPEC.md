# SuperClean (sclean) Specification

## Overview
`superclean` is a CLI tool designed to be a "one-stop shop" for cleaning development caches and temporary files across various platforms and applications. It aims to reclaim disk space efficiently and safely.

## Key Features
- **Centralized Cleaning**: Unified command to clean multiple application caches.
- **Extensible Architecture**: Easy to add new "Cleaners" for different tools.
- **Safety First**: Dry-run mode to see what will be deleted before actual execution.
- **Beautiful CLI**: Using `rich` for progress bars and formatted output.
- **Interactive Mode**: Selectively clean specific apps.

## Target Applications (Cleaners)
- **Python**: pip cache, poetry cache, uv cache, pyenv versions (optional), `__pycache__` directories.
- **JavaScript/Node**: npm cache, yarn cache, pnpm cache.
- **Docker**: Unused images, containers, and volumes.
- **Package Managers**: Homebrew cleanup, apt-get clean, nix store cleanup (`nix-collect-garbage`), nixos generation cleanup.
- **System**: Temp directories, log files.

## Proposed Command Structure
- `sclean`: Show help (default behavior).
- `sclean all`: Clean everything with confirmation.

- `sclean list`: List available cleaners and their status (e.g., how much space they are taking).
- `sclean <app>`: Clean a specific app (e.g., `sclean pip`).
- `sclean --dry-run`: Show what would be deleted.
- `sclean --force`: Skip confirmation.

## Project Management
A `Makefile` will be provided to streamline development and release tasks.

### Makefile Commands
- `make help`: Show available commands.
- `make run`: Run the tool locally for testing.
- `make build`: Build the package for distribution.
- `make patch`: Increment patch version and tag.
- `make minor`: Increment minor version and tag.
- `make major`: Increment major version and tag.
- `make pub`: Build and publish to PyPI.
- `make test`: Run unit tests.
- `make lint`: Run linters (ruff).

## Project Structure
```text
superclean/
├── src/
│   └── superclean/
│       ├── __init__.py
│       ├── main.py        # CLI entry point
│       ├── core.py        # Base classes and orchestration
│       └── cleaners/      # Implementation of specific cleaners
│           ├── __init__.py
│           ├── python.py
│           ├── node.py
│           ├── docker.py
│           └── system.py
├── tests/
├── pyproject.toml
├── Makefile
├── VERSION
└── README.md
```
