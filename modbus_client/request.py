from enum import Enum
import struct

class RequestType(Enum):
    readHoldingRegisters = 0x03

class ModBusRequest():
    REQUEST_FRAME_SIZE = 12

    def __init__(self, RequestType, start_register: int, count: int, timeout: int = 5, unit_id: int = 1):
        self.request_type = RequestType
        self.start_register = start_register
        self.count = count
        self.timeout = timeout
        self.unit_id = unit_id
        self.cache = {}

    @staticmethod
    def _parse_request(requestType: RequestType, timeout, unit_id, **kwargs) -> bytes:
        start_addr = kwargs["start_register"] - 1
        transaction_id = 1       
        protocol_id = 0          # Modbus protocol

        # Build PDU: Function (1 byte) + Start Addr (2 bytes) + Quantity (2 bytes)
        pdu = struct.pack('>BHH', RequestType.readHoldingRegisters.value, start_addr, kwargs["count"])

        # MBAP header: Transaction ID (2) | Protocol ID (2) | Length (2) | Unit ID (1)
        # Length = number of following bytes (Unit ID + PDU)
        length = len(pdu) + 1
        mbap = struct.pack('>HHHB', transaction_id, protocol_id, length, unit_id)

        request = mbap + pdu
        return request

    @property
    def hex(self) -> str:
        if "hex" in self.cache :
            return self.cache["hex"]
        self.cache["hex"] = self.bytes.hex()
        return self.cache["hex"]

    @property
    def bytes(self) -> bytes:
        if "bytes" in self.cache :
            return self.cache["bytes"]
        self.cache["bytes"] = self._parse_request(self.request_type, 
                                    unit_id=self.unit_id, timeout=self.timeout,
                                    start_register=self.start_register,
                                    count=self.count)
        return self.cache["bytes"]
    def __repr__(self):
        return f"ModBusRequest(type={self.request_type}, start_register={self.start_register}, count={self.count}, unit_id={self.unit_id}, timeout={self.timeout})"