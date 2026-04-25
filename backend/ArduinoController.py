import serial
import threading
import time
import re

class ArduinoController:
    def __init__(self, port: str, baudrate: int = 115200, timeout: float = 0.1):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.ser: serial.Serial | None = None
        self.serialLock = threading.Lock()  # protects access to self.ser

    def Connect(self):
        with self.serialLock:
            if self.ser is None or not self.ser.is_open:
                self.ser = serial.Serial(self.port, self.baudrate, timeout=self.timeout)
                print(f"[INFO] Arduino connected on {self.port}")

    def IsConnected(self) -> bool:
        return self.ser is not None and self.ser.is_open

    def Close(self):
        with self.serialLock:
            if self.ser is not None and self.ser.is_open:
                print("[INFO] Closing Arduino serial connection")
                self.ser.close()

    def SendPoint(self, az: float, alt: float) -> str:
        """
        Send a pointing command to the Arduino.
        """
        with self.serialLock:
            if not self.IsConnected():
                raise RuntimeError("Arduino not connected")

            cmd = f"G{alt:.5f}e{az:.5f};"
            self.ser.write(cmd.encode("ascii"))

            self.waitForDone()

            return cmd

    def GetCurrentPointing(self, timeout: float = 2.0) -> dict[str, float]:
        """
        Query the Arduino for its current pointing and return {'alt': float, 'az': float}.
        Expected response format: POS alt=<altitude_degrees> az=<azimuth_degrees>
        """
        with self.serialLock:
            if not self.IsConnected():
                raise RuntimeError("Arduino not connected")

            self.ser.reset_input_buffer()
            self.ser.write(b"P;")

            deadline = time.time() + timeout
            while time.time() < deadline:
                line = self.ser.readline()
                if not line:
                    continue

                decoded = line.decode("ascii", errors="ignore").strip()
                match = re.search(r"POS alt=([-+]?\d*\.?\d+)\s+az=([-+]?\d*\.?\d+)", decoded)
                if match:
                    return {
                        "alt": float(match.group(1)),
                        "az": float(match.group(2)),
                    }

            raise TimeoutError("Timed out waiting for Arduino position response")

    def waitForDone(self, timeout: float = 180.0):
        """
        Block until the Arduino reports that the move is finished.
        """
        if not self.IsConnected():
            raise RuntimeError("Arduino not connected")

        deadline = time.time() + timeout

        # Loop until deadline or DONE.
        while time.time() < deadline:
            line = self.ser.readline()
            if not line:
                continue

            if b"DONE" in line:
                return

        raise TimeoutError("Timed out waiting for Arduino to finish movement")
