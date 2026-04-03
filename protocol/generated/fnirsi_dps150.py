# This is a generated file! Please edit source .ksy file and use kaitai-struct-compiler to rebuild
# type: ignore

import kaitaistruct
from kaitaistruct import KaitaiStruct, KaitaiStream, BytesIO
from enum import IntEnum


if getattr(kaitaistruct, 'API_VERSION', (0, 9)) < (0, 11):
    raise Exception("Incompatible Kaitai Struct Python API: 0.11 or later is required, but you have %s" % (kaitaistruct.__version__))

class FnirsiDps150(KaitaiStruct):

    class CommandId(IntEnum):
        connect_ctrl = 0
        push_vin_a = 192
        set_voltage = 193
        set_current = 194
        push_output = 195
        push_vin_c = 196
        set_output = 219
        get_device_name = 222
        get_fw_version = 223
        get_hw_version = 224
        ready_status = 225
        push_vin_b = 226
        push_max_current = 227
        get_full_status = 255

    class ConnectState(IntEnum):
        disconnect = 0
        connect = 1

    class OutputState(IntEnum):
        disabled = 0
        enabled = 1

    class StartByte(IntEnum):
        query_or_response = 161
        start_session_magic = 176
        write_command = 177
        connect_ctrl = 193
    def __init__(self, _io, _parent=None, _root=None):
        super(FnirsiDps150, self).__init__(_io)
        self._parent = _parent
        self._root = _root or self
        self._read()

    def _read(self):
        self.frame = FnirsiDps150.Frame(self._io, self, self._root)


    def _fetch_instances(self):
        pass
        self.frame._fetch_instances()

    class ConnectPayload(KaitaiStruct):
        """Payload for CMD connect_ctrl (0x00).
        DATA = 0x01 → connect, DATA = 0x00 → disconnect.
        """
        def __init__(self, _io, _parent=None, _root=None):
            super(FnirsiDps150.ConnectPayload, self).__init__(_io)
            self._parent = _parent
            self._root = _root
            self._read()

        def _read(self):
            self.state = KaitaiStream.resolve_enum(FnirsiDps150.ConnectState, self._io.read_u1())


        def _fetch_instances(self):
            pass


    class Float32Payload(KaitaiStruct):
        """Single IEEE 754 32-bit LE float (voltage in V or current in A)."""
        def __init__(self, _io, _parent=None, _root=None):
            super(FnirsiDps150.Float32Payload, self).__init__(_io)
            self._parent = _parent
            self._root = _root
            self._read()

        def _read(self):
            self.value = self._io.read_f4le()


        def _fetch_instances(self):
            pass


    class Frame(KaitaiStruct):
        """Top-level protocol frame."""
        def __init__(self, _io, _parent=None, _root=None):
            super(FnirsiDps150.Frame, self).__init__(_io)
            self._parent = _parent
            self._root = _root
            self._read()

        def _read(self):
            self.start = KaitaiStream.resolve_enum(FnirsiDps150.StartByte, self._io.read_u1())
            self.cmd = KaitaiStream.resolve_enum(FnirsiDps150.CommandId, self._io.read_u1())
            self.length = self._io.read_u1()
            _on = self.cmd
            if _on == FnirsiDps150.CommandId.connect_ctrl:
                pass
                self._raw_payload = self._io.read_bytes(self.length)
                _io__raw_payload = KaitaiStream(BytesIO(self._raw_payload))
                self.payload = FnirsiDps150.ConnectPayload(_io__raw_payload, self, self._root)
            elif _on == FnirsiDps150.CommandId.get_device_name:
                pass
                self._raw_payload = self._io.read_bytes(self.length)
                _io__raw_payload = KaitaiStream(BytesIO(self._raw_payload))
                self.payload = FnirsiDps150.StringPayload(_io__raw_payload, self, self._root)
            elif _on == FnirsiDps150.CommandId.get_full_status:
                pass
                self._raw_payload = self._io.read_bytes(self.length)
                _io__raw_payload = KaitaiStream(BytesIO(self._raw_payload))
                self.payload = FnirsiDps150.FullStatusPayload(_io__raw_payload, self, self._root)
            elif _on == FnirsiDps150.CommandId.get_fw_version:
                pass
                self._raw_payload = self._io.read_bytes(self.length)
                _io__raw_payload = KaitaiStream(BytesIO(self._raw_payload))
                self.payload = FnirsiDps150.StringPayload(_io__raw_payload, self, self._root)
            elif _on == FnirsiDps150.CommandId.get_hw_version:
                pass
                self._raw_payload = self._io.read_bytes(self.length)
                _io__raw_payload = KaitaiStream(BytesIO(self._raw_payload))
                self.payload = FnirsiDps150.StringPayload(_io__raw_payload, self, self._root)
            elif _on == FnirsiDps150.CommandId.push_max_current:
                pass
                self._raw_payload = self._io.read_bytes(self.length)
                _io__raw_payload = KaitaiStream(BytesIO(self._raw_payload))
                self.payload = FnirsiDps150.Float32Payload(_io__raw_payload, self, self._root)
            elif _on == FnirsiDps150.CommandId.push_output:
                pass
                self._raw_payload = self._io.read_bytes(self.length)
                _io__raw_payload = KaitaiStream(BytesIO(self._raw_payload))
                self.payload = FnirsiDps150.PushOutputPayload(_io__raw_payload, self, self._root)
            elif _on == FnirsiDps150.CommandId.push_vin_a:
                pass
                self._raw_payload = self._io.read_bytes(self.length)
                _io__raw_payload = KaitaiStream(BytesIO(self._raw_payload))
                self.payload = FnirsiDps150.Float32Payload(_io__raw_payload, self, self._root)
            elif _on == FnirsiDps150.CommandId.push_vin_b:
                pass
                self._raw_payload = self._io.read_bytes(self.length)
                _io__raw_payload = KaitaiStream(BytesIO(self._raw_payload))
                self.payload = FnirsiDps150.Float32Payload(_io__raw_payload, self, self._root)
            elif _on == FnirsiDps150.CommandId.push_vin_c:
                pass
                self._raw_payload = self._io.read_bytes(self.length)
                _io__raw_payload = KaitaiStream(BytesIO(self._raw_payload))
                self.payload = FnirsiDps150.Float32Payload(_io__raw_payload, self, self._root)
            elif _on == FnirsiDps150.CommandId.ready_status:
                pass
                self._raw_payload = self._io.read_bytes(self.length)
                _io__raw_payload = KaitaiStream(BytesIO(self._raw_payload))
                self.payload = FnirsiDps150.ReadyPayload(_io__raw_payload, self, self._root)
            elif _on == FnirsiDps150.CommandId.set_current:
                pass
                self._raw_payload = self._io.read_bytes(self.length)
                _io__raw_payload = KaitaiStream(BytesIO(self._raw_payload))
                self.payload = FnirsiDps150.Float32Payload(_io__raw_payload, self, self._root)
            elif _on == FnirsiDps150.CommandId.set_output:
                pass
                self._raw_payload = self._io.read_bytes(self.length)
                _io__raw_payload = KaitaiStream(BytesIO(self._raw_payload))
                self.payload = FnirsiDps150.OutputEnablePayload(_io__raw_payload, self, self._root)
            elif _on == FnirsiDps150.CommandId.set_voltage:
                pass
                self._raw_payload = self._io.read_bytes(self.length)
                _io__raw_payload = KaitaiStream(BytesIO(self._raw_payload))
                self.payload = FnirsiDps150.Float32Payload(_io__raw_payload, self, self._root)
            else:
                pass
                self.payload = self._io.read_bytes(self.length)
            self.checksum = self._io.read_u1()


        def _fetch_instances(self):
            pass
            _on = self.cmd
            if _on == FnirsiDps150.CommandId.connect_ctrl:
                pass
                self.payload._fetch_instances()
            elif _on == FnirsiDps150.CommandId.get_device_name:
                pass
                self.payload._fetch_instances()
            elif _on == FnirsiDps150.CommandId.get_full_status:
                pass
                self.payload._fetch_instances()
            elif _on == FnirsiDps150.CommandId.get_fw_version:
                pass
                self.payload._fetch_instances()
            elif _on == FnirsiDps150.CommandId.get_hw_version:
                pass
                self.payload._fetch_instances()
            elif _on == FnirsiDps150.CommandId.push_max_current:
                pass
                self.payload._fetch_instances()
            elif _on == FnirsiDps150.CommandId.push_output:
                pass
                self.payload._fetch_instances()
            elif _on == FnirsiDps150.CommandId.push_vin_a:
                pass
                self.payload._fetch_instances()
            elif _on == FnirsiDps150.CommandId.push_vin_b:
                pass
                self.payload._fetch_instances()
            elif _on == FnirsiDps150.CommandId.push_vin_c:
                pass
                self.payload._fetch_instances()
            elif _on == FnirsiDps150.CommandId.ready_status:
                pass
                self.payload._fetch_instances()
            elif _on == FnirsiDps150.CommandId.set_current:
                pass
                self.payload._fetch_instances()
            elif _on == FnirsiDps150.CommandId.set_output:
                pass
                self.payload._fetch_instances()
            elif _on == FnirsiDps150.CommandId.set_voltage:
                pass
                self.payload._fetch_instances()
            else:
                pass


    class FullStatusPayload(KaitaiStruct):
        """CMD 0xff – full status blob (LEN=0x8b = 139 bytes).
        Offsets 0–95: 24 floats.  Offsets 96–138: mixed types (TBD).
        """
        def __init__(self, _io, _parent=None, _root=None):
            super(FnirsiDps150.FullStatusPayload, self).__init__(_io)
            self._parent = _parent
            self._root = _root
            self._read()

        def _read(self):
            self.vin = self._io.read_f4le()
            self.vset = self._io.read_f4le()
            self.iset = self._io.read_f4le()
            self.vout = self._io.read_f4le()
            self.iout = self._io.read_f4le()
            self.pout = self._io.read_f4le()
            self.vin2 = self._io.read_f4le()
            self.vset2 = self._io.read_f4le()
            self.iset2 = self._io.read_f4le()
            self.presets = []
            for i in range(5):
                self.presets.append(FnirsiDps150.Preset(self._io, self, self._root))

            self.max_voltage = self._io.read_f4le()
            self.max_current = self._io.read_f4le()
            self.max_power = self._io.read_f4le()
            self.max_temp = self._io.read_f4le()
            self.unknown_f = self._io.read_f4le()
            self.remainder = self._io.read_bytes_full()


        def _fetch_instances(self):
            pass
            for i in range(len(self.presets)):
                pass
                self.presets[i]._fetch_instances()



    class OutputEnablePayload(KaitaiStruct):
        """Payload for CMD set_output (0xdb).
        DATA = 0x01 → enable output, DATA = 0x00 → disable output.
        The device echoes the full frame back with START = 0xa1.
        Confirmed from capture dps150_connect_enable_out_set_v_set_i_disable_disconnect.txt.
        """
        def __init__(self, _io, _parent=None, _root=None):
            super(FnirsiDps150.OutputEnablePayload, self).__init__(_io)
            self._parent = _parent
            self._root = _root
            self._read()

        def _read(self):
            self.state = KaitaiStream.resolve_enum(FnirsiDps150.OutputState, self._io.read_u1())


        def _fetch_instances(self):
            pass


    class Preset(KaitaiStruct):
        """One stored preset (Vset + Iset pair)."""
        def __init__(self, _io, _parent=None, _root=None):
            super(FnirsiDps150.Preset, self).__init__(_io)
            self._parent = _parent
            self._root = _root
            self._read()

        def _read(self):
            self.vset = self._io.read_f4le()
            self.iset = self._io.read_f4le()


        def _fetch_instances(self):
            pass


    class PushOutputPayload(KaitaiStruct):
        """CMD 0xc3 – periodic output measurement push (LEN=12, three floats).
        All values are 0.0 when output is disabled.
        """
        def __init__(self, _io, _parent=None, _root=None):
            super(FnirsiDps150.PushOutputPayload, self).__init__(_io)
            self._parent = _parent
            self._root = _root
            self._read()

        def _read(self):
            self.vout = self._io.read_f4le()
            self.iout = self._io.read_f4le()
            self.pout = self._io.read_f4le()


        def _fetch_instances(self):
            pass


    class ReadyPayload(KaitaiStruct):
        """Device ready status (CMD 0xe1)."""
        def __init__(self, _io, _parent=None, _root=None):
            super(FnirsiDps150.ReadyPayload, self).__init__(_io)
            self._parent = _parent
            self._root = _root
            self._read()

        def _read(self):
            self.ready = self._io.read_u1()


        def _fetch_instances(self):
            pass


    class StringPayload(KaitaiStruct):
        """Variable-length ASCII string (no NUL terminator)."""
        def __init__(self, _io, _parent=None, _root=None):
            super(FnirsiDps150.StringPayload, self).__init__(_io)
            self._parent = _parent
            self._root = _root
            self._read()

        def _read(self):
            self.value = (self._io.read_bytes_full()).decode(u"ASCII")


        def _fetch_instances(self):
            pass



