#!/usr/bin/env python3
# Simple Modbus TCP read-holding-registers request (reads registers 1-4)
# Replace HOST with your slave IP (and adjust UNIT_ID/PORT if needed).

import socket
import struct
from enum import Enum

from modbus_request import ModBusRequest, RequestType
from modbus_response import ModBusResponse

class ModBusClient():
    def __init__(self, host, port=502, unit_id=1, timeout=5):
        self.host = host
        self.port = port
        self.unit_id = unit_id
        self.timeout = timeout
        self.sock = None

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

    def send_request(self, request: ModBusRequest, **kwargs) -> ModBusResponse:
        """
        Send a Modbus TCP Read Holding Registers (function 0x03) request and
        return the parsed response.

        start_register: 1-based register number (human-readable). This function
                        converts it to 0-based address used by Modbus protocol.
        count: number of registers to read.
        """

        self.sock.sendall(request.bytes)
        response = ModBusResponse.get_response(self.sock)
        print("Sent (bytes):", request)
        print("Sent (hex):", request.hex)
        print("Received (bytes):", response.bytes)
        print("Received (hex):", response.hex)
    

if __name__ == "__main__":
    HOST = "127.0.0.1"   # <-- replace with Modbus slave IP
    PORT = 502
    UNIT_ID = 1
    V = ModBusClient(HOST, port=PORT, unit_id=UNIT_ID)
    print(V.connect())
    request = ModBusRequest(RequestType.readHoldingRegisters, start_register=1, count=4)
    print(request)
    print(V.send_request(request))
    V.disconnect()
    # Read holding registers 1..4 (human numbering)
    #resp = read_holding_regs_tcp(HOST, port=PORT, unit_id=UNIT_ID, start_register=1, count=4)
