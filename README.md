# SuperClean (sclean)

`superclean` is a universal CLI tool to clean development caches and reclaim disk space.

## Installation

```bash
pip install superclean
```

## Usage

```bash
sclean --help
sclean status          # High-level health dashboard
sclean info            # Detailed system resource info
sclean list-cleaners   # Detailed list of all cleaners
sclean all             # Run all cleaners
sclean projects        # Scan local directories for project artifacts (node_modules, etc.)
sclean cron --install  # Set up weekly automated cleanup
sclean -d all          # Dry run mode
sclean docker          # Clean specific tool
```

## Features

- **Global Dry Run**: Use `-d` or `--dry-run` with any command to preview potential savings.
- **Health Dashboard**: `sclean status` gives a visually appealing summary of potential savings.
- **Detailed List**: `sclean list-cleaners` shows exact space used by each tool.
- **Project Scanner**: `sclean projects` recursively finds and deletes heavy local folders like `node_modules`, `venv`, `target`.
- **Automation**: `sclean cron` manages scheduled weekly maintenance.
- **Python**: Clean Python caches (pip, poetry, uv, __pycache__).
- **Node.js**: Clean Node.js caches (npm, yarn, pnpm).
- **Docker**: Clean unused images, containers, and volumes.
- **Nix/NixOS**: Garbage collection and generation cleanup.
- **System**: Temporary file removal.
