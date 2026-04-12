# Serial protocol for the FNIRSI DPS-150 regulated power supply,
# communicated over USB CDC (virtual COM port, USB bulk endpoint).
#
# Wire format  [DIR][START][CMD][LEN][DATA×LEN][CHKSUM]
#   DIR    : 0xf1 host→device | 0xf0 device→host (direction prefix)
#   START  : 0xa1 query/response | 0xb1 write cmd | 0xc1 connect/disconnect
#   CHKSUM : (CMD + LEN + Σ DATA) mod 256  (DIR and START excluded)
#   Values : IEEE 754 32-bit little-endian float for voltage / current
#
# Exception: the session-start magic frame (START=0xb0) uses a non-standard
# 4-byte body without CMD/LEN/CHKSUM — see session_magic_body below.
#
# The DIR byte is part of the serial data stream, NOT a USB-layer
# artefact (confirmed from Windows USBPcap raw bulk payloads).
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
    doc: Full wire frame including direction prefix.
    seq:
      - id: dir
        type: u1
        enum: direction
        doc: Direction byte — 0xf1 host→device, 0xf0 device→host.
      - id: start
        type: u1
        enum: start_byte
        doc: Packet type identifier.
      - id: body
        doc: Frame body — structure depends on start byte.
        type:
          switch-on: start
          cases:
            'start_byte::start_session_magic': session_magic_body
            _: command_body

  session_magic_body:
    doc: |
      Non-standard 4-byte payload of the session-start magic frame (START=0xb0).
      Does not follow the CMD/LEN/DATA/CHKSUM format; checksum is absent.
      Wire (after DIR+START): 00 01 01 01 — confirmed from capture 2026-03-29.
      Direction: TX only (host→device).
    seq:
      - id: magic
        contents: [0x00, 0x01, 0x01, 0x01]

  command_body:
    doc: |
      Standard CMD/LEN/PAYLOAD/CHKSUM body used by all non-magic frames.
      The payload type is determined by both the direction (DIR) and the command
      identifier (CMD): switch key = dir * 256 + cmd, so 0xf1xx = TX and 0xf0xx = RX.
    seq:
      - id: cmd
        type: u1
        enum: command_id
        doc: Command / register identifier.
      - id: length
        type: u1
        doc: Byte length of the payload field.
      - id: payload
        size: length
        doc: |
          Payload interpretation depends on direction and command.
          TX queries (host→device) carry a single 0x00 placeholder byte (query_payload).
          TX writes carry the value to set (float32 or byte).
          RX responses carry the requested data.
          RX pushes are unsolicited device→host measurements.
        type:
          switch-on: '_parent.dir.to_i * 256 + cmd.to_i'
          cases:
            # -----------------------------------------------------------------
            # TX — host→device (DIR = 0xf1)
            # -----------------------------------------------------------------
            0xf100: connect_payload        # connect_ctrl  TX: connect / disconnect
            0xf1c1: float32_payload        # set_voltage   TX: set output voltage [V]
            0xf1c2: float32_payload        # set_current   TX: set current limit [A]
            0xf1db: output_enable_payload  # set_output    TX: enable / disable output
            0xf1de: query_payload          # get_device_name TX query (data = 0x00)
            0xf1df: query_payload          # get_fw_version  TX query
            0xf1e0: query_payload          # get_hw_version  TX query
            0xf1e1: query_payload          # ready_status    TX query (GET_READY poll)
            0xf1ff: query_payload          # get_full_status TX query
            # -----------------------------------------------------------------
            # RX — device→host (DIR = 0xf0)
            # -----------------------------------------------------------------
            0xf000: connect_payload        # connect_ctrl  RX: device echo
            0xf0c0: float32_payload        # push_vin_a    RX: input voltage measurement A [V]
            0xf0c1: float32_payload        # set_voltage   RX: device echo [V]
            0xf0c2: float32_payload        # set_current   RX: device echo [A]
            0xf0c3: push_output_payload    # push_output   RX: unsolicited Vout/Iout/Pout push
            0xf0c4: float32_payload        # push_vin_c    RX: input voltage measurement C [V]
            0xf0db: output_enable_payload  # set_output    RX: device echo
            0xf0de: string_payload         # get_device_name RX: ASCII device name
            0xf0df: string_payload         # get_fw_version  RX: ASCII firmware version
            0xf0e0: string_payload         # get_hw_version  RX: ASCII hardware version
            0xf0e1: ready_payload          # ready_status    RX: device ready flag
            0xf0e2: float32_payload        # push_vin_b    RX: input voltage measurement B [V]
            0xf0e3: float32_payload        # push_max_current RX: maximum current [A]
            0xf0ff: full_status_payload    # get_full_status  RX: full status blob
      - id: checksum
        type: u1
        doc: |
          (CMD + LEN + Σ DATA bytes) mod 256. Confirmed by capture analysis.

  # ---------------------------------------------------------------------------
  # Payload types
  # ---------------------------------------------------------------------------
  query_payload:
    doc: |
      TX query frame payload (LEN=1, DATA=0x00).
      The host sends this to request a response; the device replies with a frame
      using the same CMD code but with actual data (DIR=0xf0).
    seq:
      - id: reserved
        type: u1
        doc: Always 0x00.

  output_enable_payload:
    doc: |
      Payload for CMD set_output (0xdb).
      TX: DATA = 0x01 → enable output, DATA = 0x00 → disable output.
      RX: device echoes the full frame back with START = 0xa1.
      Confirmed from capture dps150_connect_enable_out_set_v_set_i_disable_disconnect.txt.
    seq:
      - id: state
        type: u1
        enum: output_state

  connect_payload:
    doc: |
      Payload for CMD connect_ctrl (0x00).
      TX: DATA = 0x01 → connect, DATA = 0x00 → disconnect.
      RX: device echoes the connect/disconnect state.
    seq:
      - id: state
        type: u1
        enum: connect_state

  ready_payload:
    doc: |
      RX payload for CMD ready_status (0xe1).
      Device responds to a GET_READY query with this payload.
    seq:
      - id: ready
        type: u1
        doc: 0x01 = device ready, 0x00 = not ready.

  string_payload:
    doc: |
      RX payload for string response commands (device name, HW/FW version).
      Variable-length ASCII string (no NUL terminator).
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
      RX payload for CMD push_output (0xc3) — periodic measurement push (LEN=12).
      The device emits these unsolicited roughly every 600 ms during an active session.
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
      RX payload for CMD get_full_status (0xff) — full status blob (LEN=0x8b = 139 bytes).
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
  direction:
    0xf0: device_to_host
    0xf1: host_to_device

  start_byte:
    0xa1: query_or_response
    0xb0: start_session_magic
    0xb1: write_command
    0xc1: connect_ctrl

  command_id:
    0x00:
      id: connect_ctrl
      doc: "Connect/disconnect control. DATA=0x01 connect, 0x00 disconnect."
      -x-direction: host_to_device
      -x-response: none
    0xc0:
      id: push_vin_a
      doc: "Unsolicited push: input voltage channel A [V]."
      -x-direction: device_to_host
      -x-response: unsolicited
    0xc1:
      id: set_voltage
      doc: "Set output voltage [V] as float32. Fire-and-forget."
      -x-direction: host_to_device
      -x-response: none
    0xc2:
      id: set_current
      doc: "Set current limit [A] as float32. Fire-and-forget."
      -x-direction: host_to_device
      -x-response: none
    0xc3:
      id: push_output
      doc: "Unsolicited push: Vout [V], Iout [A], Pout [W]."
      -x-direction: device_to_host
      -x-response: unsolicited
    0xc4:
      id: push_vin_c
      doc: "Unsolicited push: boost rail voltage [V]."
      -x-direction: device_to_host
      -x-response: unsolicited
    0xdb:
      id: set_output
      doc: "Enable/disable output. Device echoes the frame with START=0xa1."
      -x-direction: host_to_device
      -x-response: set_output
    0xde:
      id: get_device_name
      doc: "Query device name. Response is ASCII string e.g. 'DPS-150'."
      -x-direction: host_to_device
      -x-response: get_device_name
    0xdf:
      id: get_fw_version
      doc: "Query firmware version. Response is ASCII string e.g. 'V1.0'."
      -x-direction: host_to_device
      -x-response: get_fw_version
    0xe0:
      id: get_hw_version
      doc: "Query hardware version. Response is ASCII string e.g. 'V1.2'."
      -x-direction: host_to_device
      -x-response: get_hw_version
    0xe1:
      id: ready_status
      doc: "TX: query device ready (DATA=0x00). RX: ready=1 when device is initialized."
      -x-direction: bidirectional
      -x-response: ready_status
    0xe2:
      id: push_vin_b
      doc: "Unsolicited push: alternate input voltage measurement [V]."
      -x-direction: device_to_host
      -x-response: unsolicited
    0xe3:
      id: push_max_current
      doc: "Unsolicited push: device maximum current constant (5.1 A)."
      -x-direction: device_to_host
      -x-response: unsolicited
    0xff:
      id: get_full_status
      doc: "Query full status blob. Response is 139-byte full_status_payload."
      -x-direction: host_to_device
      -x-response: get_full_status

  connect_state:
    0x00: disconnect
    0x01: connect

  output_state:
    0x00: disabled
    0x01: enabled
