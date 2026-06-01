"""
MP750513 two-channel Arbitrary Waveform Generator driver.
Protocol: SCPI over TCP socket (port 5025).

Each channel is addressed with the standard SCPI SOURce<n> / OUTPut<n>
prefix.  The driver exposes every parameter both via per-channel methods
(set_frequency(freq, channel=1)) and via a thin ChannelProxy object so
callers can write:

    awg.ch1.set_frequency(1000)
    awg.ch2.set_square()
"""

import socket
import time
import threading
from typing import Literal

VALID_CHANNELS = (1, 2)
VALID_WAVEFORMS = ("SIN", "SQU", "TRI", "RAMP")


class AWGError(Exception):
    """Raised when the instrument returns an error or is unreachable."""


class ChannelProxy:
    """
    Thin proxy that binds a fixed channel number to the parent driver.

    Usage::

        awg = MP750513("192.168.1.97")
        awg.ch1.set_sine()
        awg.ch1.set_frequency(1000)
        awg.ch1.output_on()
    """

    def __init__(self, driver: "MP750513", channel: int) -> None:
        self._driver = driver
        self._channel = channel

    # --- output -----------------------------------------------------------
    def output_on(self) -> None:
        self._driver.output_on(self._channel)

    def output_off(self) -> None:
        self._driver.output_off(self._channel)

    def enable(self) -> None:
        self._driver.output_on(self._channel)

    def disable(self) -> None:
        self._driver.output_off(self._channel)

    def get_output_state(self) -> bool:
        return self._driver.get_output_state(self._channel)

    # --- frequency --------------------------------------------------------
    def set_frequency(self, freq: float) -> None:
        self._driver.set_frequency(freq, self._channel)

    def get_frequency(self) -> float:
        return self._driver.get_frequency(self._channel)

    # --- amplitude --------------------------------------------------------
    def set_amplitude(self, amp: float) -> None:
        self._driver.set_amplitude(amp, self._channel)

    def get_amplitude(self) -> float:
        return self._driver.get_amplitude(self._channel)

    def set_voltage(self, volt: float) -> None:
        self._driver.set_amplitude(volt, self._channel)

    def get_voltage(self) -> float:
        return self._driver.get_amplitude(self._channel)

    # --- DC offset --------------------------------------------------------
    def set_dc_offset(self, offset: float) -> None:
        self._driver.set_dc_offset(offset, self._channel)

    def get_dc_offset(self) -> float:
        return self._driver.get_dc_offset(self._channel)

    def set_offset(self, offset: float) -> None:
        self._driver.set_dc_offset(offset, self._channel)

    def get_offset(self) -> float:
        return self._driver.get_dc_offset(self._channel)

    # --- waveform ---------------------------------------------------------
    def set_waveform(self, waveform: str) -> None:
        self._driver.set_waveform(waveform, self._channel)

    def get_waveform(self) -> str:
        return self._driver.get_waveform(self._channel)

    def set_sine(self) -> None:
        self._driver.set_sine(self._channel)

    def set_square(self) -> None:
        self._driver.set_square(self._channel)

    def set_triangle(self) -> None:
        self._driver.set_triangle(self._channel)

    def set_ramp(self) -> None:
        self._driver.set_ramp(self._channel)

    # --- phase ------------------------------------------------------------
    def set_phase(self, phase: float) -> None:
        self._driver.set_phase(phase, self._channel)

    def get_phase(self) -> float:
        return self._driver.get_phase(self._channel)

    # --- duty cycle -------------------------------------------------------
    def set_duty_cycle(self, duty: float) -> None:
        self._driver.set_duty_cycle(duty, self._channel)

    def get_duty_cycle(self) -> float:
        return self._driver.get_duty_cycle(self._channel)

    # --- burst ------------------------------------------------------------
    def enable_burst(self) -> None:
        self._driver.enable_burst(self._channel)

    def disable_burst(self) -> None:
        self._driver.disable_burst(self._channel)

    def set_burst_mode(self, mode: str) -> None:
        self._driver.set_burst_mode(mode, self._channel)

    def get_burst_mode(self) -> str:
        return self._driver.get_burst_mode(self._channel)

    def set_burst_cycles(self, cycles: int) -> None:
        self._driver.set_burst_cycles(cycles, self._channel)

    def get_burst_cycles(self) -> int:
        return self._driver.get_burst_cycles(self._channel)

    def trigger_burst(self) -> None:
        self._driver.trigger_burst(self._channel)

    def trigger(self) -> None:
        self._driver.trigger_burst(self._channel)

    def __repr__(self) -> str:
        return f"<ChannelProxy ch{self._channel} of {self._driver!r}>"


