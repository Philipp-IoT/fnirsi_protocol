# Captures

Raw USB capture logs from Wireshark / USBPcap sessions with the FNIRSI DPS-150.

Binary captures (`.pcapng`) are excluded from the repository via `.gitignore`.
Text exports ("C Arrays" format) are committed.

## Available Captures

| File | Date | Description |
|------|------|-------------|
| `dps150_connect_set_10v_set_1A_disconnect.txt` | 2026-03-29 | Connect, set 10 V, set 1 A, disconnect. Confirms frame format, checksums, float encoding. |
| `dps150_connect_enable_out_set_v_set_i_disable_disconnect.txt` | 2026-03-29 | Connect, enable output, set voltage, set current, disable output, disconnect. Confirms CMD 0xdb and PUSH_OUTPUT (CMD 0xc3) with Pout field. |

## Capture Methodology

See [RE Methodology](../re_methodology.md) for the step-by-step Wireshark capture workflow.
