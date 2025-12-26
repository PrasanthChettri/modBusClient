from ast import List
import struct
from enum import Enum, auto

class RegisterValueType(Enum):
    # Enum values are auto() to ensure unique identity (prevents aliasing)
    INT16 = auto()
    UINT16 = auto()
    INT32 = auto()
    UINT32 = auto()
    FLOAT32 = auto()
    INT64 = auto()
    UINT64 = auto()
    FLOAT64 = auto()  # Double precision

    @property
    def byte_len(self) -> int:
        """Return the byte length for the register type."""
        if self in (RegisterValueType.INT16, RegisterValueType.UINT16):
            return 2
        elif self in (RegisterValueType.INT32, RegisterValueType.UINT32, RegisterValueType.FLOAT32):
            return 4
        elif self in (RegisterValueType.INT64, RegisterValueType.UINT64, RegisterValueType.FLOAT64):
            return 8
        else:
            raise ValueError(f"Byte length undefined for {self.name}")

    @property
    def format_char(self) -> str:
        """Return the struct format character for unpacking."""
        mapping = {
            RegisterValueType.INT16: 'h',   # short
            RegisterValueType.UINT16: 'H',  # unsigned short
            RegisterValueType.INT32: 'i',   # int
            RegisterValueType.UINT32: 'I',  # unsigned int
            RegisterValueType.FLOAT32: 'f', # float
            RegisterValueType.INT64: 'q',   # long long
            RegisterValueType.UINT64: 'Q',  # unsigned long long
            RegisterValueType.FLOAT64: 'd', # double
        }
        return mapping[self]

