# Reverse Engineering Methodology

This document describes the workflow used to capture and analyse the serial
protocol of the FNIRSI DPS-150.

---

## Tools

| Tool | Purpose |
|------|---------|
| [Wireshark](https://www.wireshark.org/) + [USBPcap](https://desowin.org/usbpcap/) | USB traffic capture on Windows (primary — used for all confirmed captures) |
| [Wireshark](https://www.wireshark.org/) + usbmon | USB traffic capture on Linux (alternative) |
| [PulseView](https://sigrok.org/wiki/PulseView) / logic analyser | UART decode if USB sniffing fails |
| [Serial Port Monitor (free)](https://www.serial-port-monitor.com/) | Quick COM port logging on Windows |
| [Kaitai Struct Web IDE](https://ide.kaitai.io/) | Interactive binary format exploration |
| `xxd` / `hexdump` | Quick hex inspection on Linux |
| `stty`+ `cat` | Raw byte capture on Linux |
| Python `serial` REPL | Interactive command probing |

---

## Step-by-Step Capture Workflow

### Primary: Windows + USBPcap (confirmed workflow)

All confirmed captures in this project were made using **Wireshark + USBPcap**
on a Windows 11 VM.  USBPcap captures **raw USB bulk payloads** without adding
any prefix bytes — the `0xf1` / `0xf0` direction byte visible in every frame
is part of the application-layer serial protocol.

1. Install USBPcap: <https://desowin.org/usbpcap/>
2. Open Wireshark, select the USBPcap capture interface for the device's bus.
3. Display filter: `usb.transfer_type == 0x03` (bulk transfers).
4. Trigger device actions (front panel or manufacturer tool).
5. Stop capture.  Export as **"C Arrays"** hex dump and save to
   `docs/protocol/captures/<descriptive_name>.txt`.
6. Annotate frames noting the wire format: `[DIR][START][CMD][LEN][DATA×LEN][CHKSUM]`.

### Alternative: Linux + usbmon

```sh
sudo modprobe usbmon
ls /dev/usbmon*   # usbmon0 = all buses, usbmon1 = bus 1, ...
```

#### Identify the USB bus

```sh
# Plugin the DPS-150 (VID 0x2e3c / PID 0x5740, Artery AT32), then:
lsusb -v 2>/dev/null | grep -A5 "FNIRSI\|2e3c"
# Note the Bus number, e.g. Bus 002
```

#### Capture with Wireshark

```sh
sudo wireshark &
# Select capture interface: usbmon2  (for Bus 002)
# Apply display filter: usb.transfer_type == 0x03  (bulk transfers only)
```

### Trigger device actions

While capturing, use the **device's front panel** or the manufacturer's
Windows tool to:
- Change voltage set-point
- Change current limit
- Toggle output on/off
- Observe any periodic status broadcasts

### Export and annotate

1. Stop the capture.
2. File → Export Specified Packets → save as `docs/protocol/captures/<description>.pcapng`.
3. Also export as **"C Arrays"** for annotated `.txt` captures.
4. Note findings in [commands.md](protocol/commands.md) with the capture filename as evidence.

> **Important**: The wire format includes a **direction byte** (`0xf1` TX,
> `0xf0` RX) as the first byte of every frame.  This is part of the serial
> data stream, not a USB-layer artefact.  See [framing.md](protocol/framing.md).

---

## Analysis Tips

- Start with **periodic / unsolicited** packets from the device – these are likely status broadcasts.
- The first byte of every frame is a **direction byte**: `0xf1` (host→device) or `0xf0` (device→host).
  Do NOT confuse this with a USB-layer artefact — it is application-layer protocol data.
- Compare packets for **small changes** (e.g. voltage 10 V → 11 V). Only the differing bytes matter.
- Look for **constant header/footer bytes** – strong candidates for START/STOP markers.
- The **second or third byte** is usually a command identifier.
- A byte equal to the remaining byte count before a possible checksum is usually the LENGTH field.
- Checksum for this device: `(CMD + LEN + Σ DATA) mod 256` — DIR and START bytes excluded.
- Use Kaitai Struct Web IDE to draft a `.ksy` and load a binary capture for instant visual feedback.
- Confirmed serial config: **9600 baud, 8N1, DTR=off, RTS=on** (from CDC SET_LINE_CODING analysis).

---

## Naming Captures

```
docs/protocol/captures/YYYYMMDD_HHMM_<description>.txt   ← text hex dump (committed)
docs/protocol/captures/YYYYMMDD_HHMM_<description>.pcapng ← binary (git-ignored)
```
