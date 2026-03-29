# Command Catalogue

> **Status:** All CMD IDs and payload layouts are placeholders / hypotheses.
> Each entry should be annotated with the capture filename that confirms it.

---

## Request / Response Pattern

Every host request (→) expects exactly one device response (←) unless noted.  
Timeout: 1 s (configurable).

---

## 0x01 – GET_STATUS

Request device measurements and set-points.

**Request (→)**

| Offset | Size | Value | Description |
|--------|------|-------|-------------|
| 0 | 1 | 0xAA | START |
| 1 | 1 | 0x01 | CMD |
| 2 | 1 | 0x00 | LENGTH (no payload) |
| 3 | 1 | 0x01 | CHECKSUM |
| 4 | 1 | 0x55 | STOP |

**Response (←) – CMD 0x02**

| Offset | Size | Field | Description |
|--------|------|-------|-------------|
| 3 | 2 | voltage_set | Set-point voltage [mV], BE u16 |
| 5 | 2 | voltage_meas | Measured voltage [mV], BE u16 |
| 7 | 2 | current_set | Current limit [mA], BE u16 |
| 9 | 2 | current_meas | Measured current [mA], BE u16 |
| 11 | 2 | flags | Bit 0: output on/off |

> **Capture evidence:** _none yet_ – update with filename once confirmed.

---

## 0x10 – SET_VOLTAGE

**Request (→)**

| Offset | Size | Field | Description |
|--------|------|-------|-------------|
| 3 | 4 | millivolts | Target voltage [mV], BE u32 |

**Response (←):** ACK or echo – TBD.

> **Capture evidence:** _none yet_

---

## 0x11 – SET_CURRENT

**Request (→)**

| Offset | Size | Field | Description |
|--------|------|-------|-------------|
| 3 | 4 | milliamps | Current limit [mA], BE u32 |

> **Capture evidence:** _none yet_

---

## 0x12 – SET_OUTPUT

**Request (→)**

| Offset | Size | Field | Description |
|--------|------|-------|-------------|
| 3 | 1 | enabled | 0x01 = on, 0x00 = off |

> **Capture evidence:** _none yet_

---

## Adding New Commands

1. Capture the traffic (see [README.md](README.md)).
2. Add a new section above following the table format.
3. Update `protocol.py` (Python enum `Cmd` + helper function).
4. Update `fnirsi_dps150.ksy` (new enum value + payload type).
5. Add a unit test in `tests/test_protocol.py`.
