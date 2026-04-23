#!/usr/bin/env python3
import math
import time
import sys

import qwiic_icm20948


# ============================================================
# Settings you may need to tweak
# ============================================================

PRINT_HZ = 20.0                 # console update rate
MADGWICK_BETA = 0.08            # lower = smoother, higher = faster correction
DECLINATION_DEG = 0.0           # set your local declination if you want true north
USE_ACCEL_SIGN_FLIP = False     # flip if pitch/roll look upside-down

# Magnetometer hard-iron offsets.
# Leave as 0 for now, but heading will be better after calibration.
MAG_BIAS_X = 0.0
MAG_BIAS_Y = 0.0
MAG_BIAS_Z = 0.0

# Optional per-axis scale correction (soft-iron-ish simple scaling)
MAG_SCALE_X = 1.0
MAG_SCALE_Y = 1.0
MAG_SCALE_Z = 1.0

# Forward axis of your mounted device in SENSOR coordinates:
# "x", "-x", "y", "-y", "z", "-z"
FORWARD_AXIS = "x"

# Yaw smoothing on final output only
HEADING_SMOOTHING = 0.15


# ============================================================
# Small vector helpers
# ============================================================

def inv_sqrt(x: float) -> float:
    if x <= 0.0:
        return 0.0
    return 1.0 / math.sqrt(x)


def clamp360(deg: float) -> float:
    return deg % 360.0


def signed_angle_diff_deg(a: float, b: float) -> float:
    d = a - b
    while d > 180.0:
        d -= 360.0
    while d < -180.0:
        d += 360.0
    return d


# ============================================================
# Madgwick AHRS
# 6/9DOF fusion using gyro + accel + mag
# ============================================================

