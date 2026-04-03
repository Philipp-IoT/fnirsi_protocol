# Python API Reference

## Quick example

```python
from fnirsi_ps_control.device import DPS150

with DPS150("/dev/ttyACM0") as ps:
    ps.set_voltage(12.0)
    ps.set_current_limit(1.5)
    ps.enable_output()
    status = ps.get_status()
    print(f"Vset={status.voltage_set_v:.3f} V  Iset={status.current_set_a:.3f} A")
    print(f"Vout={status.voltage_out_v:.3f} V  Iout={status.current_out_a:.3f} A")
```

## `DPS150`

High-level interface. Use as a context manager — `__enter__` opens the port and
completes the connect handshake; `__exit__` sends DISCONNECT and closes the port.

| Method | Description |
|--------|-------------|
| `set_voltage(volts)` | Set output voltage (0 – 30 V) |
| `set_current_limit(amps)` | Set current limit (0 – 5.1 A) |
| `enable_output()` | Enable power supply output |
| `disable_output()` | Disable power supply output |
| `get_status()` → `DeviceStatus` | Query full status blob (CMD 0xff) |

## `DeviceStatus`

| Field | Type | Description |
|-------|------|-------------|
| `voltage_set_v` | `float` | Set-point voltage [V] |
| `current_set_a` | `float` | Current limit [A] |
| `output_enabled` | `bool` | Output on/off (TBD — offset in blob not yet confirmed) |
| `voltage_out_v` | `float` | Measured output voltage [V] |
| `current_out_a` | `float` | Measured output current [A] |

## Protocol Layer

### TX encoders (`protocol.py`)

| Function | Returns | Description |
|----------|---------|-------------|
| `encode_connect()` | `Frame` | CONNECT frame |
| `encode_disconnect()` | `Frame` | DISCONNECT frame |
| `encode_set_voltage(volts)` | `Frame` | SET_VOLTAGE (CMD 0xc1) |
| `encode_set_current(amps)` | `Frame` | SET_CURRENT (CMD 0xc2) |
| `encode_set_output(enabled)` | `Frame` | SET_OUTPUT (CMD 0xdb) |
| `encode_get_status()` | `Frame` | GET_FULL_STATUS query (CMD 0xff) |
| `parse_frame(raw)` | `FnirsiDps150` | Parse RX bytes using Kaitai parser |

### RX parser (`protocol/generated/fnirsi_dps150.py`)

Generated from `protocol/fnirsi_dps150.ksy`. Access parsed fields via the Kaitai object:

```python
from fnirsi_ps_control.protocol import parse_frame

parsed = parse_frame(raw_bytes)
frame = parsed.frame
# frame.start, frame.cmd, frame.length, frame.payload, frame.checksum

# For PUSH_OUTPUT (CMD 0xc3):
p = frame.payload  # PushOutputPayload
print(p.vout, p.iout, p.pout)

# For GET_FULL_STATUS (CMD 0xff):
s = frame.payload  # FullStatusPayload
print(s.vset, s.iset, s.vout, s.iout)
```
