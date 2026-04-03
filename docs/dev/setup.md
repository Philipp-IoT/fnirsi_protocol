# Developer Setup

## Prerequisites

- Python ≥ 3.11
- [uv](https://docs.astral.sh/uv/) — `pip install uv`
- (Optional) `kaitai-struct-compiler` 0.10 — for regenerating `protocol/generated/`

## Install

```sh
git clone https://github.com/pb-/fnirsi_ps_control.git
cd fnirsi_ps_control
uv sync --extra dev --extra docs
```

## Common Tasks

```sh
# Lint and format
uv run ruff format src tests
uv run ruff check --fix src tests

# Type check
uv run mypy

# Tests
uv run pytest

# Build docs locally
uv run mkdocs serve

# Regenerate Kaitai Python parser (requires ksc on PATH)
bash scripts/gen_kaitai.sh

# Regenerate protocol reference Markdown
uv run python scripts/ksy_to_md.py \
    --ksy protocol/fnirsi_dps150.ksy \
    --out docs/protocol/reference.md
```

## Installing kaitai-struct-compiler

```sh
# Linux (snap)
snap install kaitai-struct-compiler

# Manual (any OS)
wget https://github.com/kaitai-io/kaitai_struct_compiler/releases/download/0.10/kaitai-struct-compiler-0.10.zip
unzip kaitai-struct-compiler-0.10.zip
# Add kaitai-struct-compiler-0.10/bin to PATH
```

## Workflow: Adding a New Command

1. Capture USB traffic with Wireshark (see [RE Methodology](../re_methodology.md))
2. Update `protocol/fnirsi_dps150.ksy` (the single source of truth)
3. Run `bash scripts/gen_kaitai.sh` to regenerate the Python parser
4. Run `uv run python scripts/ksy_to_md.py ...` to regenerate the reference
5. Update `src/fnirsi_ps_control/protocol.py` TX encoders if needed
6. Add byte-exact test in `tests/test_protocol.py`
7. Commit with a conventional commit message (see [Contributing](contributing.md))
