# tracking.py
import threading
import time
from datetime import datetime, timedelta, timezone
from robutils import CoordsTo, NormalizePointing
import constants

trackingLock = threading.Lock()
trackingActive = False


def IsTracking() -> bool:
    with trackingLock:
        return trackingActive


def SetTracking(active: bool) -> None:
    global trackingActive
    with trackingLock:
        trackingActive = active


def TrackTarget(arduino, ra: float, dec: float, durationSeconds: int):
    try:
        if not arduino.IsConnected():
            print("[ERROR] Arduino not connected at tracking start.")
            return

        endTime = datetime.now(timezone.utc) + timedelta(seconds=durationSeconds)

        while datetime.now(timezone.utc) < endTime:

            try:
                az, alt = CoordsTo(constants.LAT, constants.LONG, constants.HEIGHT, ra, dec)
                az, alt = NormalizePointing(az, alt)
            except Exception as e:
                print(f"[ERROR] Failed to compute coordinates while tracking: {e}")
                break

            if alt < constants.MIN_ANGLE or alt > constants.MAX_ANGLE:
                print(f"[INFO] Target altitude {alt:.2f} out of bounds. Stopping tracking.")
                break

            try:
                arduino.SendPoint(az, alt, waitForDone=True)
            except Exception as e:
                print(f"[ERROR] Failed to send tracking command: {e}")
                break

            remaining = (endTime - datetime.now(timezone.utc)).total_seconds()
            if remaining <= 0:
                break

            time.sleep(min(constants.REPOINT_LENGTH, max(0, remaining)))

    finally:
        SetTracking(False)
        print("[INFO] Tracking finished or aborted.")


def StartTrackingBackground(
    backgroundTasks,
    arduino,
    ra: float,
    dec: float,
    duration_seconds: int,
):
    """
    Attempt to reserve tracking and enqueue a background task.

    Raises:
        Exception: whatever error occurs
    """
    global trackingActive

    with trackingLock:
        if trackingActive:
            raise Exception("Tracking already in progress.")

        if not arduino.IsConnected():
            raise Exception("Arduino not connected.")

        trackingActive = True

    try:
        backgroundTasks.add_task(TrackTarget, arduino, ra, dec, duration_seconds)
    except Exception as e:
        # If enqueueing fails, undo the reservation
        SetTracking(False)
        raise Exception(f"Failed to schedule tracking task: {e}")
