# fnirsi-ps-control

> PC control library &amp; CLI for the **FNIRSI DPS-150** regulated power supply via USB CDC (virtual COM port).

[![CI](https://github.com/yourname/fnirsi_ps_control/actions/workflows/ci.yml/badge.svg)](https://github.com/yourname/fnirsi_ps_control/actions/workflows/ci.yml)
[![Coverage](https://img.shields.io/badge/coverage-see_CI-brightgreen)](https://github.com/yourname/fnirsi_ps_control/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/)
[![GitHub release](https://img.shields.io/github/v/release/yourname/fnirsi_ps_control)](https://github.com/yourname/fnirsi_ps_control/releases)

---

## Features

- [ ] Set output voltage and current limit
- [ ] Read back measured voltage, current and power
- [ ] Enable / disable output
- [ ] Persistent preset management
- [ ] Rich terminal UI (CLI)
- [ ] Async-capable Python API

---

## Hardware

| Item | Detail |
|------|--------|
| Device | FNIRSI DPS-150 |
| Interface | USB CDC (appears as `/dev/ttyACM*` on Linux, `COMx` on Windows) |
| Baud rate | TBD (see [protocol docs](docs/protocol/README.md)) |
| USB VID/PID | TBD |

---

## Quick Start

### Prerequisites

- Python ≥ 3.11
- [uv](https://docs.astral.sh/uv/) – `pip install uv` or `curl -Lsf https://astral.sh/uv/install.sh | sh`

### Install

```sh
# Clone
git clone https://gitlab.com/yourname/fnirsi_ps_control.git
cd fnirsi_ps_control

# Create venv and install all dependencies (including dev extras)
uv sync --extra dev
```

### Run the CLI

```sh
uv run fnirsi --help
uv run fnirsi info --port /dev/ttyACM0
uv run fnirsi set-voltage --port /dev/ttyACM0 12.0
```

---

## Development

```sh
# Lint &amp; format
uv run ruff check src tests
uv run ruff format src tests

# Type check
uv run mypy

# Tests
uv run pytest
```

See [docs/dev/setup.md](docs/dev/setup.md) for a full guide.

---

## Protocol Reverse Engineering

The serial protocol was determined by capturing USB traffic with Wireshark / `usbmon` and analysing the byte patterns.

- Protocol overview: [docs/protocol/README.md](docs/protocol/README.md)
- Frame format: [docs/protocol/framing.md](docs/protocol/framing.md)
- Command catalogue: [docs/protocol/commands.md](docs/protocol/commands.md)
- Machine-readable spec: [docs/protocol/kaitai/fnirsi_dps150.ksy](docs/protocol/kaitai/fnirsi_dps150.ksy) (Kaitai Struct)

---

## License

[MIT](LICENSE) © 2026 Your Name
