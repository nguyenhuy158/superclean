# SuperClean (sclean)

`superclean` is a universal CLI tool to clean development caches and reclaim disk space.

## Installation

```bash
pip install superclean
```

## Usage

```bash
sclean --help
sclean list
sclean all
sclean docker
```

## Features

- Clean Python caches (pip, poetry, uv, __pycache__)
- Clean Node.js caches (npm, yarn, pnpm)
- Clean Docker resources
- Clean Nix/NixOS garbage
- Clean System temp files
