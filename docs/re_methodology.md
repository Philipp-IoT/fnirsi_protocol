# Reverse Engineering Methodology

This document describes the workflow used to capture and analyse the serial
protocol of the FNIRSI DPS-150.

---

## Tools

| Tool | Purpose |
|------|---------|
| [Wireshark](https://www.wireshark.org/) + usbmon | USB traffic capture on Linux |
| [USBPcap](https://desowin.org/usbpcap/) | USB traffic capture on Windows |
| [PulseView](https://sigrok.org/wiki/PulseView) / logic analyser | UART decode if USB sniffing fails |
| [Serial Port Monitor (free)](https://www.serial-port-monitor.com/) | Quick COM port logging on Windows |
| [Kaitai Struct Web IDE](https://ide.kaitai.io/) | Interactive binary format exploration |
| `xxd` / `hexdump` | Quick hex inspection on Linux |
| `stty`+ `cat` | Raw byte capture on Linux |
| Python `serial` REPL | Interactive command probing |

---

## Step-by-Step Capture Workflow (Linux / Wireshark)

### 1. Load the usbmon kernel module

```sh
sudo modprobe usbmon
ls /dev/usbmon*   # usbmon0 = all buses, usbmon1 = bus 1, ...
```

### 2. Identify the USB bus

```sh
# Plugin the DPS-150, then:
lsusb -v 2>/dev/null | grep -A5 "FNIRSI\|<VID>"
# Note the Bus number, e.g. Bus 002
```

### 3. Capture with Wireshark

```sh
sudo wireshark &
# Select capture interface: usbmon2  (for Bus 002)
# Apply display filter: usb.transfer_type == 0x03  (bulk transfers only)
```

### 4. Trigger device actions

While capturing, use the **device's front panel** to:
- Change voltage set-point
- Change current limit
- Toggle output on/off
- Observe any periodic status broadcasts

### 5. Export and annotate

1. Stop the capture.
2. File → Export Specified Packets → save as `docs/protocol/captures/YYYYMMDD_<action>.pcapng`.
3. Note findings in [commands.md](protocol/commands.md) with the capture filename as evidence.

---

## Analysis Tips

- Start with **periodic / unsolicited** packets from the device – these are likely status broadcasts.
- Compare packets for **small changes** (e.g. voltage 10 V → 11 V). Only the differing bytes matter.
- Look for **constant header/footer bytes** – strong candidates for START/STOP markers.
- The **second or third byte** is usually a command identifier.
- A byte equal to the remaining byte count before a possible checksum is usually the LENGTH field.
- XOR all bytes before the last byte (before STOP) and see if it equals the last byte before STOP.
- Use Kaitai Struct Web IDE to draft a `.ksy` and load a binary capture for instant visual feedback.

---

## Naming Captures

```
docs/protocol/captures/YYYYMMDD_HHMM_<description>.txt   ← text hex dump (committed)
docs/protocol/captures/YYYYMMDD_HHMM_<description>.pcapng ← binary (git-ignored)
```
