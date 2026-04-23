#!/usr/bin/env python3
import math
import time
import sys

import qwiic_icm20948


# ---------------------------
# Vector helpers
# ---------------------------
def dot(a, b):
    return a[0]*b[0] + a[1]*b[1] + a[2]*b[2]

def norm(v):
    return math.sqrt(dot(v, v))

def normalize(v):
    n = norm(v)
    if n < 1e-12:
        return None
    return (v[0]/n, v[1]/n, v[2]/n)

def sub(a, b):
    return (a[0]-b[0], a[1]-b[1], a[2]-b[2])

def mul(v, s):
    return (v[0]*s, v[1]*s, v[2]*s)

def cross(a, b):
    return (
        a[1]*b[2] - a[2]*b[1],
        a[2]*b[0] - a[0]*b[2],
        a[0]*b[1] - a[1]*b[0],
    )

def clamp_angle_deg(deg):
    return deg % 360.0


# ---------------------------
# User-tunable calibration
# ---------------------------
# Replace these with your own hard-iron offsets after calibration.
# Start with zeros if you haven't calibrated yet.
MAG_OFFSET_X = 0.0
MAG_OFFSET_Y = 0.0
MAG_OFFSET_Z = 0.0

# Optional soft-iron scaling. Leave at 1.0 if you don't have it yet.
MAG_SCALE_X = 1.0
MAG_SCALE_Y = 1.0
MAG_SCALE_Z = 1.0

# Local magnetic declination in degrees.
# Example: +10.5 means magnetic north is 10.5° west/east depending on local convention.
# Set this to 0.0 if you only want magnetic heading.
MAG_DECLINATION_DEG = 0.0

# Exponential smoothing for heading display
HEADING_ALPHA = 0.2   # 0..1 ; larger = more responsive, smaller = smoother

# If your installation flips signs or swaps axes, change this mapping.
# The SparkFun library updates raw instance vars axRaw..mzRaw after getAgmt(). :contentReference[oaicite:1]{index=1}
def read_body_accel_and_mag(imu):
    """
    Return accel and mag as body-frame tuples: (x, y, z)

    Adjust signs/swaps here to match your physical mounting.
    """
    # Raw values from the SparkFun driver:
    ax, ay, az = float(imu.axRaw), float(imu.ayRaw), float(imu.azRaw)
    mx, my, mz = float(imu.mxRaw), float(imu.myRaw), float(imu.mzRaw)

    # --- Magnetometer calibration ---
    mx = (mx - MAG_OFFSET_X) * MAG_SCALE_X
    my = (my - MAG_OFFSET_Y) * MAG_SCALE_Y
    mz = (mz - MAG_OFFSET_Z) * MAG_SCALE_Z

    # --- Axis mapping hook ---
    # Change these if your mounting orientation is different.
    accel = (ax, ay, az)
    mag   = (mx, my, mz)

    return accel, mag


def tilt_compensated_heading(accel, mag):
    """
    Compute heading using:
      1) accelerometer -> up/down direction
      2) magnetometer projected into horizontal plane

    Returns:
      heading_deg_true_or_magnetic, up_unit, north_horizontal_unit, east_unit
    """

    # Accelerometer at rest measures gravity.
    # Often "down" points in the direction of +accel, so "up" is -accel.
    # If your pitch appears inverted, switch this sign.
    up = normalize((-accel[0], -accel[1], -accel[2]))
    if up is None:
        return None, None, None, None

    # Project magnetic field into horizontal plane:
    # mh = m - (m·up) up
    vertical_component = mul(up, dot(mag, up))
    mh = sub(mag, vertical_component)
    north_h = normalize(mh)
    if north_h is None:
        return None, up, None, None

    # Create a horizontal east vector
    east = normalize(cross(up, north_h))
    if east is None:
        return None, up, north_h, None

    # Re-orthogonalize north to keep basis tidy
    north_h = normalize(cross(east, up))
    if north_h is None:
        return None, up, None, east

    # Heading relative to body X axis projected into horizontal plane.
    # Assumes your "forward" direction is the sensor/body +X axis.
    # If your forward axis is +Y instead, swap body_forward accordingly.
    body_forward = (1.0, 0.0, 0.0)

    # Remove any vertical component from body forward too
    bf_h = sub(body_forward, mul(up, dot(body_forward, up)))
    bf_h = normalize(bf_h)
    if bf_h is None:
        return None, up, north_h, east

    # atan2(east component, north component)
    x_east = dot(bf_h, east)
    y_north = dot(bf_h, north_h)

    heading_deg = math.degrees(math.atan2(x_east, y_north))
    heading_deg = clamp_angle_deg(heading_deg + MAG_DECLINATION_DEG)

    return heading_deg, up, north_h, east


def simple_pitch_from_accel(accel):
    """
    Simple pitch estimate.
    This definition assumes body X is forward and Z/Y follow a common IMU convention.
    You may need to change this for your mount.
    """
    ax, ay, az = accel
    return math.degrees(math.atan2(ax, math.sqrt(ay*ay + az*az)))


def simple_roll_from_accel(accel):
    ax, ay, az = accel
    return math.degrees(math.atan2(ay, math.sqrt(ax*ax + az*az)))


def main():
    print("\nSparkFun ICM-20948 tilt-compensated heading example\n")

    imu = qwiic_icm20948.QwiicIcm20948()

    if not imu.connected:
        print("The Qwiic ICM20948 device isn't connected. Check wiring/power.", file=sys.stderr)
        sys.exit(1)

    if not imu.begin():
        print("IMU.begin() failed.", file=sys.stderr)
        sys.exit(1)

    print("Started. Press Ctrl+C to stop.\n")

    filtered_heading = None

    try:
        while True:
            if imu.dataReady():
                # SparkFun example/API says getAgmt() updates axRaw..mzRaw instance vars. :contentReference[oaicite:2]{index=2}
                if not imu.getAgmt():
                    time.sleep(0.01)
                    continue

                accel, mag = read_body_accel_and_mag(imu)

                heading_deg, up, north_h, east = tilt_compensated_heading(accel, mag)

                pitch_deg = simple_pitch_from_accel(accel)
                roll_deg = simple_roll_from_accel(accel)

                if heading_deg is not None:
                    if filtered_heading is None:
                        filtered_heading = heading_deg
                    else:
                        # unwrap for smoothing across 0/360
                        delta = heading_deg - filtered_heading
                        if delta > 180:
                            delta -= 360
                        elif delta < -180:
                            delta += 360
                        filtered_heading = clamp_angle_deg(filtered_heading + HEADING_ALPHA * delta)

                print(
                    f"Accel(raw): "
                    f"ax={imu.axRaw:7d} ay={imu.ayRaw:7d} az={imu.azRaw:7d}   "
                    f"Mag(raw): "
                    f"mx={imu.mxRaw:7d} my={imu.myRaw:7d} mz={imu.mzRaw:7d}"
                )

                if heading_deg is None:
                    print("Heading: unavailable")
                else:
                    print(
                        f"Pitch={pitch_deg:7.2f} deg   "
                        f"Roll={roll_deg:7.2f} deg   "
                        f"Heading={heading_deg:7.2f} deg   "
                        f"Filtered={filtered_heading:7.2f} deg"
                    )

                print("-" * 90)

            time.sleep(0.05)

    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()