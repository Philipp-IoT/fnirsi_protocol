meta:
  id: fnirsi_dps150
  title: FNIRSI DPS-150 Serial Protocol
  file-extension: bin
  license: MIT
  ks-version: 0.10
  endian: be
  doc: |
    Serial protocol for the FNIRSI DPS-150 regulated power supply,
    communicated over USB CDC (virtual COM port).

    **Status**: work-in-progress – all field names and values are
    hypothetical until confirmed by live captures.

    See docs/protocol/ for the full reverse-engineering notes.

seq:
  - id: frame
    type: frame

types:
  frame:
    doc: Top-level protocol frame.
    seq:
      - id: start
        contents: [0xAA]
        doc: Frame start marker (TBD – value 0xAA is a placeholder).
      - id: cmd
        type: u1
        enum: command_id
        doc: Command identifier.
      - id: length
        type: u1
        doc: Byte length of the payload field.
      - id: payload
        size: length
        type:
          switch-on: cmd
          cases:
            'command_id::get_status_resp': status_payload
            'command_id::set_voltage':     set_voltage_payload
            'command_id::set_current':     set_current_payload
            'command_id::set_output':      set_output_payload
        doc: Command-specific payload – see sub-types.
      - id: checksum
        type: u1
        doc: |
          Checksum over [cmd, length, payload].
          Algorithm TBD (XOR of all bytes is the current hypothesis).
      - id: stop
        contents: [0x55]
        doc: Frame stop marker (TBD – value 0x55 is a placeholder).

  # ---------------------------------------------------------------------------
  # Payload types – expand as RE progresses
  # ---------------------------------------------------------------------------
  status_payload:
    doc: |
      Response to a GET_STATUS request.
      Layout is hypothetical – update once confirmed by captures.
    seq:
      - id: voltage_set
        type: u2
        doc: Set-point voltage in millivolts.
      - id: voltage_meas
        type: u2
        doc: Measured output voltage in millivolts.
      - id: current_set
        type: u2
        doc: Current limit in milliamps.
      - id: current_meas
        type: u2
        doc: Measured output current in milliamps.
      - id: flags
        type: u2
        doc: |
          Bit-field of device flags.
          Bit 0: output enabled (1) / disabled (0).

  set_voltage_payload:
    doc: Payload for SET_VOLTAGE command.
    seq:
      - id: millivolts
        type: u4
        doc: Target voltage in millivolts.

  set_current_payload:
    doc: Payload for SET_CURRENT command.
    seq:
      - id: milliamps
        type: u4
        doc: Current limit in milliamps.

  set_output_payload:
    doc: Payload for SET_OUTPUT command.
    seq:
      - id: enabled
        type: u1
        doc: 0x01 = enable output, 0x00 = disable.

enums:
  command_id:
    # TBD – values below are placeholders
    0x01: get_status
    0x02: get_status_resp
    0x10: set_voltage
    0x11: set_current
    0x12: set_output
