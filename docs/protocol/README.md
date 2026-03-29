# Protocol Reverse Engineering – Overview

> **Status:** Work in progress. All values marked _TBD_ are working hypotheses
> that must be confirmed (or corrected) using live hardware captures.

---

## Device

| Item | Value |
|------|-------|
| Model | FNIRSI DPS-150 |
| Interface | USB CDC / ACM (virtual COM port) |
| Baud rate | **TBD** |
| Data bits | 8 |
| Stop bits | 1 |
| Parity | None |
| Flow control | None (hardware RTS/CTS – TBD) |
| USB VID | **TBD** |
| USB PID | **TBD** |

Run `lsusb` with the device plugged in to discover VID/PID on Linux.

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

# 2. Capture raw bytes while operating the device from its front panel
#    (requires root or membership in the 'dialout' group)
stty -F /dev/ttyACM0 115200 raw
cat /dev/ttyACM0 | tee docs/protocol/captures/$(date +%Y%m%d_%H%M%S).log | xxd

# 3. Or use Wireshark with the usbmon kernel module:
sudo modprobe usbmon
# Then open Wireshark → capture on usbmon<N>
```
