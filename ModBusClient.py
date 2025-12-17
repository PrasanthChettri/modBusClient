#!/usr/bin/env python3
# Simple Modbus TCP read-holding-registers request (reads registers 1-4)
# Replace HOST with your slave IP (and adjust UNIT_ID/PORT if needed).

import socket
import struct
from enum import Enum

from ModBusRequest import ModBusRequest, RequestType
from ModBusResponse import ModBusResponse

class ModBusClient():
    def __init__(self, host, port=502, unit_id=1, timeout=5):
        self.host = host
        self.port = port
        self.unit_id = unit_id
        self.timeout = timeout
        self.socket = None

    def connect(self):
        flag = True
        try :
            self.sock = socket.create_connection((self.host, self.port), timeout=self.timeout)
        except Exception as e:
            print(f"Connection to {self.host}:{self.port} failed: {e}")
            flag = False
        return flag

    def disconnect(self):
        if self.sock:
            self.sock.close()
            self.sock = None


    @staticmethod
    def _parse_response(response: bytes) -> ModBusResponse:
        return ModBusResponse.from_bytes(response)

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

    def send_request(self, request: ModBusRequest, **kwargs) -> ModBusResponse:
        """
        Send a Modbus TCP Read Holding Registers (function 0x03) request and
        return the parsed response.

        start_register: 1-based register number (human-readable). This function
                        converts it to 0-based address used by Modbus protocol.
        count: number of registers to read.
        """

        self.sock.sendall(request.bytes)
        response_bytes = self.get_response()
        print("Sent (bytes):", request)
        print("Sent (hex):", request.hex)
        print("Received (bytes):", response_bytes)
        print("Received (hex):", response_bytes.hex())
        return self._parse_response(response_bytes)
    

if __name__ == "__main__":
    HOST = "127.0.0.1"   # <-- replace with Modbus slave IP
    PORT = 502
    UNIT_ID = 1
    V = ModBusClient(HOST, port=PORT, unit_id=UNIT_ID)
    V.connect()
    request = ModBusRequest(RequestType.readHoldingRegisters, start_register=1, count=4)
    print(V.send_request(request))
    V.disconnect()
    # Read holding registers 1..4 (human numbering)
    #resp = read_holding_regs_tcp(HOST, port=PORT, unit_id=UNIT_ID, start_register=1, count=4)
