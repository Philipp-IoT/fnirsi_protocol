# Command Catalogue

> **Status:** Commands marked ✓ are confirmed from
> `captures/dps150_connect_set_10v_set_1A_disconnect.txt`.
> Commands marked TBD are hypothetical.

All frames follow `[START] [CMD] [LEN] [DATA×LEN] [CHKSUM]` — see [framing.md](framing.md).

---

## Connect / Disconnect — CMD 0x00  (START=0xc1) ✓

| Direction | Frame |
|-----------|-------|
| TX connect    | `c1 00 01 01 02` |
| TX disconnect | `c1 00 01 00 01` |

DATA byte `0x01` = connect, `0x00` = disconnect.

---

## Get Ready Status — CMD 0xe1  (START=0xa1) ✓

**Request:** `a1 e1 01 00 e2`

**Response:**

| Offset | Size | Value | Description |
|--------|------|-------|-------------|
| 0      | 1    | 0x01  | Ready (0x00 = not ready) |

---

## Get Device Name — CMD 0xde  (START=0xa1) ✓

**Request:** `a1 de 01 00 df`

**Response:** ASCII string, LEN bytes, no NUL terminator.

| Device | Response bytes | String |
|--------|----------------|--------|
| DPS-150 | `44 50 53 2d 31 35 30` | `"DPS-150"` |

---

## Get HW Version — CMD 0xe0  (START=0xa1) ✓

**Request:** `a1 e0 01 00 e1`

**Response:** ASCII string. Example: `"V1.2"` (4 bytes).

---

## Get FW Version — CMD 0xdf  (START=0xa1) ✓

**Request:** `a1 df 01 00 e0`

**Response:** ASCII string. Example: `"V1.0"` (4 bytes).

---

## Get Full Status — CMD 0xff  (START=0xa1) ✓

**Request:** `a1 ff 01 00 00`

**Response:** LEN = 0x8b (139 bytes). See layout below.

### Status blob layout (offsets into DATA)

Bytes 0–95: 24 × IEEE 754 32-bit LE float

| Offset | Float value (example) | Interpretation |
|--------|-----------------------|----------------|
| 0      | 20.095 V              | Vin measured   |
| 4      | 12.000 V              | Vset (current) |
| 8      | 0.100 A               | Iset (current) |
| 12     | 0.000 V               | Vout measured  |
| 16     | 0.000 A               | Iout measured  |
| 20     | 0.000 W               | Pout measured  |
| 24     | 23.619 V              | ? (internal rail / Vin2 – TBD) |
| 28     | 12.000 V              | Vset echo / ch2 (TBD) |
| 32     | 0.100 A               | Iset echo / ch2 (TBD) |
| 36–39  | 5.000 V               | Preset 1 Vset  |
| 40–43  | 1.000 A               | Preset 1 Iset  |
| 44–47  | 5.000 V               | Preset 2 Vset  |
| 48–51  | 1.000 A               | Preset 2 Iset  |
| 52–55  | 5.000 V               | Preset 3 Vset  |
| 56–59  | 1.000 A               | Preset 3 Iset  |
| 60–63  | 5.000 V               | Preset 4 Vset  |
| 64–67  | 1.000 A               | Preset 4 Iset  |
| 68–71  | 5.000 V               | Preset 5 Vset  |
| 72–75  | 1.000 A               | Preset 5 Iset  |
| 76     | 30.000 V              | MAX_VOLTAGE    |
| 80     | 5.100 A               | MAX_CURRENT    |
| 84     | 150.000 W             | MAX_POWER  ← confirms "DPS-150" = 150 W |
| 88     | 80.000                | MAX_TEMP [°C]? (TBD) |
| 92     | 5.000                 | ? (TBD)        |

Bytes 96–138: mixed types (TBD — needs additional captures)

| Offset | Size | Value | Interpretation |
|--------|------|-------|----------------|
| 96     | 4    | 10 (uint32 LE) | Preset count? |
| 100–107| 8    | 0              | Reserved?      |
| 108    | 1    | 0x00           | ?              |
| 109    | 1    | 0x01           | Output state?  |
| 110    | 1    | 0x01           | Lock state?    |
| 111–138| 28   | floats (TBD)   | repeated limits / status |

---

## Set Voltage — CMD 0xc1  (START=0xb1) ✓

**Frame:** `b1 c1 04 [float32 LE] [chk]`

DATA = target voltage in **volts** as IEEE 754 32-bit LE float.

| Example | Bytes               | Value  |
|---------|---------------------|--------|
| 10.0 V  | `00 00 20 41`       | 10.0 V |
| 12.0 V  | `00 00 40 41`       | 12.0 V |
|  1.0 V  | `00 00 80 3f`       |  1.0 V |

No explicit ACK observed in capture (fire-and-forget or ACK is implicit in the next periodic push).

---

## Set Current Limit — CMD 0xc2  (START=0xb1) ✓

**Frame:** `b1 c2 04 [float32 LE] [chk]`

DATA = current limit in **amps** as IEEE 754 32-bit LE float.

| Example | Bytes               | Value  |
|---------|---------------------|--------|
| 1.0 A   | `00 00 80 3f`       | 1.0 A  |
| 0.1 A   | `cd cc cc 3d`       | 0.1 A  |

---

## Periodic Device Push: Output Measurements — CMD 0xc3  (START=0xa1) ✓

**Interval:** ~600 ms (unsolicited; device sends continuously).

**Frame:** `a1 c3 0c [3 × float32 LE] [chk]`  (LEN = 12 bytes)

| Float index | Interpretation       |
|-------------|----------------------|
| 0           | Vout measured [V]    |
| 1           | Iout measured [A]    |
| 2           | ? (TBD)              |

All three are 0.0 when the output is disabled.

**Capture evidence:** rows 2481, 2741, 2809, 2827, 2841, 2851, etc.

---

## Periodic Device Push: Vin Channel A — CMD 0xc0  (START=0xa1) ✓

**Frame:** `a1 c0 04 [float32 LE] [chk]`

Observed values: ~20.09–20.10 V → input supply voltage (channel A ADC).

---

## Periodic Device Push: ??? — CMD 0xe2  (START=0xa1) ✓

**Frame:** `a1 e2 04 [float32 LE] [chk]`

Observed values: ~19.89–19.90 V. Same rail as CMD 0xc0 at slightly different ADC point. TBD.

---

## Periodic Device Push: MAX_CURRENT reference — CMD 0xe3  (START=0xa1) ✓

**Frame:** `a1 e3 04 33 33 a3 40 30`

Value is always **5.1 A** (= device maximum current). Broadcast as a reference constant.

---

## Periodic Device Push: ??? — CMD 0xc4  (START=0xa1) ✓

**Frame:** `a1 c4 04 [float32 LE] [chk]`

Observed values: ~23.62–23.67 V. Possibly Vin on a second ADC channel or internal boost rail. TBD.

---

## Adding New Commands

1. Capture traffic while performing the new action (see [../re_methodology.md](../re_methodology.md)).
2. Add a section above, citing the capture filename.
3. Update `protocol.py` (`class Cmd` + helper function).
4. Update `fnirsi_dps150.ksy` (enum + payload type).
5. Add a unit test in `tests/test_protocol.py`.
