from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

from robutils import CoordsTo
from ArduinoController import ArduinoController

class PointRequest(BaseModel):
    ra: float
    dec: float

app = FastAPI(title="Radio Telescope Control API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

LAT = 43.082149
LONG = -77.675936
HEIGHT = 204.37
MIN_ANGLE = 15
MAX_ANGLE = 165

arduino = ArduinoController(port="/dev/ttyACM0", baudrate=115200)

@app.on_event("startup")
def startup():
    try:
        arduino.Connect()
    except Exception as e:
        print(f"[WARNING] Could not connect to Arduino: {e}")

@app.on_event("shutdown")
def shutdown():
    arduino.Close()

@app.post("/point")
def point(req: PointRequest):
    if not arduino.IsConnected():
        return JSONResponse(
            status_code=500,
            content={"error": "Arduino not connected. Cannot send movement command."},
        )

    try:
        az, alt = CoordsTo(LAT, LONG, HEIGHT, req.ra, req.dec)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": "Invalid coordinates", "detail": str(e)},
        )

    if alt < MIN_ANGLE:
        return JSONResponse(
            status_code=400,
            content={"error": f"Target altitude {alt:.2f}° is below {MIN_ANGLE}°."},
        )

    if alt > MAX_ANGLE:
        return JSONResponse(
            status_code=400,
            content={"error": f"Target altitude {alt:.2f}° is above {MAX_ANGLE}°."},
        )

    try:
        cmd = arduino.SendPoint(az, alt)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": "Failed to send serial command", "detail": str(e)},
        )

    return {"az": az, "alt": alt, "sent": cmd}
