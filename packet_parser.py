#!/usr/bin/env python3
# Simple Modbus TCP read-holding-registers request (reads registers 1-4)
# Replace HOST with your slave IP (and adjust UNIT_ID/PORT if needed).

import socket
import struct
from enum import Enum

class RequestType(Enum):
    readHoldingRegisters = 0x03


class ModBusClient():
    def __init__(self, host, port=502, unit_id=1, timeout=5):
        self.host = host
        self.port = port
        self.unit_id = unit_id
        self.timeout = timeout
        self.socket = None

    def connect(self):
        self.sock = socket.create_connection((self.host, self.port), timeout=self.timeout)

    def disconnect(self):
        if self.sock:
            self.sock.close()
            self.sock = None

    def send_request(self, request : bytes):
        if not self.sock:
            self.connect()
        self.sock.sendall(request)


    @staticmethod
    def _parse_request(requestType: RequestType, timeout, unit_id, **kwargs) -> bytes:
        start_addr = kwargs["start_register"] - 1
        transaction_id = 1       # arbitrary; increment if doing multiple requests
        protocol_id = 0          # Modbus protocol

        # Build PDU: Function (1 byte) + Start Addr (2 bytes) + Quantity (2 bytes)
        pdu = struct.pack('>BHH', RequestType.readHoldingRegisters.value, start_addr, kwargs["count"])

        # MBAP header: Transaction ID (2) | Protocol ID (2) | Length (2) | Unit ID (1)
        # Length = number of following bytes (Unit ID + PDU)
        length = len(pdu) + 1
        mbap = struct.pack('>HHHB', transaction_id, protocol_id, length, unit_id)

        request = mbap + pdu
        return request

    @staticmethod
    def _parse_response(response: bytes) -> dict:
        pass

    def get_response(self) -> bytes:
        mbap_resp = b''
        while len(mbap_resp) < 7:
            chunk = self.sock.recv(7 - len(mbap_resp))
            if not chunk:
                raise ConnectionError("Connection closed while reading MBAP header")
            mbap_resp += chunk

        # Unpack MBAP header to get remaining length
        tid, pid, length_field, unit = struct.unpack('>HHHB', mbap_resp)
        # length_field includes Unit ID (1) + remaining PDU bytes
        remaining_pdu_len = length_field - 1
        pdu_resp = b''
        while len(pdu_resp) < remaining_pdu_len:
            chunk = self.sock.recv(remaining_pdu_len - len(pdu_resp))
            if not chunk:
                raise ConnectionError("Connection closed while reading PDU")
            pdu_resp += chunk

        response = mbap_resp + pdu_resp
        return response

    def send_request(self, requestType : RequestType, **kwargs) -> bytes:
        """
        Send a Modbus TCP Read Holding Registers (function 0x03) request and
        return the raw response bytes.

        start_register: 1-based register number (human-readable). This function
                        converts it to 0-based address used by Modbus protocol.
        count: number of registers to read.
        """
        # Convert to 0-based address for protocol
        request = self._parse_request(requestType, self.timeout, self.unit_id, **kwargs)
        # Send request and read full response (read MBAP first to know length)
        self.sock.sendall(request)
        # Read MBAP header (7 bytes)
        response = self.get_response()
        # Print results (raw byte array and hex)
        print("Sent (bytes):", request)
        print("Sent (hex):", request.hex())
        print("Received (bytes):", response)
        print("Received (hex):", response.hex())

        return response
    

if __name__ == "__main__":
    HOST = "127.0.0.1"   # <-- replace with Modbus slave IP
    PORT = 502
    UNIT_ID = 1
    V = ModBusClient(HOST, port=PORT, unit_id=UNIT_ID)
    V.connect()
    V.send_request(RequestType.readHoldingRegisters, start_register=1, count=4)
    V.disconnect()
    # Read holding registers 1..4 (human numbering)
    #resp = read_holding_regs_tcp(HOST, port=PORT, unit_id=UNIT_ID, start_register=1, count=4)
