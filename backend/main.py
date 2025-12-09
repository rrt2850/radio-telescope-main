from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from robutils import CoordsTo
from ArduinoController import ArduinoController

import constants
from tracking import IsTracking, StartTrackingBackground

class PointRequest(BaseModel):
    ra: float
    dec: float


class TrackRequest(PointRequest):
    # total tracking time in seconds
    duration: int

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

arduino = ArduinoController(port="/dev/ttyACM0", baudrate=115200)


@app.on_event("startup")
def startup():
    try:
        arduino.Connect()
    except Exception as e:
        print(f"[WARNING] Could not connect to Arduino: {e}")


@app.on_event("shutdown")
def shutdown():
    try:
        arduino.Close()
    except Exception as e:
        print(f"[WARNING] Error while closing Arduino: {e}")


@app.post("/point")
def point(req: PointRequest):
    # Do not interrupt tracking
    if IsTracking():
        return JSONResponse(
            status_code=409,
            content={
                "error": (
                    "Telescope is currently tracking. "
                    "Abort tracking before manual pointing."
                )
            },
        )

    if not arduino.IsConnected():
        return JSONResponse(
            status_code=500,
            content={"error": "Arduino not connected. Cannot send movement command."},
        )

    try:
        az, alt = CoordsTo(constants.LAT, constants.LONG, constants.HEIGHT, req.ra, req.dec)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": "Invalid coordinates", "detail": str(e)},
        )

    if alt < constants.MIN_ANGLE:
        return JSONResponse(
            status_code=400,
            content={"error": f"Target altitude {alt:.2f}° is below {constants.MIN_ANGLE}°."},
        )

    if alt > constants.MAX_ANGLE:
        return JSONResponse(
            status_code=400,
            content={"error": f"Target altitude {alt:.2f}° is above {constants.MAX_ANGLE}°."},
        )

    try:
        cmd = arduino.SendPoint(az, alt)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": "Failed to send serial command", "detail": str(e)},
        )

    return {"az": az, "alt": alt, "sent": cmd}


@app.post("/track")
def track(req: TrackRequest, backgroundTasks: BackgroundTasks):
    # Basic validation
    if req.duration <= 0:
        return JSONResponse(
            status_code=400,
            content={"error": "duration must be positive (seconds)."},
        )
    
    try:
        StartTrackingBackground(
            backgroundTasks=backgroundTasks,
            arduino=arduino,
            ra=req.ra,
            dec=req.dec,
            duration_seconds=req.duration,
        )
    except Exception as e:
        msg = str(e).lower()

        # TODO: do this smarter
        # Decode known failure reasons by message
        if "already in progress" in msg:
            return JSONResponse(
                status_code=409,
                content={"error": msg},
            )
        if "not connected" in msg:
            return JSONResponse(
                status_code=500,
                content={"error": msg},
            )

        # Fallback for any other startup failure
        return JSONResponse(
            status_code=500,
            content={
                "error": "Failed to start tracking.",
                "detail": msg,
            },
        )

    return {
        "status": "tracking_started",
        "ra": req.ra,
        "dec": req.dec,
        "duration": req.duration,
    }
