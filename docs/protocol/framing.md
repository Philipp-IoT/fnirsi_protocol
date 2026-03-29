# Frame Structure

> **Status:** CONFIRMED from capture `dps150_connect_set_10v_set_1A_disconnect.txt`

## Frame Layout

```
Offset   Size  Field     Description
──────   ────  ────────  ─────────────────────────────────────────────────────
0        1     START     Packet type identifier (see below)
1        1     CMD       Command / register ID
2        1     LEN       Byte length of the DATA field (0–255)
3        LEN   DATA      Command-specific payload
3+LEN    1     CHKSUM    Integrity byte
```

**No fixed stop byte.** Minimum frame size: 4 bytes (LEN=0).

---

## START Byte Values

| Value | Direction  | Meaning                          |
|-------|------------|----------------------------------|
| `0xa1`| Host → Dev | Read / query request             |
| `0xa1`| Dev → Host | All device responses             |
| `0xb1`| Host → Dev | Write / set command              |
| `0xc1`| Host → Dev | Connect / disconnect control     |
| `0xb0`| Host → Dev | Unknown (one capture; checksum anomaly) |

---

## Checksum Algorithm

```
CHKSUM = (CMD + LEN + DATA[0] + DATA[1] + ... + DATA[LEN-1]) mod 256
```

Verified against every frame in the capture (except the single `0xb0` packet).

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
b1  c1  04  00 00 20 41  26
│   │   │   └──────────┘  └── CHKSUM = (c1+04+00+00+20+41) mod 256 = 0x26 ✓
│   │   └── LEN = 4 bytes
│   └────── CMD = 0xc1 (SET_VOLTAGE)
└────────── START = 0xb1 (write command)

Data: 0x41200000 (LE) = 10.0f
```

### SET_CURRENT 1.0 A  (confirmed)

```
b1  c2  04  00 00 80 3f  85
Data: 0x3f800000 (LE) = 1.0f
CHKSUM = (c2+04+00+00+80+3f) mod 256 = 0x85 ✓
```

### CONNECT REQUEST

```
c1  00  01  01  02
│               └── CHKSUM = (00+01+01) mod 256 = 0x02 ✓
│           └────── DATA = 0x01 (connect; 0x00 = disconnect)
│       └────────── LEN = 1
│   └────────────── CMD = 0x00
└────────────────── START = 0xc1
```

### Device response: device name "DPS-150"

```
a1  de  07  44 50 53 2d 31 35 30  8f
│           └─────────────────┘   └── CHKSUM = (de+07+44+50+53+2d+31+35+30) mod 256 = 0x8f ✓
│           "DPS-150" in ASCII
│       └── LEN = 7
│   └────── CMD = 0xde (GET_DEVICE_NAME)
└────────── START = 0xa1 (response)
```
