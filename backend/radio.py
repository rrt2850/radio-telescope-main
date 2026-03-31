"""
radio.py

Fixed-purpose live spectrum viewer for observing around the hydrogen line
with an RTL-SDR device.

The neutral hydrogen spectral line is centered at:
    1420.40575177 MHz

Dependencies:
    pip install pyrtlsdr numpy matplotlib

System packages needed on Raspberry Pi:
    sudo apt update
    sudo apt install rtl-sdr librtlsdr-dev
"""

import sys
import signal

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from rtlsdr import RtlSdr


# Hydrogen line center frequency in Hz
HYDROGEN_LINE_HZ = 1420.40575177e6

# RTL-SDR tuning
CENTER_FREQ_HZ = HYDROGEN_LINE_HZ
SAMPLE_RATE_HZ = 2.4e6
GAIN = "auto"              # "auto" or a float like 35.7

# FFT / plotting
FFT_SIZE = 16384
READ_SIZE = 262144
UPDATE_INTERVAL_MS = 250
PLOT_TITLE = "RTL-SDR Hydrogen Line Live Spectrum"

# Display behavior
SMOOTHING_ALPHA = 0.25     # 0..1 ; lower = smoother/slower
REMOVE_DC = True
USE_WINDOW = True

# Optional fixed Y-axis range. Set to None for auto scaling.
Y_MIN_DB = None
Y_MAX_DB = None

def resolveGain(gain_value):
    if isinstance(gain_value, str) and gain_value.lower() == "auto":
        return "auto"
    return float(gain_value)


def main():
    if FFT_SIZE <= 0:
        raise ValueError("FFT_SIZE must be > 0")
    if READ_SIZE < FFT_SIZE:
        raise ValueError("READ_SIZE must be >= FFT_SIZE")
    if SAMPLE_RATE_HZ <= 0:
        raise ValueError("SAMPLE_RATE_HZ must be > 0")
    if CENTER_FREQ_HZ <= 0:
        raise ValueError("CENTER_FREQ_HZ must be > 0")
    if not (0.0 < SMOOTHING_ALPHA <= 1.0):
        raise ValueError("SMOOTHING_ALPHA must be in (0, 1]")

    sdr = RtlSdr()
    sdr.sample_rate = SAMPLE_RATE_HZ
    sdr.center_freq = CENTER_FREQ_HZ
    sdr.gain = resolveGain(GAIN)

    freqs = np.fft.fftshift(np.fft.fftfreq(FFT_SIZE, d=1.0 / SAMPLE_RATE_HZ))
    freqs_mhz = (freqs + CENTER_FREQ_HZ) / 1e6

    fig, ax = plt.subplots()
    line, = ax.plot(freqs_mhz, np.full(FFT_SIZE, -120.0))
    ax.set_title(PLOT_TITLE)
    ax.set_xlabel("Frequency (MHz)")
    ax.set_ylabel("Power (dB)")
    ax.grid(True)

    # Mark the hydrogen line on the graph
    ax.axvline(HYDROGEN_LINE_HZ / 1e6, linestyle="--", alpha=0.8)

    smoothed = None

    def cleanupAndExit(*_):
        try:
            sdr.close()
        except Exception:
            pass
        plt.close("all")

    signal.signal(signal.SIGINT, cleanupAndExit)
    signal.signal(signal.SIGTERM, cleanupAndExit)

    def update(_frame):
        nonlocal smoothed

        samples = sdr.read_samples(READ_SIZE)
        x = samples[:FFT_SIZE]

        if REMOVE_DC:
            x = x - np.mean(x)

        if USE_WINDOW:
            x = x * np.hanning(len(x))

        spectrum = np.fft.fftshift(np.fft.fft(x))
        power_db = 20.0 * np.log10(np.abs(spectrum) + 1e-12)

        if smoothed is None:
            smoothed = power_db
        else:
            smoothed = SMOOTHING_ALPHA * power_db + (1.0 - SMOOTHING_ALPHA) * smoothed

        line.set_ydata(smoothed)

        if Y_MIN_DB is None or Y_MAX_DB is None:
            ax.set_ylim(float(np.min(smoothed) - 5), float(np.max(smoothed) + 5))
        else:
            ax.set_ylim(Y_MIN_DB, Y_MAX_DB)

        peak_idx = int(np.argmax(smoothed))
        peak_freq_mhz = freqs_mhz[peak_idx]
        peak_power_db = smoothed[peak_idx]

        ax.set_title(
            f"{PLOT_TITLE}\n"
            f"Center: {CENTER_FREQ_HZ/1e6:.6f} MHz | "
            f"H line: {HYDROGEN_LINE_HZ/1e6:.6f} MHz | "
            f"Peak: {peak_freq_mhz:.6f} MHz @ {peak_power_db:.1f} dB"
        )

        return (line,)

    FuncAnimation(
        fig,
        update,
        interval=UPDATE_INTERVAL_MS,
        blit=True,
        cache_frame_data=False,
    )

    try:
        plt.show()
    finally:
        try:
            sdr.close()
        except Exception:
            pass


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)