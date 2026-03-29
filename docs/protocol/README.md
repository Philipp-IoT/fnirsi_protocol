# Protocol Reverse Engineering – Overview

> **Status:** Core protocol CONFIRMED against live hardware (2026-03-29).
> Values marked _TBD_ are still working hypotheses.

---

## Device

| Item | Value |
|------|-------|
| Model | FNIRSI DPS-150 |
| MCU | Artery AT32 |
| Interface | USB CDC / ACM (virtual COM port) |
| USB VID | `0x2e3c` (Artery) |
| USB PID | `0x5740` (AT32 Virtual Com Port) |
| Baud rate | **9600** |
| Data bits | 8 |
| Stop bits | 1 |
| Parity | None |
| Flow control | None |
| Serial line state | DTR=off, RTS=on |

---

## RE Methodology

See [methodology.md](../re_methodology.md) for the step-by-step capture workflow.

---

## Documents

| Document | Contents |
|----------|----------|
| [framing.md](framing.md) | Frame structure, start/stop bytes, checksum |
| [commands.md](commands.md) | Command catalogue with request/response layout |
| [kaitai/fnirsi_dps150.ksy](kaitai/fnirsi_dps150.ksy) | Kaitai Struct machine-readable spec |
| [captures/](captures/) | Raw capture log files (binary excluded via .gitignore) |

---

## Quick-Start Capture Workflow

```sh
# 1. Identify port
dmesg | grep ttyACM

# 2. On Windows: use USBPcap with Wireshark to capture USB bulk traffic.
#    The pcapng contains raw serial data including the 0xf1/0xf0 direction prefix.

# 3. On Linux: use Wireshark with the usbmon kernel module:
sudo modprobe usbmon
# Then open Wireshark → capture on usbmon<N>

# Note: captures contain the wire format:
#   TX = f1 [START] [CMD] [LEN] [DATA] [CHK]
#   RX = f0 [START] [CMD] [LEN] [DATA] [CHK]
```
