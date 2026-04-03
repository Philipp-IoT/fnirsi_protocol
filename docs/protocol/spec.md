# Protocol Specification

!!! tip "Single source of truth"
    The **Kaitai Struct specification**
    `protocol/fnirsi_dps150.ksy` is the authoritative,
    machine-readable definition of the FNIRSI DPS-150 serial protocol.
    All frame structures, command IDs, payload types and enumerations are
    defined there.  This page embeds it directly and adds annotated wire
    examples for quick reference.

---

## Kaitai Struct Spec — `fnirsi_dps150.ksy`

```yaml
--8<-- "protocol/fnirsi_dps150.ksy"
```

---

## Using the Specification

=== "Kaitai Web IDE"

    Paste the `.ksy` source above into the
    [Kaitai Struct Web IDE](https://ide.kaitai.io/) and load a binary
    capture for interactive exploration.

=== "Compile to Python"

    ```sh
    bash scripts/gen_kaitai.sh
    # output: protocol/generated/fnirsi_dps150.py
    ```

=== "Other targets"

    Supported: `java`, `csharp`, `ruby`, `javascript`, `go`, `php`, etc.
    See [kaitai.io](https://kaitai.io/) for the full list.

---

## Annotated Wire Examples

These real-world frame dumps complement the `.ksy` spec.  All checksums
verified against the algorithm defined in the spec.

### SET_VOLTAGE 10.0 V

```
              Application frame (after DIR prefix 0xf1)
              ┌───────────────────────────────────────┐
Wire: f1  b1  c1  04  00 00 20 41  26
      │   │   │   │   └──────────┘  └── CHKSUM = (c1+04+00+00+20+41) mod 256 = 0x26 ✓
      │   │   │   └── LEN = 4 bytes
      │   │   └────── CMD = 0xc1 (set_voltage)
      │   └────────── START = 0xb1 (write_command)
      └────────────── DIR = 0xf1 (host→device)

Data: 0x41200000 (LE) = 10.0f
```

### SET_CURRENT 1.0 A

```
Wire: f1  b1  c2  04  00 00 80 3f  85
Data: 0x3f800000 (LE) = 1.0f
CHKSUM = (c2+04+00+00+80+3f) mod 256 = 0x85 ✓
```

### CONNECT

```
Wire: f1  c1  00  01  01  02
          │               └── CHKSUM = (00+01+01) mod 256 = 0x02 ✓
          │           └────── DATA = 0x01 (connect_state::connect)
          │       └────────── LEN = 1
          │   └────────────── CMD = 0x00 (connect_ctrl)
          └────────────────── START = 0xc1 (connect_ctrl)
      └── DIR = 0xf1 (host→device)
```

### DISCONNECT

```
Wire: f1  c1  00  01  00  01
          │               └── CHKSUM = (00+01+00) mod 256 = 0x01 ✓
          │           └────── DATA = 0x00 (connect_state::disconnect)
          │       └────────── LEN = 1
          │   └────────────── CMD = 0x00 (connect_ctrl)
          └────────────────── START = 0xc1 (connect_ctrl)
      └── DIR = 0xf1 (host→device)
```

### Device Response: device name "DPS-150"

```
Wire: f0  a1  de  07  44 50 53 2d 31 35 30  8f
          │           └─────────────────┘   └── CHKSUM = 0x8f ✓
          │           "DPS-150" in ASCII
          │       └── LEN = 7
          │   └────── CMD = 0xde (get_device_name)
          └────────── START = 0xa1 (query_or_response)
      └── DIR = 0xf0 (device→host)
```

### Enable Output

```
Wire: f1  b1  db  01  01  dd
          │           └── DATA = 0x01 (output_state::enabled)
          │       └────── LEN = 1
          │   └────────── CMD = 0xdb (set_output)
          └────────────── START = 0xb1 (write_command)
      └── DIR = 0xf1 (host→device)

Echo: f0  a1  db  01  01  dd   ← device echoes with START = 0xa1
```

### Disable Output

```
Wire: f1  b1  db  01  00  dc
Echo: f0  a1  db  01  00  dc
```

### GET_FULL_STATUS Query

```
Wire: f1  a1  ff  01  00  00
          │           └── DATA = 0x00
          │       └────── LEN = 1
          │   └────────── CMD = 0xff (get_full_status)
          └────────────── START = 0xa1 (query_or_response)

Response: f0  a1  ff  8b  [139 bytes — see full_status_payload in .ksy]  [chk]
```

---

## Adding New Commands

1. Capture USB traffic with Wireshark while performing the action.
   Save to `docs/protocol/captures/`.
2. Update **`fnirsi_dps150.ksy`**: add the command to `command_id` enum,
   create a payload type, add the `cases` entry in `frame`.
3. Update `src/fnirsi_ps_control/protocol.py` (`Cmd` class + builder function).
4. Add a byte-exact unit test in `tests/test_protocol.py`.
5. Add an annotated wire example to the section above.
