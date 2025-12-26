#!/usr/bin/env python3
# Simple Modbus TCP read-holding-registers request (reads registers 1-4)
# Replace HOST with your slave IP (and adjust UNIT_ID/PORT if needed).

import socket
import struct
from enum import Enum

from modbus_client.request import ModBusRequest, RequestType
from modbus_client.response import ModBusResponse

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
        Send a Modbus TCP request and return the parsed response.
        
        Supports:
        - readCoil (function 0x01): Read coil status
        - readHoldingRegisters (function 0x03): Read holding registers

        Args:
            request: ModBusRequest object with configured request type
            
        Returns:
            ModBusResponse: Parsed response from the server
        """

        self.sock.sendall(request.bytes)
        response = ModBusResponse.get_response(self.sock)
        print("Sent (bytes):", request)
        print("Sent (hex):", request.hex)
        print("Received (bytes):", response.bytes)
        print("Received (hex):", response.hex)
        return response
    
    def read_coils(self, start_coil: int, count: int) -> ModBusResponse:
        """
        Read coils (function 0x01).
        
        Args:
            start_coil: 1-based coil address
            count: Number of coils to read
            
        Returns:
            ModBusResponse: Response containing coil values
        """
        request = ModBusRequest(RequestType.readCoil, start_register=start_coil, count=count, unit_id=self.unit_id)
        return self.send_request(request)
    
    def read_holding_registers(self, start_register: int, count: int) -> ModBusResponse:
        """
        Read holding registers (function 0x03).
        
        Args:
            start_register: 1-based register address
            count: Number of registers to read
            
        Returns:
            ModBusResponse: Response containing register values
        """
        request = ModBusRequest(RequestType.readHoldingRegisters, start_register=start_register, count=count, unit_id=self.unit_id)
        return self.send_request(request)
    

if __name__ == "__main__":
    HOST = "127.0.0.1"   # <-- replace with Modbus slave IP
    PORT = 502
    UNIT_ID = 1
    V = ModBusClient(HOST, port=PORT, unit_id=UNIT_ID)
    print(V.connect())
    
    # Read holding registers
    print("\n--- Reading Holding Registers ---")
    request = ModBusRequest(RequestType.readHoldingRegisters, start_register=1, count=4)
    print(request)
    print(V.send_request(request))
    
    # Read coils
    print("\n--- Reading Coils ---")
    request = ModBusRequest(RequestType.readCoil, start_register=1, count=8)
    print(request)
    print(V.send_request(request))
    
    V.disconnect()
