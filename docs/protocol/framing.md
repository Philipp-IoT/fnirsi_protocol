# Frame Structure

> **Status:** Hypothesis – all byte values are placeholders until verified.

## Overview

All communication uses a simple request/response framing:

```
Offset  Size  Field     Description
------  ----  --------  -----------------------------------------------------
0       1     START     Frame start marker. Hypothesis: 0xAA
1       1     CMD       Command / response identifier (see commands.md)
2       1     LENGTH    Byte length of the PAYLOAD field (0–255)
3       N     PAYLOAD   Command-specific data (N = LENGTH)
3+N     1     CHECKSUM  Integrity check over [CMD, LENGTH, PAYLOAD]
4+N     1     STOP      Frame stop marker. Hypothesis: 0x55
```

Minimum frame length (empty payload): **5 bytes**.

---

## Byte Order

Multi-byte integers: **big-endian** (hypothesis – verify in captures).

---

## Checksum

Current hypothesis: **XOR** of all bytes in `[CMD, LENGTH, PAYLOAD]`.

```
checksum = CMD XOR LENGTH XOR payload[0] XOR payload[1] XOR ...
```

Alternative candidates to verify:
- Sum modulo 256
- CRC-8

### Verification procedure

1. Capture a known command (e.g. GET_STATUS) sent by the official PC software.
2. Extract `[CMD, LENGTH, PAYLOAD]` bytes.
3. Compute XOR, sum-mod-256, and CRC-8.
4. Compare with the captured `CHECKSUM` byte and update this document.

---

## Example (hypothetical GET_STATUS request)

```
AA  01  00  01  55
│   │   │   │   └─ STOP  (0x55)
│   │   │   └───── CHECKSUM = 0x01 XOR 0x00 = 0x01
│   │   └───────── LENGTH = 0 (no payload)
│   └───────────── CMD = 0x01 (GET_STATUS)
└───────────────── START (0xAA)
```