class MadgwickAHRS:
    def __init__(self, beta: float = 0.08):
        self.beta = beta
        # quaternion representing sensor frame relative to Earth frame
        self.q0 = 1.0
        self.q1 = 0.0
        self.q2 = 0.0
        self.q3 = 0.0

    def update(self, gx, gy, gz, ax, ay, az, mx, my, mz, dt):
        """
        gx,gy,gz in rad/s
        ax,ay,az arbitrary accel units
        mx,my,mz arbitrary mag units
        dt in seconds
        """

        q0 = self.q0
        q1 = self.q1
        q2 = self.q2
        q3 = self.q3

        # Normalize accelerometer
        norm_a = math.sqrt(ax * ax + ay * ay + az * az)
        if norm_a == 0.0:
            return
        ax /= norm_a
        ay /= norm_a
        az /= norm_a

        # Normalize magnetometer
        norm_m = math.sqrt(mx * mx + my * my + mz * mz)
        if norm_m == 0.0:
            # fall back to IMU-only update
            self.update_imu(gx, gy, gz, ax, ay, az, dt)
            return
        mx /= norm_m
        my /= norm_m
        mz /= norm_m

        # Auxiliary variables to avoid repeated arithmetic
        _2q0mx = 2.0 * q0 * mx
        _2q0my = 2.0 * q0 * my
        _2q0mz = 2.0 * q0 * mz
        _2q1mx = 2.0 * q1 * mx
        _2q0 = 2.0 * q0
        _2q1 = 2.0 * q1
        _2q2 = 2.0 * q2
        _2q3 = 2.0 * q3
        _2q0q2 = 2.0 * q0 * q2
        _2q2q3 = 2.0 * q2 * q3
        q0q0 = q0 * q0
        q0q1 = q0 * q1
        q0q2 = q0 * q2
        q0q3 = q0 * q3
        q1q1 = q1 * q1
        q1q2 = q1 * q2
        q1q3 = q1 * q3
        q2q2 = q2 * q2
        q2q3 = q2 * q3
        q3q3 = q3 * q3

        # Reference direction of Earth's magnetic field
        hx = mx * q0q0 - _2q0my * q3 + _2q0mz * q2 + mx * q1q1 + _2q1 * my * q2 + _2q1 * mz * q3 - mx * q2q2 - mx * q3q3
        hy = _2q0mx * q3 + my * q0q0 - _2q0mz * q1 + _2q1mx * q2 - my * q1q1 + my * q2q2 + _2q2 * mz * q3 - my * q3q3
        _2bx = math.sqrt(hx * hx + hy * hy)
        _2bz = -_2q0mx * q2 + _2q0my * q1 + mz * q0q0 + _2q1mx * q3 - mz * q1q1 + _2q2 * my * q3 - mz * q2q2 + mz * q3q3
        _4bx = 2.0 * _2bx
        _4bz = 2.0 * _2bz

        # Gradient descent corrective step
        s0 = (
            -_2q2 * (2.0 * (q1q3 - q0q2) - ax)
            + _2q1 * (2.0 * (q0q1 + q2q3) - ay)
            - _2bz * q2 * (_2bx * (0.5 - q2q2 - q3q3) + _2bz * (q1q3 - q0q2) - mx)
            + (-_2bx * q3 + _2bz * q1) * (_2bx * (q1q2 - q0q3) + _2bz * (q0q1 + q2q3) - my)
            + _2bx * q2 * (_2bx * (q0q2 + q1q3) + _2bz * (0.5 - q1q1 - q2q2) - mz)
        )
        s1 = (
            _2q3 * (2.0 * (q1q3 - q0q2) - ax)
            + _2q0 * (2.0 * (q0q1 + q2q3) - ay)
            - 4.0 * q1 * (1.0 - 2.0 * (q1q1 + q2q2) - az)
            + _2bz * q3 * (_2bx * (0.5 - q2q2 - q3q3) + _2bz * (q1q3 - q0q2) - mx)
            + (_2bx * q2 + _2bz * q0) * (_2bx * (q1q2 - q0q3) + _2bz * (q0q1 + q2q3) - my)
            + (_2bx * q3 - _4bz * q1) * (_2bx * (q0q2 + q1q3) + _2bz * (0.5 - q1q1 - q2q2) - mz)
        )
        s2 = (
            -_2q0 * (2.0 * (q1q3 - q0q2) - ax)
            + _2q3 * (2.0 * (q0q1 + q2q3) - ay)
            - 4.0 * q2 * (1.0 - 2.0 * (q1q1 + q2q2) - az)
            + (-_4bx * q2 - _2bz * q0) * (_2bx * (0.5 - q2q2 - q3q3) + _2bz * (q1q3 - q0q2) - mx)
            + (_2bx * q1 + _2bz * q3) * (_2bx * (q1q2 - q0q3) + _2bz * (q0q1 + q2q3) - my)
            + (_2bx * q0 - _4bz * q2) * (_2bx * (q0q2 + q1q3) + _2bz * (0.5 - q1q1 - q2q2) - mz)
        )
        s3 = (
            _2q1 * (2.0 * (q1q3 - q0q2) - ax)
            + _2q2 * (2.0 * (q0q1 + q2q3) - ay)
            + (-_4bx * q3 + _2bz * q1) * (_2bx * (0.5 - q2q2 - q3q3) + _2bz * (q1q3 - q0q2) - mx)
            + (-_2bx * q0 + _2bz * q2) * (_2bx * (q1q2 - q0q3) + _2bz * (q0q1 + q2q3) - my)
            + _2bx * q1 * (_2bx * (q0q2 + q1q3) + _2bz * (0.5 - q1q1 - q2q2) - mz)
        )

        norm_s = math.sqrt(s0 * s0 + s1 * s1 + s2 * s2 + s3 * s3)
        if norm_s != 0.0:
            s0 /= norm_s
            s1 /= norm_s
            s2 /= norm_s
            s3 /= norm_s

        # Rate of change of quaternion
        qDot0 = 0.5 * (-q1 * gx - q2 * gy - q3 * gz) - self.beta * s0
        qDot1 = 0.5 * ( q0 * gx + q2 * gz - q3 * gy) - self.beta * s1
        qDot2 = 0.5 * ( q0 * gy - q1 * gz + q3 * gx) - self.beta * s2
        qDot3 = 0.5 * ( q0 * gz + q1 * gy - q2 * gx) - self.beta * s3

        # Integrate
        q0 += qDot0 * dt
        q1 += qDot1 * dt
        q2 += qDot2 * dt
        q3 += qDot3 * dt

        # Normalize quaternion
        norm_q = math.sqrt(q0 * q0 + q1 * q1 + q2 * q2 + q3 * q3)
        if norm_q == 0.0:
            return

        self.q0 = q0 / norm_q
        self.q1 = q1 / norm_q
        self.q2 = q2 / norm_q
        self.q3 = q3 / norm_q

    def update_imu(self, gx, gy, gz, ax, ay, az, dt):
        q0 = self.q0
        q1 = self.q1
        q2 = self.q2
        q3 = self.q3

        norm_a = math.sqrt(ax * ax + ay * ay + az * az)
        if norm_a == 0.0:
            return
        ax /= norm_a
        ay /= norm_a
        az /= norm_a

        _2q0 = 2.0 * q0
        _2q1 = 2.0 * q1
        _2q2 = 2.0 * q2
        _2q3 = 2.0 * q3
        _4q0 = 4.0 * q0
        _4q1 = 4.0 * q1
        _4q2 = 4.0 * q2
        _8q1 = 8.0 * q1
        _8q2 = 8.0 * q2
        q0q0 = q0 * q0
        q1q1 = q1 * q1
        q2q2 = q2 * q2
        q3q3 = q3 * q3

        s0 = _4q0 * q2q2 + _2q2 * ax + _4q0 * q1q1 - _2q1 * ay
        s1 = _4q1 * q3q3 - _2q3 * ax + 4.0 * q0q0 * q1 - _2q0 * ay - _4q1 + _8q1 * q1q1 + _8q1 * q2q2 + _4q1 * az
        s2 = 4.0 * q0q0 * q2 + _2q0 * ax + _4q2 * q3q3 - _2q3 * ay - _4q2 + _8q2 * q1q1 + _8q2 * q2q2 + _4q2 * az
        s3 = 4.0 * q1q1 * q3 - _2q1 * ax + 4.0 * q2q2 * q3 - _2q2 * ay

        norm_s = math.sqrt(s0 * s0 + s1 * s1 + s2 * s2 + s3 * s3)
        if norm_s != 0.0:
            s0 /= norm_s
            s1 /= norm_s
            s2 /= norm_s
            s3 /= norm_s

        qDot0 = 0.5 * (-q1 * gx - q2 * gy - q3 * gz) - self.beta * s0
        qDot1 = 0.5 * ( q0 * gx + q2 * gz - q3 * gy) - self.beta * s1
        qDot2 = 0.5 * ( q0 * gy - q1 * gz + q3 * gx) - self.beta * s2
        qDot3 = 0.5 * ( q0 * gz + q1 * gy - q2 * gx) - self.beta * s3

        q0 += qDot0 * dt
        q1 += qDot1 * dt
        q2 += qDot2 * dt
        q3 += qDot3 * dt

        norm_q = math.sqrt(q0 * q0 + q1 * q1 + q2 * q2 + q3 * q3)
        if norm_q == 0.0:
            return

        self.q0 = q0 / norm_q
        self.q1 = q1 / norm_q
        self.q2 = q2 / norm_q
        self.q3 = q3 / norm_q

    def euler_deg(self):
        q0, q1, q2, q3 = self.q0, self.q1, self.q2, self.q3

        # roll (x-axis rotation)
        sinr_cosp = 2.0 * (q0 * q1 + q2 * q3)
        cosr_cosp = 1.0 - 2.0 * (q1 * q1 + q2 * q2)
        roll = math.degrees(math.atan2(sinr_cosp, cosr_cosp))

        # pitch (y-axis rotation)
        sinp = 2.0 * (q0 * q2 - q3 * q1)
        if abs(sinp) >= 1.0:
            pitch = math.degrees(math.copysign(math.pi / 2.0, sinp))
        else:
            pitch = math.degrees(math.asin(sinp))

        # yaw (z-axis rotation)
        siny_cosp = 2.0 * (q0 * q3 + q1 * q2)
        cosy_cosp = 1.0 - 2.0 * (q2 * q2 + q3 * q3)
        yaw = math.degrees(math.atan2(siny_cosp, cosy_cosp))

        return roll, pitch, yaw


