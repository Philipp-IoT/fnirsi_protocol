# Serial protocol for the FNIRSI DPS-150 regulated power supply,
# communicated over USB CDC (virtual COM port, USB bulk endpoint).
#
# Wire format  [DIR][START][CMD][LEN][DATA×LEN][CHKSUM]
#   DIR    : 0xf1 host→device | 0xf0 device→host (direction prefix)
#   START  : 0xa1 query/response | 0xb1 write cmd | 0xc1 connect/disconnect
#   CHKSUM : (CMD + LEN + Σ DATA) mod 256  (DIR and START excluded)
#   Values : IEEE 754 32-bit little-endian float for voltage / current
#
# The DIR byte is part of the serial data stream, NOT a USB-layer
# artefact (confirmed from Windows USBPcap raw bulk payloads).
# This spec describes the application frame AFTER stripping the DIR byte.
#
# Status: CONFIRMED from capture and live hardware test 2026-03-29
# USB: VID 0x2e3c (Artery) / PID 0x5740 (AT32 Virtual Com Port)
# Serial: 9600 baud, 8N1, DTR=off, RTS=on

meta:
  id: fnirsi_dps150
  title: FNIRSI DPS-150 Serial Protocol
  file-extension: bin
  license: MIT
  ks-version: '0.11'
  endian: le

seq:
  - id: frame
    type: frame

types:
  frame:
    doc: Top-level protocol frame.
    seq:
      - id: start
        type: u1
        enum: start_byte
        doc: Packet type identifier.
      - id: cmd
        type: u1
        enum: command_id
        doc: Command / register identifier.
      - id: length
        type: u1
        doc: Byte length of the payload field.
      - id: payload
        size: length
        type:
          switch-on: cmd
          cases:
            'command_id::connect_ctrl':    connect_payload
            'command_id::ready_status':    ready_payload
            'command_id::get_device_name': string_payload
            'command_id::get_hw_version':  string_payload
            'command_id::get_fw_version':  string_payload
            'command_id::get_full_status': full_status_payload
            'command_id::set_voltage':     float32_payload
            'command_id::set_current':     float32_payload
            'command_id::set_output':      output_enable_payload
            'command_id::push_output':     push_output_payload
            'command_id::push_vin_a':      float32_payload
            'command_id::push_vin_b':      float32_payload
            'command_id::push_max_current': float32_payload
            'command_id::push_vin_c':      float32_payload
      - id: checksum
        type: u1
        doc: |
          (CMD + LEN + Σ DATA bytes) mod 256. Confirmed by capture analysis.

  # ---------------------------------------------------------------------------
  # Payload types
  # ---------------------------------------------------------------------------
  output_enable_payload:
    doc: |
      Payload for CMD set_output (0xdb).
      DATA = 0x01 → enable output, DATA = 0x00 → disable output.
      The device echoes the full frame back with START = 0xa1.
      Confirmed from capture dps150_connect_enable_out_set_v_set_i_disable_disconnect.txt.
    seq:
      - id: state
        type: u1
        enum: output_state

  connect_payload:
    doc: |
      Payload for CMD connect_ctrl (0x00).
      DATA = 0x01 → connect, DATA = 0x00 → disconnect.
    seq:
      - id: state
        type: u1
        enum: connect_state

  ready_payload:
    doc: Device ready status (CMD 0xe1).
    seq:
      - id: ready
        type: u1
        doc: 0x01 = device ready, 0x00 = not ready.

  string_payload:
    doc: Variable-length ASCII string (no NUL terminator).
    seq:
      - id: value
        type: str
        encoding: ASCII
        size-eos: true

  float32_payload:
    doc: Single IEEE 754 32-bit LE float (voltage in V or current in A).
    seq:
      - id: value
        type: f4

  push_output_payload:
    doc: |
      CMD 0xc3 – periodic output measurement push (LEN=12, three floats).
      All values are 0.0 when output is disabled.
    seq:
      - id: vout
        type: f4
        doc: Measured output voltage [V].
      - id: iout
        type: f4
        doc: Measured output current [A].
      - id: pout
        type: f4
        doc: |
          Measured output power [W].
          Confirmed from capture row 12827: Vout≈8.45 V, Iout≈0.0077 A → Pout≈0.065 W.

  full_status_payload:
    doc: |
      CMD 0xff – full status blob (LEN=0x8b = 139 bytes).
      Offsets 0–95: 24 floats.  Offsets 96–138: mixed types (TBD).
    seq:
      - id: vin
        type: f4
        doc: Measured input voltage [V].
      - id: vset
        type: f4
        doc: Current voltage set-point [V].
      - id: iset
        type: f4
        doc: Current current limit [A].
      - id: vout
        type: f4
        doc: Measured output voltage [V] (0 when output off).
      - id: iout
        type: f4
        doc: Measured output current [A] (0 when output off).
      - id: pout
        type: f4
        doc: Measured output power [W] (0 when output off).
      - id: vin2
        type: f4
        doc: Secondary input voltage measurement [V] – TBD.
      - id: vset2
        type: f4
        doc: Duplicate / channel-2 Vset – TBD.
      - id: iset2
        type: f4
        doc: Duplicate / channel-2 Iset – TBD.
      - id: presets
        type: preset
        repeat: expr
        repeat-expr: 5
        doc: Five stored presets (Vset, Iset each).
      - id: max_voltage
        type: f4
        doc: Device maximum output voltage [V] (30.0).
      - id: max_current
        type: f4
        doc: Device maximum output current [A] (5.1).
      - id: max_power
        type: f4
        doc: Device maximum output power [W] (150.0 = DPS-150).
      - id: max_temp
        type: f4
        doc: Maximum temperature [°C]? (80.0 – TBD).
      - id: unknown_f
        type: f4
        doc: Unknown float at offset 92 – TBD.
      - id: remainder
        size-eos: true
        doc: Mixed-type tail (offsets 96–138). Layout TBD.

  preset:
    doc: One stored preset (Vset + Iset pair).
    seq:
      - id: vset
        type: f4
        doc: Preset voltage set-point [V].
      - id: iset
        type: f4
        doc: Preset current limit [A].

enums:
  start_byte:
    0xa1: query_or_response
    0xb0: start_session_magic
    0xb1: write_command
    0xc1: connect_ctrl

  command_id:
    0x00: connect_ctrl
    0xc0: push_vin_a
    0xc1: set_voltage
    0xc2: set_current
    0xc3: push_output
    0xc4: push_vin_c
    0xdb: set_output
    0xde: get_device_name
    0xdf: get_fw_version
    0xe0: get_hw_version
    0xe1: ready_status
    0xe2: push_vin_b
    0xe3: push_max_current
    0xff: get_full_status

  connect_state:
    0x00: disconnect
    0x01: connect

  output_state:
    0x00: disabled
    0x01: enabled
