import time
import math
import board
import adafruit_mmc56x3

i2c = board.I2C()
mag = adafruit_mmc56x3.MMC5603(i2c)

# Hard-iron offsets: update these after calibration
OFFSET_X = 0.0
OFFSET_Y = 0.0

# Magnetic declination for your location.
# Example: west is negative, east is positive.
DECLINATION_DEG = 0.0

def heading_deg(x_uT, y_uT):
    x = x_uT - OFFSET_X
    y = y_uT - OFFSET_Y

    heading = math.degrees(math.atan2(y, x))
    heading += DECLINATION_DEG

    heading %= 360.0
    return heading

while True:
    x, y, z = mag.magnetic
    heading = heading_deg(x, y)

    print(f"X={x:8.2f} uT  Y={y:8.2f} uT  Z={z:8.2f} uT  heading={heading:6.1f}°")
    time.sleep(0.1)