# ============================================================
# Sensor axis helpers
# ============================================================

def axis_value(name, x, y, z):
    if name == "x":
        return x
    if name == "-x":
        return -x
    if name == "y":
        return y
    if name == "-y":
        return -y
    if name == "z":
        return z
    if name == "-z":
        return -z
    raise ValueError(f"Unknown axis spec: {name}")


def yaw_from_quaternion_about_forward_axis(filter_obj, forward_axis="x"):
    """
    For a simple mounted device, many times you can just use Euler yaw.
    But if your mounted forward axis isn't sensor +X, this remaps it.
    """
    q0, q1, q2, q3 = filter_obj.q0, filter_obj.q1, filter_obj.q2, filter_obj.q3

    # Rotation matrix body->earth (NED-ish/sign-convention-ish depending on filter)
    r11 = 1.0 - 2.0 * (q2*q2 + q3*q3)
    r12 = 2.0 * (q1*q2 - q0*q3)
    r13 = 2.0 * (q1*q3 + q0*q2)

    r21 = 2.0 * (q1*q2 + q0*q3)
    r22 = 1.0 - 2.0 * (q1*q1 + q3*q3)
    r23 = 2.0 * (q2*q3 - q0*q1)

    r31 = 2.0 * (q1*q3 - q0*q2)
    r32 = 2.0 * (q2*q3 + q0*q1)
    r33 = 1.0 - 2.0 * (q1*q1 + q2*q2)

    if forward_axis in ("x", "-x"):
        sx = 1.0 if forward_axis == "x" else -1.0
        fx, fy, fz = sx * r11, sx * r21, sx * r31
    elif forward_axis in ("y", "-y"):
        sy = 1.0 if forward_axis == "y" else -1.0
        fx, fy, fz = sy * r12, sy * r22, sy * r32
    elif forward_axis in ("z", "-z"):
        sz = 1.0 if forward_axis == "z" else -1.0
        fx, fy, fz = sz * r13, sz * r23, sz * r33
    else:
        raise ValueError("Bad FORWARD_AXIS")

    # Heading from horizontal projection of forward vector.
    heading = math.degrees(math.atan2(fy, fx))
    return clamp360(heading + DECLINATION_DEG)


