from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, model_validator
from typing import Optional

from robutils import CoordsTo
from ArduinoController import ArduinoController

import constants
from tracking import IsTracking, StartTrackingBackground
from radio_service import RadioDataService

class PointRequest(BaseModel):
    ra: Optional[float] = None
    dec: Optional[float] = None
    az: Optional[float] = None
    alt: Optional[float] = None

    @model_validator(mode="before")
    @classmethod
    def validate_coordinates(cls, values):
        ra, dec = values.get("ra"), values.get("dec")
        az, alt = values.get("az"), values.get("alt")

        if (ra is not None and dec is not None) and (az is None and alt is None):
            return values
        elif (az is not None and alt is not None) and (ra is None and dec is None):
            return values
        raise ValueError("Must provide either (ra, dec) or (az, alt), but not both. Also don't send them as tuples, I just grouped them to make this easier to read")



class TrackRequest(PointRequest):
    # total tracking time in seconds
    duration: int

class RadioConfigRequest(BaseModel):
    record_mode: Optional[str] = None
    observation_mode: Optional[str] = None

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
radio_service = RadioDataService()


@app.on_event("startup")
def startup():
    radio_service.start()

    try:
        arduino.Connect()
    except Exception as e:
        print(f"[WARNING] Could not connect to Arduino: {e}")


@app.on_event("shutdown")
def shutdown():
    radio_service.stop()

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
        if req.ra is not None and req.dec is not None:
            az, alt = CoordsTo(constants.LAT, constants.LONG, constants.HEIGHT, req.ra, req.dec)
        else:
            az, alt = req.az, req.alt
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": "Coordinate error", "detail": str(e)})

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


@app.get("/radio")
def radio_data():
    return radio_service.get_payload()


@app.post("/radio/config")
def configure_radio(req: RadioConfigRequest):
    try:
        radio_service.set_modes(
            record_mode=req.record_mode,
            observation_mode=req.observation_mode,
        )
    except ValueError as exc:
        return JSONResponse(status_code=400, content={"error": str(exc)})

    return radio_service.get_payload()


@app.post("/radio/capture-cold")
def capture_radio_cold_profile():
    success = radio_service.capture_cold_profile()
    if not success:
        return JSONResponse(
            status_code=409,
            content={"error": "No radio snapshot available yet; try again shortly."},
        )
    return radio_service.get_payload()
