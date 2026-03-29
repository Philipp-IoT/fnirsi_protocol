# GitHub Copilot – Repository Instructions

> These instructions are loaded automatically by GitHub Copilot and every
> AI agent working in this repository.  Keep them up to date whenever the
> toolchain, protocol findings, or architecture change.

---

## 1. Project Summary

**fnirsi-ps-control** is a Python library + CLI for controlling the
FNIRSI DPS-150 regulated power supply (150 W, 30 V / 5.1 A) over USB CDC
(virtual COM port).

| Layer | Location |
|---|---|
| Protocol encode/decode | `src/fnirsi_ps_control/protocol.py` |
| Serial transport | `src/fnirsi_ps_control/connection.py` |
| High-level device API | `src/fnirsi_ps_control/device.py` |
| CLI (Typer + Rich) | `src/fnirsi_ps_control/cli.py` |
| Unit tests | `tests/` |
| Protocol RE docs | `docs/protocol/` |
| Developer docs | `docs/dev/` |

---

## 2. Python Environment – uv

This project uses **[uv](https://docs.astral.sh/uv/)** for all environment
and package management.  Do **not** use plain `pip`, `venv`, or `poetry`.

### First-time setup

```sh
# Creates .venv/ and installs all runtime + dev deps from uv.lock
uv sync --extra dev
```

### Activate the environment (optional – uv run handles it automatically)

```sh
source .venv/bin/activate
```

### Run any command inside the managed environment

```sh
uv run <command>          # preferred – no manual activation needed
.venv/bin/python <script> # alternative direct invocation
```

### Add / remove dependencies

```sh
# Runtime dependency
uv add pyserial

# Dev-only dependency  (goes into [project.optional-dependencies] dev = [...])
uv add --optional dev pytest-asyncio

# Remove
uv remove somepackage
```

Always commit both `pyproject.toml` **and** `uv.lock` after any dependency change.

### Upgrade all packages

```sh
uv sync --upgrade --extra dev
```

---

## 3. Running Tests

```sh
# Full test suite with coverage report
uv run pytest

# Single file or test
uv run pytest tests/test_protocol.py -v
uv run pytest tests/test_protocol.py::TestFrameEncode::test_connect_frame_bytes -v

# Without coverage (faster feedback loop)
uv run pytest --no-cov

# Stop on first failure
uv run pytest -x
```

Tests live in `tests/`.  Coverage is reported automatically (configured in
`pyproject.toml` `[tool.pytest.ini_options]`).  Target: all protocol encode /
decode tests pass with byte-exact assertions derived from real captures.

---

## 4. Code Quality

```sh
# Auto-format
uv run ruff format src tests

# Lint (apply safe auto-fixes)
uv run ruff check --fix src tests

# Type-check (strict mypy)
uv run mypy

# Run everything in one shot
uv run ruff format src tests && uv run ruff check --fix src tests && uv run mypy && uv run pytest
```

Settings live in `pyproject.toml` under `[tool.ruff]` and `[tool.mypy]`.
The CI pipeline (`lint` job in `.github/workflows/ci.yml`) runs the same
checks non-interactively.

---

## 5. CLI – Interacting with the Device

The entry-point is `fnirsi` (registered in `pyproject.toml` `[project.scripts]`).

```sh
# Show help
uv run fnirsi --help

# Query device status
uv run fnirsi info --port /dev/ttyACM0

# Set voltage (float, in volts)
uv run fnirsi set-voltage --port /dev/ttyACM0 10.0

# Set current limit (float, in amps)
uv run fnirsi set-current --port /dev/ttyACM0 1.0

# Enable / disable output
uv run fnirsi output --port /dev/ttyACM0 on
uv run fnirsi output --port /dev/ttyACM0 off
```

Default baud rate: **115200**.  The device appears as `/dev/ttyACM0` on Linux
(USB CDC ACM).  On Windows: `COMx`.

### Linux serial port permissions

```sh
sudo usermod -aG dialout $USER   # then log out and back in
```

### Library API (Python)

```python
from fnirsi_ps_control.device import DPS150

with DPS150("/dev/ttyACM0") as ps:
    ps.set_voltage(12.0)     # volts (float)
    ps.set_current(1.0)      # amps (float)
    ps.enable_output()
    status = ps.get_status()
    print(status.vout, status.iout)
```

---

## 6. Protocol Layer Quick Reference

**Confirmed 2026-03-29** from capture
`docs/protocol/captures/dps150_connect_set_10v_set_1A_disconnect.txt`.

### Frame format

```
[START:1] [CMD:1] [LEN:1] [DATA:LEN] [CHKSUM:1]
```

- No stop byte.
- `CHKSUM = (CMD + LEN + Σ DATA bytes) mod 256`
- All voltage/current values: **IEEE 754 32-bit little-endian float** in SI units (V / A).

### START byte values

| Byte | Meaning |
|------|---------|
| `0xa1` | Query from host **or** any device response |
| `0xb1` | Write / set command from host |
| `0xc1` | Connect / disconnect control |

### Confirmed command IDs

| CMD | START | Direction | Description |
|-----|-------|-----------|-------------|
| `0x00` | `0xc1` | TX | Connect (data=`01`) / Disconnect (data=`00`) |
| `0xc0` | `0xa1` | RX push | Vin channel A [V] float32 |
| `0xc1` | `0xb1` | TX | SET_VOLTAGE float32 [V] |
| `0xc2` | `0xb1` | TX | SET_CURRENT float32 [A] |
| `0xc3` | `0xa1` | RX push | Output meas: Vout, Iout, ? (3×float32) |
| `0xc4` | `0xa1` | RX push | Vin channel B/boost [V] float32 |
| `0xde` | `0xa1` | RX | Device name ASCII ("DPS-150") |
| `0xdf` | `0xa1` | RX | Firmware version ASCII |
| `0xe0` | `0xa1` | RX | Hardware version ASCII |
| `0xe1` | `0xa1` | RX | Ready status uint8 (1=ready) |
| `0xe2` | `0xa1` | RX push | Alt Vin [V] float32 |
| `0xe3` | `0xa1` | RX push | MAX_CURRENT constant 5.1 A float32 |
| `0xff` | `0xa1` | RX | Full status blob (139 bytes) |

Full command catalogue: `docs/protocol/commands.md`
Frame format details: `docs/protocol/framing.md`
Kaitai Struct spec: `docs/protocol/kaitai/fnirsi_dps150.ksy`

---

## 7. Protocol RE Workflow (adding new commands)

1. Capture USB traffic with Wireshark while performing the action on the device.
   Export as **"C Arrays"** (plain hex) and save to
   `docs/protocol/captures/<descriptive_name>.txt`.
2. Decode frames using the Python snippet pattern from prior captures
   (see existing annotated `.txt` files).
3. Verify every checksum: `(CMD + LEN + Σ data) % 256`.
4. Update `docs/protocol/commands.md` with the new CMD, citing the capture file.
5. Update `docs/protocol/kaitai/fnirsi_dps150.ksy` (enum + payload type).
6. Add/update `src/fnirsi_ps_control/protocol.py` (`Cmd` class + helper function).
7. Write a byte-exact unit test in `tests/test_protocol.py`.
8. Commit using conventional commit: `docs(protocol): ...` or `feat(protocol): ...`.

---

## 8. Building Protocol Documentation

There is no static site generator configured yet.  Docs are plain Markdown +
one Kaitai Struct file.

### Render Kaitai Struct spec

```sh
# Install kaitai-struct-compiler: https://kaitai.io/#download
kaitai-struct-compiler --target python \
  --outdir docs/protocol/kaitai/compiled \
  docs/protocol/kaitai/fnirsi_dps150.ksy
```

Compiled output is `.gitignore`d; re-generate whenever the `.ksy` changes.

### Preview Markdown locally

Any Markdown viewer works (VS Code built-in preview, `grip`, `mdcat`, etc.).

### Future: add MkDocs

If a static site is desired:
```sh
uv add --optional dev mkdocs mkdocs-material
uv run mkdocs serve     # local preview at http://127.0.0.1:8000
uv run mkdocs build     # outputs to site/
```

---

## 9. Versioning & Releases

Versions come **exclusively from annotated git tags** – no version string
lives in the source tree.  `hatch-vcs` reads the tag at build time.

```sh
# The release job in CI handles tagging automatically via PSR.
# To trigger manually (dry-run):
uv run semantic-release version --no-commit --no-tag --no-push

# What would be the next version?
uv run semantic-release version --print
```

Commit messages must follow **Conventional Commits**:

| Prefix | SemVer bump |
|--------|-------------|
| `feat:` | minor |
| `fix:`, `perf:` | patch |
| `BREAKING CHANGE` / `!` | major |
| `docs:`, `chore:`, `test:`, `ci:` | no bump |

---

## 10. Known Issues / Tech Debt

| File | Issue |
|------|-------|
| `src/fnirsi_ps_control/device.py` | Still uses old `millivolts`/`milliamps` integer API – must be updated to float V/A to match confirmed protocol |
| `src/fnirsi_ps_control/cli.py` | Status display still references `.voltage_set_mv` etc. – needs updating once `device.py` is fixed |
| `docs/protocol/commands.md` offsets 96–138 | Status blob tail layout still TBD – needs another capture with output enabled |
| CMD `0xb0` | One anomalous packet in capture; checksum doesn't verify – needs investigation |