# ============================================================
# Main
# ============================================================

def main():
    print("\nSparkFun ICM-20948 fused compass / heading\n")

    imu = qwiic_icm20948.QwiicIcm20948()

    if imu.connected is False:
        print("ICM-20948 not connected.", file=sys.stderr)
        sys.exit(1)

    ok = imu.begin()
    if not ok:
        print("IMU.begin() failed.", file=sys.stderr)
        sys.exit(1)

    print("Started. Ctrl+C to stop.")
    print("If heading is mirrored or 90/180 off, adjust FORWARD_AXIS.\n")

    ahrs = MadgwickAHRS(beta=MADGWICK_BETA)

    last_time = time.monotonic()
    last_print = last_time
    filtered_heading = None

    try:
        while True:
            if not imu.dataReady():
                time.sleep(0.002)
                continue

            # SparkFun example/docs: getAgmt() updates axRaw..mzRaw instance variables. :contentReference[oaicite:1]{index=1}
            imu.getAgmt()

            now = time.monotonic()
            dt = now - last_time
            last_time = now

            # guard dt
            if dt <= 0.0 or dt > 0.25:
                dt = 1.0 / 100.0

            ax = float(imu.axRaw)
            ay = float(imu.ayRaw)
            az = float(imu.azRaw)

            gx = float(imu.gxRaw)
            gy = float(imu.gyRaw)
            gz = float(imu.gzRaw)

            mx = (float(imu.mxRaw) - MAG_BIAS_X) * MAG_SCALE_X
            my = (float(imu.myRaw) - MAG_BIAS_Y) * MAG_SCALE_Y
            mz = (float(imu.mzRaw) - MAG_BIAS_Z) * MAG_SCALE_Z

            if USE_ACCEL_SIGN_FLIP:
                ax, ay, az = -ax, -ay, -az

            # Raw gyro units from library are exposed as gxRaw/gyRaw/gzRaw; convert if needed.
            # For many SparkFun IMU examples these are raw counts, so if your output looks too sluggish
            # or too wild, set your own scale here based on your configured gyro full-scale range.
            #
            # Common starting assumption for ICM-20948 default FS:
            # 131 LSB/(deg/s) for ±250 dps is MPU6050-ish, but NOT guaranteed here.
            # Start with this placeholder and tune if motion is clearly wrong.
            GYRO_LSB_PER_DPS = 131.0

            gx_rad = math.radians(gx / GYRO_LSB_PER_DPS)
            gy_rad = math.radians(gy / GYRO_LSB_PER_DPS)
            gz_rad = math.radians(gz / GYRO_LSB_PER_DPS)

            ahrs.update(gx_rad, gy_rad, gz_rad, ax, ay, az, mx, my, mz, dt)

            roll_deg, pitch_deg, yaw_deg = ahrs.euler_deg()
            heading_deg = yaw_from_quaternion_about_forward_axis(ahrs, FORWARD_AXIS)

            if filtered_heading is None:
                filtered_heading = heading_deg
            else:
                delta = signed_angle_diff_deg(heading_deg, filtered_heading)
                filtered_heading = clamp360(filtered_heading + HEADING_SMOOTHING * delta)

            if now - last_print >= (1.0 / PRINT_HZ):
                last_print = now

                print(
                    f"heading={heading_deg:7.2f}°   "
                    f"smoothed={filtered_heading:7.2f}°   "
                    f"roll={roll_deg:7.2f}°   "
                    f"pitch={pitch_deg:7.2f}°   "
                    f"yaw={yaw_deg:7.2f}°"
                )

    except KeyboardInterrupt:
        print("\nStopped.")
        sys.exit(0)


if __name__ == "__main__":
    main()