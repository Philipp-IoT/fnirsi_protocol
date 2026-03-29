# Developer Setup

## Prerequisites

- Python 3.11 or newer
- [uv](https://docs.astral.sh/uv/) (`pip install uv` or via the install script)
- Git

## Clone and Install

```sh
git clone https://gitlab.com/yourname/fnirsi_ps_control.git
cd fnirsi_ps_control

# Install all runtime + dev dependencies into a managed .venv
uv sync --extra dev
```

`uv sync` automatically creates `.venv/` in the project root and installs dependencies
from `uv.lock` (generated on first sync). The lock file is committed to ensure
reproducible builds.

## Running the CLI

```sh
uv run fnirsi --help
```

## Code Quality

```sh
# Format
uv run ruff format src tests

# Lint (auto-fix safe issues)
uv run ruff check --fix src tests

# Type check
uv run mypy

# All tests with coverage
uv run pytest
```

## Adding a Dependency

```sh
# Runtime dependency
uv add pyserial

# Dev-only dependency
uv add --optional dev pytest-asyncio
```

After adding, commit both `pyproject.toml` and `uv.lock`.

## Hardware Access (Linux)

Add your user to the `dialout` group to access serial ports without `sudo`:

```sh
sudo usermod -aG dialout $USER
# Log out and back in for the change to take effect
```

## Kaitai Struct

The binary format specification lives in `docs/protocol/kaitai/fnirsi_dps150.ksy`.

To compile it into Python (optional – useful for unit tests against real captures):

```sh
# Install the Kaitai Struct compiler
# https://kaitai.io/#download
kaitai-struct-compiler --target python \
  --outdir docs/protocol/kaitai/compiled \
  docs/protocol/kaitai/fnirsi_dps150.ksy
```

Compiled output is git-ignored; re-generate as needed.
