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
    def __repr__(self):
        return f"ModBusResponse(transaction_id={self.transaction_id}, protocol_id={self.protocol_id}, length={self.length}, unit_id={self.unit_id}, function_code={self.function_code}, byte_count={self.byte_count}, data={self.data.hex()})"