import qwiic_icm20948
import time
import sys


def runExample():
    print("SparkFun 9DoF ICM-20948 Sensor Example 1")

    IMU = qwiic_icm20948.QwiicIcm20948()

    if IMU.connected == False:
        print(
            "The Qwiic ICM20948 device isn't connected to the system. Please check your connection",
            file=sys.stderr
        )
        return

    IMU.begin()

    prev_line = None

    while True:
        if IMU.dataReady():
            IMU.getAgmt()

            line = (
                f"ax:{IMU.axRaw:6d} "
                f"ay:{IMU.ayRaw:6d} "
                f"az:{IMU.azRaw:6d} "
                f"gx:{IMU.gxRaw:6d} "
                f"gy:{IMU.gyRaw:6d} "
                f"gz:{IMU.gzRaw:6d} "
                f"mx:{IMU.mxRaw:6d} "
                f"my:{IMU.myRaw:6d} "
                f"mz:{IMU.mzRaw:6d}"
            )

            if line != prev_line:
                sys.stdout.write("\033[0G\033[2K" + line)
                sys.stdout.flush()
                prev_line = line

            time.sleep(0.03)

        else:
            sys.stdout.write("\033[0G\033[2KWaiting for data")
            sys.stdout.flush()
            time.sleep(0.5)


if __name__ == '__main__':
    try:
        runExample()
    except (KeyboardInterrupt, SystemExit):
        sys.stdout.write("\nEnding Example 1\n")
        sys.stdout.flush()
        sys.exit(0)