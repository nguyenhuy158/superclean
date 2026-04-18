.PHONY: help run build patch minor major pub test lint

VERSION := $(shell cat VERSION)

help:
	@echo "Available commands:"
	@echo "  make run      - Run sclean locally"
	@echo "  make build    - Build the package"
	@echo "  make patch    - Bump version (patch) and tag"
	@echo "  make minor    - Bump version (minor) and tag"
	@echo "  make major    - Bump version (major) and tag"
	@echo "  make pub      - Build and publish to PyPI"
	@echo "  make test     - Run tests"
	@echo "  make lint     - Run linter (ruff)"

run:
	PYTHONPATH=src python3 -m superclean.main

build:
	python3 -m build

patch:
	@python3 -c "v = '$(VERSION)'.split('.'); v[2] = str(int(v[2]) + 1); print('.'.join(v))" > VERSION
	@sed -i '' 's/version = "$(VERSION)"/version = "'$$(cat VERSION)'"/' pyproject.toml
	@sed -i '' 's/__version__ = "$(VERSION)"/__version__ = "'$$(cat VERSION)'"/' src/superclean/__init__.py
	@git add VERSION pyproject.toml src/superclean/__init__.py
	@git commit -m "chore: bump version to $$(cat VERSION)"
	@git tag v$$(cat VERSION)

minor:
	@python3 -c "v = '$(VERSION)'.split('.'); v[1] = str(int(v[1]) + 1); v[2] = '0'; print('.'.join(v))" > VERSION
	@sed -i '' 's/version = "$(VERSION)"/version = "'$$(cat VERSION)'"/' pyproject.toml
	@sed -i '' 's/__version__ = "$(VERSION)"/__version__ = "'$$(cat VERSION)'"/' src/superclean/__init__.py
	@git add VERSION pyproject.toml src/superclean/__init__.py
	@git commit -m "chore: bump version to $$(cat VERSION)"
	@git tag v$$(cat VERSION)

major:
	@python3 -c "v = '$(VERSION)'.split('.'); v[0] = str(int(v[0]) + 1); v[1] = '0'; v[2] = '0'; print('.'.join(v))" > VERSION
	@sed -i '' 's/version = "$(VERSION)"/version = "'$$(cat VERSION)'"/' pyproject.toml
	@sed -i '' 's/__version__ = "$(VERSION)"/__version__ = "'$$(cat VERSION)'"/' src/superclean/__init__.py
	@git add VERSION pyproject.toml src/superclean/__init__.py
	@git commit -m "chore: bump version to $$(cat VERSION)"
	@git tag v$$(cat VERSION)

pub: build
	python3 -m twine upload dist/*

test:
	PYTHONPATH=src python3 -m pytest

lint:
	ruff check .
