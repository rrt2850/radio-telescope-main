import serial
import threading
import time

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

            cmd = f"G{az:.5f}e{alt:.5f};"
            self.ser.write(cmd.encode("ascii"))

            self.waitForDone()

            return cmd

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
