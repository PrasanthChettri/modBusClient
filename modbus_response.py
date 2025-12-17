import struct

class ModBusResponse:
    def __init__(self, bytes, transaction_id: int, protocol_id: int, length: int, unit_id: int, function_code: int, byte_count: int, data: bytes):
        self.response_bytes = bytes
        self.transaction_id = transaction_id
        self.protocol_id = protocol_id
        self.length = length
        self.unit_id = unit_id
        self.function_code = function_code
        self.byte_count = byte_count
        self.data = data

    @staticmethod
    def get_response(sock) -> ModBusResponse:
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
        return __class__.from_bytes(response)

    @staticmethod
    def from_bytes(response_bytes: bytes) -> 'ModBusResponse':
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