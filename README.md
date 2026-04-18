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
sclean explore         # Interactive disk usage explorer (ncdu-like)
sclean check           # Check for useful developer tools
sclean list-cleaners   # Detailed list of all cleaners
sclean all             # Run all cleaners
sclean all -i          # Interactive selection of what to clean
sclean all --min-size 1GB # Only clean large caches
sclean projects        # Scan local directories for project artifacts (node_modules, etc.)
sclean cron --install  # Set up weekly automated cleanup
sclean -d all          # Dry run mode
sclean docker          # Clean specific tool
```

## Features

- **Global Dry Run**: Use `-d` or `--dry-run` with any command to preview potential savings.
- **Health Dashboard**: `sclean status` gives a visually appealing summary of potential savings.
- **Interactive Mode**: Use `sclean all -i` to selectively clean specific caches using a TUI menu.
- **Smart Thresholds**: Filter cleanups by size using `--min-size` to focus on the biggest wins.
- **Detailed Info**: `sclean info` shows comprehensive system resource usage.
- **Project Scanner**: `sclean projects` recursively finds and deletes heavy local folders like `node_modules`, `venv`, `target`. **Optimized with `fd`** if installed.
- **Automation**: `sclean cron` manages scheduled weekly maintenance.
- **Python**: Clean Python caches (pip, poetry, uv, __pycache__).
- **Node.js**: Clean Node.js caches (npm, yarn, pnpm).
- **Docker**: Clean unused images, containers, and volumes.
- **Nix/NixOS**: Garbage collection and generation cleanup.
- **System**: Temporary file removal.