class MP750513:
    """
    Driver for the Multicomp Pro MP750513 two-channel AWG.

    Parameters
    ----------
    ip : str
        Instrument IP address.
    port : int
        TCP port (default 5025).
    timeout : float
        Socket timeout in seconds (default 2).

    Channel addressing
    ------------------
    All methods that operate on a single channel accept an optional
    ``channel`` keyword argument (1 or 2, default 1).

    Alternatively use the ``ch1`` / ``ch2`` proxy attributes::

        awg = MP750513("192.168.1.97")
        awg.ch1.set_sine()
        awg.ch2.set_square()
        awg.ch1.output_on()
        awg.ch2.output_on()
    """

    def __init__(self, ip: str, port: int = 5025, timeout: float = 2) -> None:
        self._ip = ip
        self._port = port
        self._timeout = timeout
        self._sock: socket.socket | None = None
        self._lock = threading.Lock()

        # Convenient per-channel proxy attributes
        self.ch1 = ChannelProxy(self, 1)
        self.ch2 = ChannelProxy(self, 2)

    # ------------------------------------------------------------------ #
    # Internal helpers                                                     #
    # ------------------------------------------------------------------ #

    def _connect(self) -> None:
        """Open TCP socket if not already open."""
        if self._sock is not None:
            return
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(self._timeout)
        try:
            sock.connect((self._ip, self._port))
        except OSError as exc:
            sock.close()
            raise AWGError(f"Cannot connect to {self._ip}:{self._port}: {exc}") from exc
        self._sock = sock

    def _disconnect(self) -> None:
        if self._sock is not None:
            try:
                self._sock.close()
            except OSError:
                pass
            self._sock = None

    def _send(self, cmd: str) -> None:
        """Send a command string (no response expected)."""
        with self._lock:
            self._connect()
            try:
                self._sock.sendall((cmd + "\n").encode())
            except OSError:
                self._disconnect()
                self._connect()
                self._sock.sendall((cmd + "\n").encode())

    def _query(self, cmd: str) -> str:
        """Send a query and return the stripped response."""
        with self._lock:
            self._connect()
            try:
                self._sock.sendall((cmd + "\n").encode())
                return self._recv()
            except OSError:
                self._disconnect()
                self._connect()
                self._sock.sendall((cmd + "\n").encode())
                return self._recv()

    def _recv(self) -> str:
        buf = b""
        while True:
            chunk = self._sock.recv(4096)
            if not chunk:
                break
            buf += chunk
            if buf.endswith(b"\n"):
                break
        return buf.decode().strip()

    @staticmethod
    def _validate_channel(channel: int) -> int:
        if channel not in VALID_CHANNELS:
            raise ValueError(f"channel must be 1 or 2, got {channel!r}")
        return channel

    @staticmethod
    def _src(channel: int) -> str:
        """Return the SOURce prefix for a channel, e.g. 'SOURce1'."""
        return f"SOURce{channel}"

    @staticmethod
    def _out(channel: int) -> str:
        """Return the OUTPut prefix for a channel, e.g. 'OUTPut1'."""
        return f"OUTPut{channel}"

    # ------------------------------------------------------------------ #
    # Device info                                                          #
    # ------------------------------------------------------------------ #

    def get_id(self) -> str:
        """Query the instrument identification string (*IDN?)."""
        return self._query("*IDN?")

    def is_connected(self) -> bool:
        """Return True if the instrument responds to *IDN?."""
        try:
            self.get_id()
            return True
        except AWGError:
            return False

    # ------------------------------------------------------------------ #
    # Output control                                                       #
    # ------------------------------------------------------------------ #

    def output_on(self, channel: int = 1) -> None:
        """Enable the output of *channel*."""
        ch = self._validate_channel(channel)
        self._send(f"{self._out(ch)} ON")

    def output_off(self, channel: int = 1) -> None:
        """Disable the output of *channel*."""
        ch = self._validate_channel(channel)
        self._send(f"{self._out(ch)} OFF")

    def enable(self, channel: int = 1) -> None:
        """Alias for :meth:`output_on`."""
        self.output_on(channel)

    def disable(self, channel: int = 1) -> None:
        """Alias for :meth:`output_off`."""
        self.output_off(channel)

    def get_output_state(self, channel: int = 1) -> bool:
        """Return True if the output of *channel* is enabled."""
        ch = self._validate_channel(channel)
        resp = self._query(f"{self._out(ch)}?")
        return resp.strip().upper() in ("1", "ON")

    def all_outputs_on(self) -> None:
        """Enable both channel outputs simultaneously."""
        for ch in VALID_CHANNELS:
            self.output_on(ch)

    def all_outputs_off(self) -> None:
        """Disable both channel outputs simultaneously."""
        for ch in VALID_CHANNELS:
            self.output_off(ch)

    # ------------------------------------------------------------------ #
    # Frequency                                                            #
    # ------------------------------------------------------------------ #

    def set_frequency(self, freq: float, channel: int = 1) -> None:
        """Set the output frequency of *channel* in Hz."""
        ch = self._validate_channel(channel)
        self._send(f"{self._src(ch)}:FREQuency {freq:.6f}")

    def get_frequency(self, channel: int = 1) -> float:
        """Return the output frequency of *channel* in Hz."""
        ch = self._validate_channel(channel)
        return float(self._query(f"{self._src(ch)}:FREQuency?"))

    # ------------------------------------------------------------------ #
    # Amplitude                                                            #
    # ------------------------------------------------------------------ #

    def set_amplitude(self, amp: float, channel: int = 1) -> None:
        """Set the output amplitude of *channel* in Volts (peak-to-peak)."""
        ch = self._validate_channel(channel)
        self._send(f"{self._src(ch)}:VOLTage {amp:.6f}")

    def get_amplitude(self, channel: int = 1) -> float:
        """Return the output amplitude of *channel* in Volts."""
        ch = self._validate_channel(channel)
        return float(self._query(f"{self._src(ch)}:VOLTage?"))

    def set_voltage(self, volt: float, channel: int = 1) -> None:
        """Alias for :meth:`set_amplitude`."""
        self.set_amplitude(volt, channel)

    def get_voltage(self, channel: int = 1) -> float:
        """Alias for :meth:`get_amplitude`."""
        return self.get_amplitude(channel)

    # ------------------------------------------------------------------ #
    # DC offset                                                            #
    # ------------------------------------------------------------------ #

    def set_dc_offset(self, offset: float, channel: int = 1) -> None:
        """Set the DC offset of *channel* in Volts."""
        ch = self._validate_channel(channel)
        self._send(f"{self._src(ch)}:VOLTage:OFFSet {offset:.6f}")

    def get_dc_offset(self, channel: int = 1) -> float:
        """Return the DC offset of *channel* in Volts."""
        ch = self._validate_channel(channel)
        return float(self._query(f"{self._src(ch)}:VOLTage:OFFSet?"))

    def set_offset(self, offset: float, channel: int = 1) -> None:
        """Alias for :meth:`set_dc_offset`."""
        self.set_dc_offset(offset, channel)

    def get_offset(self, channel: int = 1) -> float:
        """Alias for :meth:`get_dc_offset`."""
        return self.get_dc_offset(channel)

    # ------------------------------------------------------------------ #
    # Waveform type                                                        #
    # ------------------------------------------------------------------ #

    def set_waveform(self, waveform: str, channel: int = 1) -> None:
        """
        Set the waveform type of *channel*.

        Parameters
        ----------
        waveform : str
            One of ``SIN``, ``SQU``, ``TRI``, ``RAMP``.
        channel : int
            1 or 2 (default 1).
        """
        ch = self._validate_channel(channel)
        wf = waveform.upper()
        if wf not in VALID_WAVEFORMS:
            raise ValueError(
                f"waveform must be one of {VALID_WAVEFORMS}, got {waveform!r}"
            )
        self._send(f"{self._src(ch)}:FUNCtion {wf}")

    def get_waveform(self, channel: int = 1) -> str:
        """Return the active waveform type of *channel*."""
        ch = self._validate_channel(channel)
        return self._query(f"{self._src(ch)}:FUNCtion?")

    def set_sine(self, channel: int = 1) -> None:
        """Set *channel* to sine wave."""
        self.set_waveform("SIN", channel)

    def set_square(self, channel: int = 1) -> None:
        """Set *channel* to square wave."""
        self.set_waveform("SQU", channel)

    def set_triangle(self, channel: int = 1) -> None:
        """Set *channel* to triangle wave."""
        self.set_waveform("TRI", channel)

    def set_ramp(self, channel: int = 1) -> None:
        """Set *channel* to ramp wave."""
        self.set_waveform("RAMP", channel)

    # ------------------------------------------------------------------ #
    # Phase                                                                #
    # ------------------------------------------------------------------ #

    def set_phase(self, phase: float, channel: int = 1) -> None:
        """Set the phase of *channel* in degrees."""
        ch = self._validate_channel(channel)
        self._send(f"{self._src(ch)}:PHASe {phase:.4f}")

    def get_phase(self, channel: int = 1) -> float:
        """Return the phase of *channel* in degrees."""
        ch = self._validate_channel(channel)
        return float(self._query(f"{self._src(ch)}:PHASe?"))

    # ------------------------------------------------------------------ #
    # Duty cycle                                                           #
    # ------------------------------------------------------------------ #

    def set_duty_cycle(self, duty: float, channel: int = 1) -> None:
        """
        Set the duty cycle of *channel* (square wave) as a percentage 0–100.
        """
        ch = self._validate_channel(channel)
        self._send(f"{self._src(ch)}:FUNCtion:SQUare:DCYCle {duty:.2f}")

    def get_duty_cycle(self, channel: int = 1) -> float:
        """Return the duty cycle of *channel* as a percentage."""
        ch = self._validate_channel(channel)
        return float(self._query(f"{self._src(ch)}:FUNCtion:SQUare:DCYCle?"))

    # ------------------------------------------------------------------ #
    # Burst mode                                                           #
    # ------------------------------------------------------------------ #

    def enable_burst(self, channel: int = 1) -> None:
        """Enable burst mode on *channel*."""
        ch = self._validate_channel(channel)
        self._send(f"{self._src(ch)}:BURSt:STATe ON")

    def disable_burst(self, channel: int = 1) -> None:
        """Disable burst mode on *channel*."""
        ch = self._validate_channel(channel)
        self._send(f"{self._src(ch)}:BURSt:STATe OFF")

    def set_burst_mode(self, mode: str, channel: int = 1) -> None:
        """
        Set the burst trigger mode of *channel*.

        Parameters
        ----------
        mode : str
            ``TRIGgered`` or ``MANUAL``.
        channel : int
            1 or 2 (default 1).
        """
        ch = self._validate_channel(channel)
        self._send(f"{self._src(ch)}:BURSt:MODE {mode}")

    def get_burst_mode(self, channel: int = 1) -> str:
        """Return the burst trigger mode of *channel*."""
        ch = self._validate_channel(channel)
        return self._query(f"{self._src(ch)}:BURSt:MODE?")

    def set_burst_cycles(self, cycles: int, channel: int = 1) -> None:
        """Set the number of cycles per burst on *channel*."""
        ch = self._validate_channel(channel)
        self._send(f"{self._src(ch)}:BURSt:NCYCles {int(cycles)}")

    def get_burst_cycles(self, channel: int = 1) -> int:
        """Return the burst cycle count of *channel*."""
        ch = self._validate_channel(channel)
        return int(float(self._query(f"{self._src(ch)}:BURSt:NCYCles?")))

    def trigger_burst(self, channel: int = 1) -> None:
        """Software-trigger a burst on *channel*."""
        ch = self._validate_channel(channel)
        self._send(f"{self._src(ch)}:BURSt:TRIGger")

    def trigger(self, channel: int = 1) -> None:
        """Alias for :meth:`trigger_burst`."""
        self.trigger_burst(channel)

    # ------------------------------------------------------------------ #
    # Phase coupling / synchronisation helpers                             #
    # ------------------------------------------------------------------ #

    def align_phases(self) -> None:
        """
        Reset the phase accumulators of both channels simultaneously so
        that CH1 and CH2 start from the same point in their cycle.
        Useful when using the two channels as a quadrature or differential
        pair.
        """
        self._send("PHASe:ALIGn")

    # ------------------------------------------------------------------ #
    # Snapshot / measure                                                   #
    # ------------------------------------------------------------------ #

    def get_channel_state(self, channel: int = 1) -> dict:
        """
        Return a dictionary of all current settings for *channel*.

        Returns
        -------
        dict with keys: channel, waveform, frequency_hz, amplitude_v,
        dc_offset_v, phase_deg, duty_cycle_pct, output_on,
        burst_enabled, burst_mode, burst_cycles.
        """
        ch = self._validate_channel(channel)
        wf = self.get_waveform(ch)
        duty = self.get_duty_cycle(ch) if wf.upper() in ("SQU",) else None
        return {
            "channel": ch,
            "waveform": wf,
            "frequency_hz": self.get_frequency(ch),
            "amplitude_v": self.get_amplitude(ch),
            "dc_offset_v": self.get_dc_offset(ch),
            "phase_deg": self.get_phase(ch),
            "duty_cycle_pct": duty,
            "output_on": self.get_output_state(ch),
            "burst_mode": self.get_burst_mode(ch),
            "burst_cycles": self.get_burst_cycles(ch),
        }

    def get_all_state(self) -> dict:
        """Return a snapshot of settings for both channels."""
        return {
            "ch1": self.get_channel_state(1),
            "ch2": self.get_channel_state(2),
        }

    # ------------------------------------------------------------------ #
    # Context manager support                                              #
    # ------------------------------------------------------------------ #

    def close(self) -> None:
        """Close the TCP connection."""
        self._disconnect()

    def __enter__(self) -> "MP750513":
        self._connect()
        return self

    def __exit__(self, *_) -> None:
        self.close()

    def __repr__(self) -> str:
        return f"MP750513(ip={self._ip!r}, port={self._port})"
