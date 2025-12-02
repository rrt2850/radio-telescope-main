import serial

class ArduinoController:
    def __init__(self, port: str, baudrate: int = 115200, timeout: float = 0.1):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.ser: serial.Serial | None = None

    def Connect(self):
        self.ser = serial.Serial(self.port, self.baudrate, timeout=self.timeout)
        print(f"[INFO] Arduino connected on {self.port}")

    def IsConnected(self) -> bool:
        return self.ser is not None and self.ser.is_open

    def Close(self):
        if self.ser is not None and self.ser.is_open:
            print("[INFO] Closing Arduino serial connection")
            self.ser.close()

    def SendPoint(self, az: float, alt: float) -> str:
        if not self.IsConnected():
            raise RuntimeError("Arduino not connected")

        cmd = f"G{az:.5f}e{alt:.5f};"
        self.ser.write(cmd.encode("ascii"))
        return cmd
