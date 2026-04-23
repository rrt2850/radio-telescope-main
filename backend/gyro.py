#!/usr/bin/env python3
"""
Log ICM-20948 pointing direction relative to magnetic north.

Requires:
    pip3 install sparkfun-qwiic-icm20948

Output:
    heading_log.csv with:
      timestamp_utc, heading_deg_magnetic, pitch_deg, roll_deg,
      ax, ay, az, mx, my, mz

Notes:
- This computes MAGNETIC heading, not true heading.
- For best results, calibrate the magnetometer offsets below.
- Axis signs may need adjustment depending on how your board is mounted.
"""

import csv
import math
import signal
import sys
import time
from datetime import datetime, timezone

import qwiic_icm20948


# ---------- User settings ----------
LOG_FILE = "heading_log.csv"
SAMPLE_HZ = 10.0  # log rate
DECLINATION_DEG = 0.0  # keep 0.0 for magnetic north; set local declination for true north
# Hard-iron calibration offsets for magnetometer raw counts.
# Start with 0,0,0. After calibration, replace these with measured offsets.
MAG_OFFSET_X = 0.0
MAG_OFFSET_Y = 0.0
MAG_OFFSET_Z = 0.0

# Optional soft-iron scale correction. Leave as 1.0 until calibrated.
MAG_SCALE_X = 1.0
MAG_SCALE_Y = 1.0
MAG_SCALE_Z = 1.0
# ----------------------------------


running = True


def handle_sigint(signum, frame):
    global running
    running = False


signal.signal(signal.SIGINT, handle_sigint)
signal.signal(signal.SIGTERM, handle_sigint)


def normalize(vx, vy, vz):
    norm = math.sqrt(vx * vx + vy * vy + vz * vz)
    if norm == 0:
        return 0.0, 0.0, 0.0
    return vx / norm, vy / norm, vz / norm


def tilt_compensated_heading(ax, ay, az, mx, my, mz):
    """
    Returns:
        heading_deg_magnetic, pitch_deg, roll_deg

    Assumes:
    - accelerometer gives gravity direction when device is not accelerating hard
    - magnetometer is calibrated
    """

    # Normalize accelerometer and magnetometer
    ax, ay, az = normalize(ax, ay, az)
    mx, my, mz = normalize(mx, my, mz)

    # Roll and pitch from accelerometer
    roll = math.atan2(ay, az)
    pitch = math.atan2(-ax, math.sqrt(ay * ay + az * az))

    # Tilt compensation
    mx_comp = mx * math.cos(pitch) + mz * math.sin(pitch)
    my_comp = (
        mx * math.sin(roll) * math.sin(pitch)
        + my * math.cos(roll)
        - mz * math.sin(roll) * math.cos(pitch)
    )

    heading = math.atan2(-my_comp, mx_comp)  # sign may need flipping for your board
    heading_deg = math.degrees(heading) + DECLINATION_DEG

    # Wrap to [0, 360)
    heading_deg %= 360.0

    return heading_deg, math.degrees(pitch), math.degrees(roll)


def main():
    imu = qwiic_icm20948.QwiicIcm20948()

    if not imu.connected:
        print("ICM-20948 not found. Check wiring and I2C.")
        sys.exit(1)

    if not imu.begin():
        print("Failed to initialize ICM-20948.")
        sys.exit(1)

    period = 1.0 / SAMPLE_HZ

    with open(LOG_FILE, "a", newline="") as f:
        writer = csv.writer(f)

        # Write header only if file is empty
        if f.tell() == 0:
            writer.writerow([
                "timestamp_utc",
                "heading_deg_magnetic",
                "pitch_deg",
                "roll_deg",
                "ax_raw", "ay_raw", "az_raw",
                "mx_raw_cal", "my_raw_cal", "mz_raw_cal",
            ])

        print(f"Logging to {LOG_FILE}. Press Ctrl+C to stop.")

        while running:
            loop_start = time.time()

            if imu.dataReady():
                ok = imu.getAgmt()
                if not ok:
                    print("Read failed.")
                    time.sleep(period)
                    continue

                # Raw accelerometer counts
                ax = float(imu.axRaw)
                ay = float(imu.ayRaw)
                az = float(imu.azRaw)

                # Raw magnetometer counts with simple calibration
                mx = (float(imu.mxRaw) - MAG_OFFSET_X) * MAG_SCALE_X
                my = (float(imu.myRaw) - MAG_OFFSET_Y) * MAG_SCALE_Y
                mz = (float(imu.mzRaw) - MAG_OFFSET_Z) * MAG_SCALE_Z

                heading_deg, pitch_deg, roll_deg = tilt_compensated_heading(
                    ax, ay, az, mx, my, mz
                )

                ts = datetime.now(timezone.utc).isoformat()

                writer.writerow([
                    ts,
                    round(heading_deg, 2),
                    round(pitch_deg, 2),
                    round(roll_deg, 2),
                    int(ax), int(ay), int(az),
                    round(mx, 2), round(my, 2), round(mz, 2),
                ])
                f.flush()

                print(
                    f"{ts}  heading={heading_deg:7.2f}° magnetic   "
                    f"pitch={pitch_deg:7.2f}°   roll={roll_deg:7.2f}°"
                )

            elapsed = time.time() - loop_start
            if elapsed < period:
                time.sleep(period - elapsed)

    print("Stopped.")


if __name__ == "__main__":
    main()