# FNIRSI DPS-150 Protocol

Reverse engineering of the serial protocol used by the **FNIRSI DPS-150** regulated power supply, with a Python CLI demo.

## Hardware

| Item | Detail |
|------|--------|
| Device | FNIRSI DPS-150 (150 W, 30 V / 5.1 A) |
| MCU | Artery AT32 |
| Interface | USB CDC ACM (`/dev/ttyACM*` on Linux, `COMx` on Windows) |
| USB IDs | VID `0x2e3c` / PID `0x5740` (Artery AT32 Virtual Com Port) |
| Baud rate | 9600, 8N1 |
| Serial line state | DTR=off, RTS=on |

## Wire Format

```
[DIR:1] [START:1] [CMD:1] [LEN:1] [DATA×LEN] [CHKSUM:1]

DIR    : 0xf1 host→device  |  0xf0 device→host
START  : 0xa1 query/response  |  0xb1 write cmd  |  0xc1 connect/disconnect
CHKSUM : (CMD + LEN + Σ DATA) mod 256
```

Full protocol: [Specification](protocol/spec.md) · [Reference](protocol/reference.md) · [Session Lifecycle](protocol/session.md)

## Status

Core protocol **confirmed** from USB captures and live hardware test (2026-03-29).

| Area | Status |
|------|--------|
| Frame format (DIR + START + CMD + LEN + DATA + CHKSUM) | Confirmed |
| All 14 command IDs | Confirmed |
| Voltage / current set (float32 LE) | Confirmed |
| Output enable/disable (CMD 0xdb) | Confirmed |
| Periodic push stream (PUSH_OUTPUT, PUSH_VIN_*) | Confirmed |
| Full status blob layout (offsets 0–95) | Confirmed |
| Full status blob tail (offsets 96–138) | TBD |

## Python Quick Start

```sh
git clone https://github.com/pb-/fnirsi_ps_control.git
cd fnirsi_ps_control
uv sync --extra dev
uv run fnirsi --help
uv run fnirsi info --port /dev/ttyACM0
```

## Project Structure

```
protocol/
├── fnirsi_dps150.ksy     ← Kaitai Struct spec (SINGLE SOURCE OF TRUTH)
├── captures/             ← Raw USB capture logs
└── generated/
    └── fnirsi_dps150.py  ← Kaitai-generated Python parser (committed baseline)

scripts/
├── gen_kaitai.sh         ← regenerate protocol/generated/ from .ksy
└── ksy_to_md.py          ← regenerate docs/protocol/reference.md from .ksy

src/fnirsi_ps_control/    ← Python library and CLI
```
