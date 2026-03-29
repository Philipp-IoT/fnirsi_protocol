# Developer Setup

## Prerequisites

- Python 3.11 or newer
- [uv](https://docs.astral.sh/uv/) (`pip install uv` or via the install script)
- Git

## Clone and Install

```sh
git clone https://github.com/yourname/fnirsi_ps_control.git
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

## Semantic Versioning

The package version is derived automatically from **git tags** via
[`hatch-vcs`](https://github.com/ofek/hatch-vcs). You never edit a version
string manually. Tags are created automatically by
[`python-semantic-release`](https://python-semantic-release.readthedocs.io/)
in CI based on **Conventional Commit** messages.

### Commit message format

```
<type>[(scope)][!]: <short description>

[optional body]

[optional footer: BREAKING CHANGE: ...]
```

| Commit prefix | SemVer bump |
|---------------|-------------|
| `feat:` | minor (`0.x → 0.x+1`) |
| `fix:`, `perf:` | patch (`0.x.y → 0.x.y+1`) |
| `feat!:` / `BREAKING CHANGE` footer | major (`x → x+1`) |
| `chore:`, `ci:`, `docs:`, `style:`, `test:` | no release |

### How releases happen

1. Merge a PR into `main` with conventional commits.
2. The CI `release` job runs `semantic-release version` which:
   - reads all commits since the last tag
   - determines the next version
   - creates an annotated git tag (`v1.2.3`)
   - generates a CHANGELOG entry
   - creates a GitHub Release
3. The wheel is built with `uv build` (hatch-vcs reads the new tag).
4. The wheel is attached to the GitHub Release via `semantic-release publish`.

### Local version inspection

```sh
uv run python -c "import fnirsi_ps_control; print(fnirsi_ps_control.__version__)"

# Preview what the next release version would be (dry-run):
uv run semantic-release version --print
```