class ModBusResponse:
    ## BYTE_ORDER is BIG ENDIAN
    def __init__(self, bytes, transaction_id: int, protocol_id: int, length: int, unit_id: int, function_code: int, byte_count: int, data: bytes):
        self.response_bytes = bytes
        self.transaction_id = transaction_id
        self.protocol_id = protocol_id
        self.length = length
        self.unit_id = unit_id
        self.function_code = function_code
        self.byte_count = byte_count # TODO: REMOVE THIS AND USE LEN(DATA)
        self.data = data
        assert self.byte_count == len(self.data), f"BYTE COUNT MISMATCH, {self.__repr__()}"
        self.cache = {} 


    def _get_value_as(self, register_val: RegisterValueType, index: int = 0) -> Union[int, float]:
        step = register_val.byte_len
        start = index * step
        end = start + step
        
        if end > len(self.data):
            raise IndexError(f"Register index {index} out of range for type {register_val.name}. "
                             f"Requires bytes {start}-{end}, but data length is {len(self.data)}")

        raw_value = self.data[start:end]
        
        # Build the struct format string: '>' (Big Endian) + format char
        fmt = '>' + register_val.format_char
        
        try:
            val = struct.unpack(fmt, raw_value)[0]
            return val
        except struct.error as e:
            raise ValueError(f"Failed to unpack {register_val.name}: {e}")

    def get_register_values(self, value_as: RegisterValueType = RegisterValueType.UINT16) -> List[Union[int, float]]:
        cache_key = f"register_values_{value_as.name}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        registers = []
        step = value_as.byte_len
        
        # Calculate how many full items fit in the data buffer
        count = len(self.data) // step
        
        for i in range(count):
            register_value = self._get_value_as(value_as, index=i)
            registers.append(register_value)
            
        self.cache[cache_key] = registers
        return registers


    @staticmethod
    def get_response(sock) -> 'ModBusResponse':
        mbap_resp = b''
        while len(mbap_resp) < 7:
            chunk = sock.recv(7 - len(mbap_resp))
            if not chunk:
                raise ConnectionError("Connection closed while reading MBAP header")
            mbap_resp += chunk

        # Unpack MBAP header to get remaining length
        tid, pid, length_field, unit = struct.unpack('>HHHB', mbap_resp)
        # length_field includes Unit ID (1) + remaining PDU bytes
        remaining_pdu_len = length_field - 1
        pdu_resp = b''
        while len(pdu_resp) < remaining_pdu_len:
            chunk = sock.recv(remaining_pdu_len - len(pdu_resp))
            if not chunk:
                raise ConnectionError("Connection closed while reading PDU")
            pdu_resp += chunk

        response = mbap_resp + pdu_resp
        assert len(response) == length_field + 6, f"Response length mismatch: {len(response)} != {length_field + 6}"

        return __class__.from_bytes(response)

    @staticmethod
    def from_bytes(response_bytes: bytes) -> 'ModBusResponse':
        """
        Parse a ModBus response from bytes.
        Converts raw bytes into a ModBusResponse object by extracting and validating
        the MBAP (ModBus Application Protocol) header and PDU (Protocol Data Unit).
        Args:
            response_bytes (bytes): The raw response bytes to parse.
        Returns:
            ModBusResponse: A ModBusResponse object containing the parsed transaction ID,
                           protocol ID, length, unit ID, function code, byte count, and data.
        Raises:
            ValueError: If response_bytes is less than 9 bytes (too short).
            ValueError: If the PDU portion is less than 2 bytes (too short).
        Notes:
            - MBAP header is 7 bytes: Transaction ID (2), Protocol ID (2), Length (2), Unit ID (1)
            - PDU starts at byte 7 and contains: Function Code (1), Byte Count (1), Data (variable)
            - Unpacking uses big-endian byte order ('>HHHB')
        """
        if len(response_bytes) < 9:
            raise ValueError("Response too short")

        # Unpack MBAP header: Transaction ID (2), Protocol ID (2), Length (2), Unit ID (1)
        transaction_id, protocol_id, length, unit_id = struct.unpack('>HHHB', response_bytes[:7])

        # PDU starts after MBAP
        pdu = response_bytes[7:]

        if len(pdu) < 2:
            raise ValueError("PDU too short")

        function_code = pdu[0]
        byte_count = pdu[1]
        data = pdu[2:2 + byte_count]

        return ModBusResponse(
            response_bytes,
            transaction_id,
            protocol_id,
            length,
            unit_id,
            function_code,
            byte_count, data
        )

    @property
    def bytes(self) -> bytes:
        return self.response_bytes

    @property
    def hex(self) -> str:
        return self.bytes.hex()

    def __repr__(self):
        return f"ModBusResponse(transaction_id={self.transaction_id}, protocol_id={self.protocol_id}, length={self.length}, unit_id={self.unit_id}, function_code={self.function_code}, byte_count={self.byte_count}, data={self.data.hex()})"


if __name__ == "__main__":

    # Simple smoke tests for register_values (uses underlying fget to pass params)
    # Test 1: single unsigned/signed 16-bit value
    data = struct.pack('>H', 1)
    resp = ModBusResponse(data, transaction_id=1, protocol_id=0, length=3, unit_id=1, function_code=3, byte_count=len(data), data=data)
    vals = resp.get_register_values(value_as= RegisterValueType.INT16)
    print("register_values (INT16):", vals)
    assert vals == [1], "INT16 parsing failed"


    # Test 2: signed negative 16-bit
    data2 = struct.pack('>h', -1)
    resp2 = ModBusResponse(data2, transaction_id=2, protocol_id=0, length=3, unit_id=1, function_code=3, byte_count=len(data2), data=data2)
    vals2 = resp2.get_register_values(value_as = RegisterValueType.INT16)
    print("register_values (INT16) negative:", vals2)
    assert vals2 == [-1], "INT16 negative parsing failed"
    # Test 3: verify IndexError for UINT16 with current implementation

    data3 = b'\x42\xf6\x3d\x71'
    resp3 = ModBusResponse(data3, transaction_id=2, protocol_id=0, length=3, unit_id=1, function_code=3, byte_count=len(data3), data=data3)
    val3 = resp3.get_register_values(value_as = RegisterValueType.FLOAT32)
    print(vals, vals2, val3)
