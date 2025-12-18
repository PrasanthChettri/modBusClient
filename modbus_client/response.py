from ast import List
import struct

class ModBusResponse:
    ## BYTE_ORDER is BIG ENDIAN
    VAL_SIZE = 2 # Size of each register value in bytes # 16 bit data per register
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
        assert len(self.data) % __class__.VAL_SIZE == 0, f"DATA LENGTH MISMATCH, {self.__repr__()}"
        self.cache = {} 


    @property
    def register_values(self) -> List[int]:
        if "register_values" in self.cache :
            return self.cache["register_values"]
        registers = []

        for i in range(0, len(self.data), __class__.VAL_SIZE):
            register_value = int.from_bytes(self.data[i:i+__class__.VAL_SIZE], byteorder='big')
            registers.append(register_value)
        self.cache["register_values"] = registers
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