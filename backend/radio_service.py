import threading
import time
from dataclasses import dataclass
from typing import Optional

import numpy as np

HYDROGEN_LINE_HZ = 1420.40575177e6
CENTER_FREQ_HZ = HYDROGEN_LINE_HZ
SAMPLE_RATE_HZ = 2.4e6
FFT_SIZE = 1024
READ_SIZE = 4096
UPDATE_INTERVAL_SECONDS = 1.0


@dataclass
class RadioSnapshot:
    timestamp: float
    center_freq_hz: float
    peak_freq_hz: float
    peak_power_db: float
    source: str
    record_mode: str
    observation_mode: str
    integration_count: int
    bins_hz: list[float]
    power_db: list[float]
    averaged_power_db: list[float]
    calibrated_power_db: Optional[list[float]]
    cold_profile_db: Optional[list[float]]


class RadioDataService:
    """Continuously collects radio spectrum snapshots for API consumers."""

    def __init__(self):
        self._lock = threading.Lock()
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._snapshot: Optional[RadioSnapshot] = None
        self._status = "idle"
        self._error: Optional[str] = None
        self._sdr = None
        self._window = np.hanning(FFT_SIZE)
        self._record_mode = "average"  # "instant" | "average"
        self._observation_mode = "spectrum"  # "spectrum" | "hotcold"
        self._integration_sum: Optional[np.ndarray] = None
        self._integration_count = 0
        self._cold_profile: Optional[np.ndarray] = None

    def start(self):
        if self._thread and self._thread.is_alive():
            return

        self._status = "starting"
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)
        self._close_sdr()

    def get_payload(self) -> dict:
        with self._lock:
            snapshot = self._snapshot
            status = self._status
            error = self._error

        if snapshot is None:
            return {
                "status": status,
                "error": error,
                "data": None,
            }

        return {
            "status": status,
            "error": error,
            "data": {
                "timestamp": snapshot.timestamp,
                "center_freq_hz": snapshot.center_freq_hz,
                "peak_freq_hz": snapshot.peak_freq_hz,
                "peak_power_db": snapshot.peak_power_db,
                "source": snapshot.source,
                "record_mode": snapshot.record_mode,
                "observation_mode": snapshot.observation_mode,
                "integration_count": snapshot.integration_count,
                "bins_hz": snapshot.bins_hz,
                "power_db": snapshot.power_db,
                "averaged_power_db": snapshot.averaged_power_db,
                "calibrated_power_db": snapshot.calibrated_power_db,
                "cold_profile_db": snapshot.cold_profile_db,
            },
        }

    def set_modes(self, record_mode: Optional[str] = None, observation_mode: Optional[str] = None) -> None:
        with self._lock:
            if record_mode is not None:
                if record_mode not in ("instant", "average"):
                    raise ValueError("record_mode must be 'instant' or 'average'")
                self._record_mode = record_mode
                if record_mode == "instant":
                    self._integration_sum = None
                    self._integration_count = 0
            if observation_mode is not None:
                if observation_mode not in ("spectrum", "hotcold"):
                    raise ValueError("observation_mode must be 'spectrum' or 'hotcold'")
                self._observation_mode = observation_mode

    def capture_cold_profile(self) -> bool:
        with self._lock:
            if self._snapshot is None:
                return False
            self._cold_profile = np.array(self._snapshot.averaged_power_db, dtype=float)
            return True

    def _run(self):
        freqs = np.fft.fftshift(np.fft.fftfreq(FFT_SIZE, d=1.0 / SAMPLE_RATE_HZ)) + CENTER_FREQ_HZ
        use_simulated = not self._open_sdr()

        with self._lock:
            self._status = "simulated" if use_simulated else "running"

        while not self._stop_event.is_set():
            try:
                power_db = self._read_power_simulated(freqs) if use_simulated else self._read_power_hardware()
                with self._lock:
                    record_mode = self._record_mode
                    observation_mode = self._observation_mode

                if record_mode == "average":
                    if self._integration_sum is None:
                        self._integration_sum = np.zeros_like(power_db)
                        self._integration_count = 0
                    self._integration_sum += power_db
                    self._integration_count += 1
                    averaged_power = self._integration_sum / max(1, self._integration_count)
                else:
                    averaged_power = power_db
                    self._integration_sum = None
                    self._integration_count = 1

                calibrated = None
                if observation_mode == "hotcold" and self._cold_profile is not None:
                    calibrated = averaged_power - self._cold_profile
                    peak_source = calibrated
                else:
                    peak_source = averaged_power

                peak_idx = int(np.argmax(peak_source))

                snapshot = RadioSnapshot(
                    timestamp=time.time(),
                    center_freq_hz=CENTER_FREQ_HZ,
                    peak_freq_hz=float(freqs[peak_idx]),
                    peak_power_db=float(peak_source[peak_idx]),
                    source="simulation" if use_simulated else "rtl-sdr",
                    record_mode=record_mode,
                    observation_mode=observation_mode,
                    integration_count=int(self._integration_count),
                    bins_hz=freqs.astype(float).tolist(),
                    power_db=power_db.astype(float).tolist(),
                    averaged_power_db=averaged_power.astype(float).tolist(),
                    calibrated_power_db=calibrated.astype(float).tolist() if calibrated is not None else None,
                    cold_profile_db=self._cold_profile.astype(float).tolist() if self._cold_profile is not None else None,
                )

                with self._lock:
                    self._snapshot = snapshot
                    self._error = None
            except Exception as exc:
                with self._lock:
                    self._status = "error"
                    self._error = str(exc)

            time.sleep(UPDATE_INTERVAL_SECONDS)

    def _open_sdr(self) -> bool:
        try:
            from rtlsdr import RtlSdr

            self._sdr = RtlSdr()
            self._sdr.sample_rate = SAMPLE_RATE_HZ
            self._sdr.center_freq = CENTER_FREQ_HZ
            self._sdr.gain = "auto"
            return True
        except Exception as exc:
            self._error = f"RTL-SDR unavailable, using simulated radio data: {exc}"
            self._sdr = None
            return False

    def _close_sdr(self):
        if self._sdr is None:
            return
        try:
            self._sdr.close()
        except Exception:
            pass
        self._sdr = None

    def _read_power_hardware(self) -> np.ndarray:
        if self._sdr is None:
            raise RuntimeError("RTL-SDR is not connected")

        samples = self._sdr.read_samples(READ_SIZE)
        x = samples[:FFT_SIZE]
        x = x - np.mean(x)
        x = x * self._window
        spectrum = np.fft.fftshift(np.fft.fft(x))
        return 20.0 * np.log10(np.abs(spectrum) + 1e-12)

    def _read_power_simulated(self, freqs: np.ndarray) -> np.ndarray:
        noise = np.random.normal(loc=-95.0, scale=2.0, size=FFT_SIZE)
        drift_hz = np.sin(time.time() / 10.0) * 20000.0
        gaussian = 14.0 * np.exp(-((freqs - (HYDROGEN_LINE_HZ + drift_hz)) ** 2) / (2 * (45000.0 ** 2)))
        return noise + gaussian
