import time
import math
import csv
import board
import adafruit_icm20x
import json


# ---------------------------
# Hardware Init
# ---------------------------
i2c = board.I2C()
imu = adafruit_icm20x.ICM20948(i2c)


# ---------------------------
# Constants
# ---------------------------
TIMESTEP = 0.02  # How often the loop runs in seconds

# How much we trust gyro vs sensors
AZIMUTH_GYRO_WEIGHT = 0.98
ALTITUDE_GYRO_WEIGHT = 0.98

# Magnetic declination (degrees) at the RIT observatory
BASE_DECLINATION = -11.40
YEARLY_CHANGE = 0.04  # degrees per year
REFERENCE_YEAR = 2026

# How much of the new acceleration do we use compared to the old one
NEW_ACCELERATION_WEIGHT = 0.2

CAL_FILE = "mag_calibration.json"


# ---------------------------
# Derived Values
# ---------------------------
currYear = time.localtime().tm_year
DECLINATION = BASE_DECLINATION + (currYear - REFERENCE_YEAR) * YEARLY_CHANGE


# ---------------------------
# Magnetometer Calibration
# ---------------------------
def calibrateMagnetometer(imu, duration=30):
    print("\nMagnetometer Calibration:")
    print("Rotate the sensor slowly in all orientations.")
    print("Figure-8 motions help, try to avoid metal things lol")
    input("Press ENTER to start calibration...")

    minX = minY = minZ = float("inf")
    maxX = maxY = maxZ = float("-inf")

    start = time.time()

    while time.time() - start < duration:
        mx, my, mz = imu.magnetic

        minX = min(minX, mx)
        minY = min(minY, my)
        minZ = min(minZ, mz)

        maxX = max(maxX, mx)
        maxY = max(maxY, my)
        maxZ = max(maxZ, mz)

        print(
            f"\rCalibrating... {int(time.time() - start)}s "
            f"X[{minX:.1f},{maxX:.1f}] "
            f"Y[{minY:.1f},{maxY:.1f}] "
            f"Z[{minZ:.1f},{maxZ:.1f}]",
            end=""
        )

        time.sleep(0.05)

    print("\nCalibration complete.")

    # Hard-iron offset (center of min/max)
    offsetX = (maxX + minX) / 2
    offsetY = (maxY + minY) / 2
    offsetZ = (maxZ + minZ) / 2

    # Soft-iron scaling
    rangeX = maxX - minX
    rangeY = maxY - minY
    rangeZ = maxZ - minZ
    avgRange = (rangeX + rangeY + rangeZ) / 3

    scaleX = avgRange / rangeX if rangeX != 0 else 1
    scaleY = avgRange / rangeY if rangeY != 0 else 1
    scaleZ = avgRange / rangeZ if rangeZ != 0 else 1

    calibration = {
        "offsetX": offsetX,
        "offsetY": offsetY,
        "offsetZ": offsetZ,
        "scaleX": scaleX,
        "scaleY": scaleY,
        "scaleZ": scaleZ,
    }

    with open(CAL_FILE, "w") as f:
        json.dump(calibration, f, indent=4)

    print("\nSaved calibration:")
    print(json.dumps(calibration, indent=4))

    return calibration


def loadCalibration():
    try:
        with open(CAL_FILE, "r") as f:
            print("Loaded magnetometer calibration.")
            return json.load(f)
    except:
        print("No calibration file found, calibrating")
        fart = calibrateMagnetometer(imu)
        input("continue?")
        return fart


magCal = loadCalibration()


# ---------------------------
# Helpers
# ---------------------------
def constrain360(deg):
    while deg >= 360:
        deg -= 360
    while deg < 0:
        deg += 360
    return deg


def constrain180(deg):
    while deg > 180:
        deg -= 360
    while deg < -180:
        deg += 360
    return deg


def applyMagCal(mx, my, mz):
    # Apply hard + soft iron correction
    mx = (mx - magCal["offsetX"]) * magCal["scaleX"]
    my = (my - magCal["offsetY"]) * magCal["scaleY"]
    mz = (mz - magCal["offsetZ"]) * magCal["scaleZ"]
    # Negate Y to compensate for AK09916 axis inversion inside ICM20948
    my = -my
    return mx, my, mz


