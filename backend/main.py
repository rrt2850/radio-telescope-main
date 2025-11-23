# backend/main.py
from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from robutils import CoordsTo
import serial

class PointRequest(BaseModel):
    ra: float
    dec: float

app = FastAPI(
    title="Radio Telescope Control API",
    description="Backend API to compute telescope movement and send commands to the Arduino",
)

# Telescope coordinates
LAT = 43.082149
LONG = -77.675936
HEIGHT = 204.37
MIN_ANGLE = 15
MAX_ANGLE = 165

# Try opening the serial port on startup
try:
    arduino = serial.Serial('/dev/ttyACM0', 115200, timeout=0.1)
    print("[INFO] Arduino connected on /dev/ttyACM0")
except Exception as e:
    print(f"[WARNING] Could not open serial port: {e}")
    arduino = None


def SendToArduino(az: float, alt: float):
    """
    Send azimuth/altitude to the Arduino.
    Raise an error if Arduino is not connected.
    """
    if arduino is None:
        try:
            arduino = serial.Serial('/dev/ttyACM0', 115200, timeout=0.1)
        except:
            raise RuntimeError("Arduino serial connection is not available.")

    command = f"G{az:.5f}e{alt:.5f};"
    arduino.write(command.encode("ascii"))
    return command


@app.post("/point")
def Point(req: PointRequest):
    ra = req.ra
    dec = req.dec
    """
    Convert RA/DEC to AZ/ALT and send movement command to Arduino.
    """
    # Ensure Arduino is available before computing anything
    if arduino is None:
        return JSONResponse(
            status_code=500,
            content={"error": "Arduino not connected. Cannot send movement command."}
        )
    try:
        az, alt = CoordsTo(LAT, LONG, HEIGHT, ra, dec)
    except:
        return JSONResponse(
            status_code=500,
            content={"error": "Invalid coordinates", "detail": str(e)}
        )

    # Safety checks
    if alt < MIN_ANGLE:
        return JSONResponse(
            status_code=400,
            content={"error": f"Target altitude {alt:.2f}° is below the minimum allowed {MIN_ANGLE}°."}
        )

    if alt > MAX_ANGLE:
        return JSONResponse(
            status_code=400,
            content={"error": f"Target altitude {alt:.2f}° is above the maximum allowed {MAX_ANGLE}°."}
        )

    # Attempt to send to Arduino
    try:
        command = SendToArduino(az, alt)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": "Failed to send serial command", "detail": str(e)}
        )

    return {"az": az, "alt": alt, "sent": command}
