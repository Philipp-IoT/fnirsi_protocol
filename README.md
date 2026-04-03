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
| Device | FNIRSI DPS-150 (150 W, 30 V / 5.1 A) |
| MCU | Artery AT32 |
| Interface | USB CDC ACM (appears as `/dev/ttyACM*` on Linux, `COMx` on Windows) |
| Baud rate | **9600** 8N1 |
| USB VID/PID | `2e3c:5740` (Artery AT32 Virtual Com Port) |
| Serial line state | DTR=off, RTS=on |

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

The serial protocol was determined by capturing USB traffic with Wireshark / USBPcap and analysing the byte patterns.

- Protocol overview: [docs/protocol/README.md](docs/protocol/README.md)
- Protocol specification: [docs/protocol/spec.md](docs/protocol/spec.md)
- Kaitai Struct spec (single source of truth): [docs/protocol/kaitai/fnirsi_dps150.ksy](docs/protocol/kaitai/fnirsi_dps150.ksy)

---

## License

[MIT](LICENSE) © 2026 Your Name
