#!/usr/bin/env python3

import os
import time
import json
import math
import board
import adafruit_mmc56x3


# -----------------------------
# User settings
# -----------------------------

PRINT_HZ = 5

# Set this for your location.
# East declination is positive, west is negative.
MAGNETIC_DECLINATION_DEG = 0.0

# Hard-iron calibration offsets.
# Run with --calibrate and paste results here.
OFFSET_X = 0.0
OFFSET_Y = 0.0
OFFSET_Z = 0.0

# Axis pair used for compass heading.
# Try "xy", "xz", or "yz" depending on sensor mounting.
HEADING_PLANE = "xy"


# -----------------------------
# Helpers
# -----------------------------

def clear_screen():
    os.system("clear")


def normalize_degrees(angle):
    return angle % 360.0


def field_strength(x, y, z):
    return math.sqrt(x * x + y * y + z * z)


def heading_from_plane(x, y, z, plane):
    """
    Returns magnetic heading in degrees from selected sensor plane.

    If rotating the telescope 90 degrees only changes heading a few degrees,
    the plane is probably wrong. Try xy, xz, or yz.
    """
    if plane == "xy":
        a, b = x, y
    elif plane == "xz":
        a, b = x, z
    elif plane == "yz":
        a, b = y, z
    else:
        raise ValueError("HEADING_PLANE must be 'xy', 'xz', or 'yz'")

    heading = math.degrees(math.atan2(b, a))
    heading += MAGNETIC_DECLINATION_DEG
    return normalize_degrees(heading)


def compass_direction(deg):
    directions = [
        "N", "NNE", "NE", "ENE",
        "E", "ESE", "SE", "SSE",
        "S", "SSW", "SW", "WSW",
        "W", "WNW", "NW", "NNW"
    ]
    index = round(deg / 22.5) % 16
    return directions[index]


def encoded_compass_packet(x, y, z, heading):
    """
    This is the structured output you can send over serial, socket, MQTT,
    write to a file, or consume from another telescope process.
    """
    return {
        "sensor": "MMC56x3",
        "heading_deg": round(heading, 2),
        "direction": compass_direction(heading),
        "magnetic_field_uT": {
            "x": round(x, 3),
            "y": round(y, 3),
            "z": round(z, 3),
            "magnitude": round(field_strength(x, y, z), 3),
        },
        "calibration": {
            "offset_x": OFFSET_X,
            "offset_y": OFFSET_Y,
            "offset_z": OFFSET_Z,
            "declination_deg": MAGNETIC_DECLINATION_DEG,
            "heading_plane": HEADING_PLANE,
        },
        "timestamp": time.time(),
    }


# -----------------------------
# Main compass mode
# -----------------------------

def run_compass():
    i2c = board.I2C()
    mag = adafruit_mmc56x3.MMC5603(i2c)

    delay = 1.0 / PRINT_HZ

    while True:
        raw_x, raw_y, raw_z = mag.magnetic

        x = raw_x - OFFSET_X
        y = raw_y - OFFSET_Y
        z = raw_z - OFFSET_Z

        heading = heading_from_plane(x, y, z, HEADING_PLANE)
        packet = encoded_compass_packet(x, y, z, heading)

        clear_screen()

        print("MMC56x3 Telescope Compass")
        print("-------------------------")
        print(f"Heading:   {heading:7.2f}°  {compass_direction(heading)}")
        print(f"Plane:     {HEADING_PLANE}")
        print()
        print("Corrected magnetic field:")
        print(f"X:         {x:9.3f} µT")
        print(f"Y:         {y:9.3f} µT")
        print(f"Z:         {z:9.3f} µT")
        print(f"Magnitude: {field_strength(x, y, z):9.3f} µT")
        print()
        print("Encoded JSON:")
        print(json.dumps(packet, indent=2))
        print()
        print("Tip: If heading barely changes when rotated, try HEADING_PLANE = 'xz' or 'yz'.")

        time.sleep(delay)


# -----------------------------
# Calibration mode
# -----------------------------

def run_calibration(seconds=30):
    i2c = board.I2C()
    mag = adafruit_mmc56x3.MMC5603(i2c)

    xmin = ymin = zmin = 999999.0
    xmax = ymax = zmax = -999999.0

    start = time.time()

    while time.time() - start < seconds:
        x, y, z = mag.magnetic

        xmin = min(xmin, x)
        xmax = max(xmax, x)

        ymin = min(ymin, y)
        ymax = max(ymax, y)

        zmin = min(zmin, z)
        zmax = max(zmax, z)

        clear_screen()
        remaining = seconds - int(time.time() - start)

        print("MMC56x3 Calibration")
        print("-------------------")
        print(f"Rotate the mounted telescope/sensor through as much motion as possible.")
        print(f"Time remaining: {remaining}s")
        print()
        print(f"X range: {xmin:9.3f} to {xmax:9.3f}")
        print(f"Y range: {ymin:9.3f} to {ymax:9.3f}")
        print(f"Z range: {zmin:9.3f} to {zmax:9.3f}")

        time.sleep(0.05)

    offset_x = (xmax + xmin) / 2.0
    offset_y = (ymax + ymin) / 2.0
    offset_z = (zmax + zmin) / 2.0

    clear_screen()
    print("Calibration complete.")
    print()
    print("Paste these into the top of the script:")
    print()
    print(f"OFFSET_X = {offset_x:.6f}")
    print(f"OFFSET_Y = {offset_y:.6f}")
    print(f"OFFSET_Z = {offset_z:.6f}")
    print()
    print("Then test HEADING_PLANE values:")
    print("HEADING_PLANE = 'xy'")
    print("HEADING_PLANE = 'xz'")
    print("HEADING_PLANE = 'yz'")


# -----------------------------
# Entrypoint
# -----------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="MMC56x3 telescope compass")
    parser.add_argument(
        "--calibrate",
        action="store_true",
        help="Run hard-iron calibration mode",
    )
    parser.add_argument(
        "--seconds",
        type=int,
        default=30,
        help="Calibration duration in seconds",
    )

    args = parser.parse_args()

    if args.calibrate:
        run_calibration(args.seconds)
    else:
        run_compass()