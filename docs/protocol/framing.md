# Frame Structure

> **Status:** CONFIRMED from capture `dps150_connect_set_10v_set_1A_disconnect.txt`
> and verified against live hardware (2026-03-29).

## Wire Format

Every serial transfer is prepended with a **direction prefix byte**:

```
Offset   Size  Field     Description
──────   ────  ────────  ─────────────────────────────────────────────────────
0        1     DIR       Direction prefix (0xf1 = TX, 0xf0 = RX)
1        1     START     Packet type identifier (see below)
2        1     CMD       Command / register ID
3        1     LEN       Byte length of the DATA field (0–255)
4        LEN   DATA      Command-specific payload
4+LEN    1     CHKSUM    Integrity byte
```

The DIR byte is part of the serial data stream (confirmed from Windows
USBPcap capture — USBPcap records raw bulk payloads without modification).
It is **not** a USB-layer artefact.

**Minimum wire size:** 5 bytes (DIR + START + CMD + LEN=0 + CHKSUM).

## Application Frame (after stripping DIR)

```
Offset   Size  Field     Description
──────   ────  ────────  ─────────────────────────────────────────────────────
0        1     START     Packet type identifier (see below)
1        1     CMD       Command / register ID
2        1     LEN       Byte length of the DATA field (0–255)
3        LEN   DATA      Command-specific payload
3+LEN    1     CHKSUM    Integrity byte
```

**No fixed stop byte.** Minimum application frame size: 4 bytes (LEN=0).

---

## Direction Prefix (DIR)

| Value  | Direction  | Meaning                       |
|--------|------------|-------------------------------|
| `0xf1` | Host → Dev | Prepended to every TX frame   |
| `0xf0` | Dev → Host | Prepended to every RX frame   |

---

## START Byte Values

| Value | Direction  | Meaning                          |
|-------|------------|----------------------------------|
| `0xa1`| Host → Dev | Read / query request             |
| `0xa1`| Dev → Host | All device responses             |
| `0xb1`| Host → Dev | Write / set command              |
| `0xc1`| Host → Dev | Connect / disconnect control     |
| `0xb0`| Host → Dev | Start-session magic (see below)  |

---

## Checksum Algorithm

```
CHKSUM = (CMD + LEN + DATA[0] + DATA[1] + ... + DATA[LEN-1]) mod 256
```

Verified against every frame in the capture.

The `0xb0` start-session magic frame (`b0 00 01 01 01`) uses a non-standard
checksum (expected `0x02`, observed `0x01`). It is treated as an opaque
5-byte sequence sent after the READY handshake in every session.

---

## Data Encoding

All voltage and current values are encoded as **IEEE 754 32-bit little-endian floats** in SI units (volts / amps).

```python
import struct

def encode_f32(value: float) -> bytes:
    return struct.pack('<f', value)

def decode_f32(data: bytes) -> float:
    return struct.unpack('<f', data)[0]
```

String fields (device name, version) are plain ASCII, no NUL terminator.

---

## Example Frames

### SET_VOLTAGE 10.0 V  (confirmed)

```
              Application frame (after DIR prefix 0xf1)
              ┌───────────────────────────────────────┐
Wire: f1  b1  c1  04  00 00 20 41  26
      │   │   │   │   └──────────┘  └── CHKSUM = (c1+04+00+00+20+41) mod 256 = 0x26 ✓
      │   │   │   └── LEN = 4 bytes
      │   │   └────── CMD = 0xc1 (SET_VOLTAGE)
      │   └────────── START = 0xb1 (write command)
      └────────────── DIR = 0xf1 (host→device)

Data: 0x41200000 (LE) = 10.0f
```

### SET_CURRENT 1.0 A  (confirmed)

```
Wire: f1  b1  c2  04  00 00 80 3f  85
Data: 0x3f800000 (LE) = 1.0f
CHKSUM = (c2+04+00+00+80+3f) mod 256 = 0x85 ✓
```

### CONNECT REQUEST

```
Wire: f1  c1  00  01  01  02
          │               └── CHKSUM = (00+01+01) mod 256 = 0x02 ✓
          │           └────── DATA = 0x01 (connect; 0x00 = disconnect)
          │       └────────── LEN = 1
          │   └────────────── CMD = 0x00
          └────────────────── START = 0xc1
      └── DIR = 0xf1 (host→device)
```

### Device response: device name "DPS-150"

```
Wire: f0  a1  de  07  44 50 53 2d 31 35 30  8f
          │           └─────────────────┘   └── CHKSUM = 0x8f ✓
          │           "DPS-150" in ASCII
          │       └── LEN = 7
          │   └────── CMD = 0xde (GET_DEVICE_NAME)
          └────────── START = 0xa1 (response)
      └── DIR = 0xf0 (device→host)
```
