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
- This version uses gravity + magnetic field vectors directly for tilt compensation.
- You may need to change AXIS_MAP_* and FORWARD_AXIS depending on mounting.
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
SAMPLE_HZ = 10.0
DECLINATION_DEG = 0.0  # 0.0 for magnetic north; set local declination for true north

# Hard-iron calibration offsets for magnetometer raw counts
MAG_OFFSET_X = 0.0
MAG_OFFSET_Y = 0.0
MAG_OFFSET_Z = 0.0

# Optional soft-iron scale correction
MAG_SCALE_X = 1.0
MAG_SCALE_Y = 1.0
MAG_SCALE_Z = 1.0

# Axis remap from raw sensor frame to your desired body frame.
# Each entry is one of: "x", "-x", "y", "-y", "z", "-z"
#
# These define:
#   body_x = chosen raw axis
#   body_y = chosen raw axis
#   body_z = chosen raw axis
#
# Start with identity. If heading behaves oddly, adjust these to match your mount.
AXIS_MAP_X = "x"
AXIS_MAP_Y = "y"
AXIS_MAP_Z = "z"

# Which BODY axis points forward in the final installation?
# Usually this is "x" after remapping, but can be "-x", "y", "-y", "z", "-z".
FORWARD_AXIS = "x"
# ----------------------------------


running = True


def handle_sigint(signum, frame):
    global running
    running = False


signal.signal(signal.SIGINT, handle_sigint)
signal.signal(signal.SIGTERM, handle_sigint)


def normalize3(v):
    x, y, z = v
    n = math.sqrt(x * x + y * y + z * z)
    if n == 0.0:
        return (0.0, 0.0, 0.0)
    return (x / n, y / n, z / n)


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def cross(a, b):
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def get_axis_component(v, axis_name):
    x, y, z = v
    if axis_name == "x":
        return x
    if axis_name == "-x":
        return -x
    if axis_name == "y":
        return y
    if axis_name == "-y":
        return -y
    if axis_name == "z":
        return z
    if axis_name == "-z":
        return -z
    raise ValueError(f"Invalid axis specifier: {axis_name}")


def remap_axes(v):
    """
    Remap raw sensor vector into body-frame vector.
    """
    return (
        get_axis_component(v, AXIS_MAP_X),
        get_axis_component(v, AXIS_MAP_Y),
        get_axis_component(v, AXIS_MAP_Z),
    )


def forward_unit_vector():
    """
    Returns the body-frame unit vector that points forward.
    """
    if FORWARD_AXIS == "x":
        return (1.0, 0.0, 0.0)
    if FORWARD_AXIS == "-x":
        return (-1.0, 0.0, 0.0)
    if FORWARD_AXIS == "y":
        return (0.0, 1.0, 0.0)
    if FORWARD_AXIS == "-y":
        return (0.0, -1.0, 0.0)
    if FORWARD_AXIS == "z":
        return (0.0, 0.0, 1.0)
    if FORWARD_AXIS == "-z":
        return (0.0, 0.0, -1.0)
    raise ValueError(f"Invalid FORWARD_AXIS: {FORWARD_AXIS}")


def tilt_compensated_heading(ax, ay, az, mx, my, mz):
    a_body = remap_axes((ax, ay, az))
    m_body = remap_axes((mx, my, mz))

    # Use DOWN from accelerometer, then define UP
    down = normalize3(a_body)
    up = (-down[0], -down[1], -down[2])

    m = normalize3(m_body)

    east = normalize3(cross(m, up))
    if east == (0.0, 0.0, 0.0):
        return float("nan"), float("nan"), float("nan")

    north = normalize3(cross(up, east))

    fwd = forward_unit_vector()

    heading_rad = math.atan2(dot(fwd, east), dot(fwd, north))
    heading_deg = (math.degrees(heading_rad) + DECLINATION_DEG) % 360.0

    ux, uy, uz = up
    pitch_rad = math.atan2(-ux, math.sqrt(uy * uy + uz * uz))
    roll_rad = math.atan2(uy, uz)

    return heading_deg, math.degrees(pitch_rad), math.degrees(roll_rad)

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

        if f.tell() == 0:
            writer.writerow([
                "timestamp_utc",
                "heading_deg_magnetic",
                "pitch_deg",
                "roll_deg",
                "ax_body", "ay_body", "az_body",
                "mx_body_cal", "my_body_cal", "mz_body_cal",
            ])

        print(f"Logging to {LOG_FILE}. Press Ctrl+C to stop.")
        print(f"Axis remap: X={AXIS_MAP_X}, Y={AXIS_MAP_Y}, Z={AXIS_MAP_Z}")
        print(f"Forward axis: {FORWARD_AXIS}")

        while running:
            loop_start = time.time()

            if imu.dataReady():
                ok = imu.getAgmt()
                if not ok:
                    print("Read failed.")
                    time.sleep(period)
                    continue

                # Raw accelerometer counts
                ax_raw = float(imu.axRaw)
                ay_raw = float(imu.ayRaw)
                az_raw = float(imu.azRaw)

                # Raw magnetometer counts with simple calibration
                mx_raw = (float(imu.mxRaw) - MAG_OFFSET_X) * MAG_SCALE_X
                my_raw = (float(imu.myRaw) - MAG_OFFSET_Y) * MAG_SCALE_Y
                mz_raw = (float(imu.mzRaw) - MAG_OFFSET_Z) * MAG_SCALE_Z

                # Remap for logging consistency
                ax_body, ay_body, az_body = remap_axes((ax_raw, ay_raw, az_raw))
                mx_body, my_body, mz_body = remap_axes((mx_raw, my_raw, mz_raw))

                heading_deg, pitch_deg, roll_deg = tilt_compensated_heading(
                    ax_raw, ay_raw, az_raw, mx_raw, my_raw, mz_raw
                )

                ts = datetime.now(timezone.utc).isoformat()

                writer.writerow([
                    ts,
                    round(heading_deg, 2) if not math.isnan(heading_deg) else "",
                    round(pitch_deg, 2) if not math.isnan(pitch_deg) else "",
                    round(roll_deg, 2) if not math.isnan(roll_deg) else "",
                    round(ax_body, 2),
                    round(ay_body, 2),
                    round(az_body, 2),
                    round(mx_body, 2),
                    round(my_body, 2),
                    round(mz_body, 2),
                ])
                f.flush()

                if math.isnan(heading_deg):
                    print(f"{ts}  heading=NaN   pitch=NaN   roll=NaN")
                else:
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