# SuperClean (sclean)

`superclean` is a universal CLI tool to clean development caches and reclaim disk space.

## Installation

```bash
pip install superclean
```

## Usage

```bash
sclean --help
sclean list-cleaners
sclean all
sclean -d all   # Dry run mode
sclean docker
```

## Features

- **Global Dry Run**: Use `-d` or `--dry-run` with any command to preview potential savings.
- **Detailed List**: `sclean list-cleaners` shows exact space used by each tool.
- **Python**: Clean Python caches (pip, poetry, uv, __pycache__).
- **Node.js**: Clean Node.js caches (npm, yarn, pnpm).
- **Docker**: Clean unused images, containers, and volumes.
- **Nix/NixOS**: Garbage collection and generation cleanup.
- **System**: Temporary file removal.