def altFromAccel(ax, ay, az):
    # Using equation from Analog Devices app note
    return math.degrees(math.atan2(-ax, math.sqrt(ay*ay + az*az)))


def azFromMagTiltComp(mx, my, mz, ax, ay, az):
    # Normalize accelerometer
    norm = math.sqrt(ax*ax + ay*ay + az*az)
    if norm == 0:
        return 0

    ax /= norm
    ay /= norm
    az /= norm

    # Pitch + roll
    pitch = math.asin(-ax)
    roll = math.atan2(ay, az)

    # Tilt compensation
    mx2 = mx * math.cos(pitch) + mz * math.sin(pitch)
    my2 = (
        mx * math.sin(roll) * math.sin(pitch)
        + my * math.cos(roll)
        - mz * math.sin(roll) * math.cos(pitch)
    )

    # Negated my2 per standard tilt-compensated heading formula
    angle = math.degrees(math.atan2(-my2, mx2))
    angle += DECLINATION

    return constrain360(angle)


# ---------------------------
# Gyro Calibration
# ---------------------------
print("Keep telescope still for gyro calibration...")

gyroXBias = gyroYBias = gyroZBias = 0
numSamples = 300

for _ in range(numSamples):
    gx, gy, gz = imu.gyro
    gyroXBias += gx
    gyroYBias += gy
    gyroZBias += gz
    time.sleep(0.01)

gyroXBias /= numSamples
gyroYBias /= numSamples
gyroZBias /= numSamples

print("Gyro calibrated")


# ---------------------------
# Initial Angles
# ---------------------------
ax, ay, az = imu.acceleration
mx, my, mz = applyMagCal(*imu.magnetic)

currAlt = altFromAccel(ax, ay, az)
currAz = azFromMagTiltComp(mx, my, mz, ax, ay, az)

print("Starting angles:")
print(f"Azimuth: {currAz}")
print(f"Altitude: {currAlt}")


# ---------------------------
# Logging
# ---------------------------
log = open("telescope_angles.csv", "w", newline="")
writer = csv.writer(log)
writer.writerow(["time", "azimuth", "altitude"])


# ---------------------------
# Main Loop
# ---------------------------
smoothedAX, smoothedAY, smoothedAZ = ax, ay, az
prev = time.time()

try:
    while True:
        now = time.time()
        dt = now - prev
        prev = now

        ax, ay, az = imu.acceleration
        gx, gy, gz = imu.gyro
        mx, my, mz = applyMagCal(*imu.magnetic)

        # Smooth accel (reduce noise)
        smoothedAX = NEW_ACCELERATION_WEIGHT * ax + (1 - NEW_ACCELERATION_WEIGHT) * smoothedAX
        smoothedAY = NEW_ACCELERATION_WEIGHT * ay + (1 - NEW_ACCELERATION_WEIGHT) * smoothedAY
        smoothedAZ = NEW_ACCELERATION_WEIGHT * az + (1 - NEW_ACCELERATION_WEIGHT) * smoothedAZ

        # Remove gyro bias
        gx -= gyroXBias
        gy -= gyroYBias
        gz -= gyroZBias

        # Integrate gyro
        azGyro = currAz + math.degrees(gz * dt)
        altGyro = currAlt + math.degrees(gy * dt)

        # Absolute angles
        azMag = azFromMagTiltComp(mx, my, mz, smoothedAX, smoothedAY, smoothedAZ)
        altMag = altFromAccel(smoothedAX, smoothedAY, smoothedAZ)

        # Wraparound fix
        azError = constrain180(azMag - azGyro)

        # Complementary filter
        currAz = constrain360(
            azGyro + (1 - AZIMUTH_GYRO_WEIGHT) * azError
        )

        currAlt = (
            ALTITUDE_GYRO_WEIGHT * altGyro +
            (1 - ALTITUDE_GYRO_WEIGHT) * altMag
        )

        print(f"\r\033[KAzimuth: {currAz:.2f}°, Altitude: {currAlt:.2f}°", end="", flush=True)

        writer.writerow([now, currAz, currAlt])
        log.flush()

        time.sleep(TIMESTEP)

except KeyboardInterrupt:
    print("\nStopped")
    log.close()