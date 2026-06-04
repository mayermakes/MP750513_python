import socket
import time


class MP750513:
    """
    Simple SCPI driver for Multicomp-Pro MP750513 Arbitrary Waveform Generator.
    Designed to be stable, blocking, and safe (no polling loops inside).

    Supports both channels. Pass channel=1 or channel=2 to each method,
    or set a default channel on the instance via set_channel().
    """

    def __init__(self, ip, port=5025, timeout=2, channel=1):
        self.ip = ip
        self.port = port
        self.timeout = timeout
        self.channel = channel  # default channel

        self._connect()

    # -----------------------------
    # CHANNEL SELECTION
    # -----------------------------
    def set_channel(self, channel: int):
        """Set the default channel (1 or 2) for subsequent commands."""
        if channel not in (1, 2):
            raise ValueError("Channel must be 1 or 2")
        self.channel = channel

    def get_channel(self):
        """Return the current default channel."""
        return self.channel

    def _ch(self, channel=None) -> int:
        """Resolve channel: use argument if given, else fall back to self.channel."""
        ch = channel if channel is not None else self.channel
        if ch not in (1, 2):
            raise ValueError(f"Invalid channel: {ch}. Must be 1 or 2.")
        return ch

    def _src(self, channel=None) -> str:
        """Return the SOURCE prefix for a given channel, e.g. 'SOURCE1'."""
        return f"SOURCE{self._ch(channel)}"

    # -----------------------------
    # CONNECTION
    # -----------------------------
    def _connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(self.timeout)
        self.sock.connect((self.ip, self.port))
        time.sleep(0.2)

    def _reconnect(self):
        try:
            self.sock.close()
        except Exception:
            pass
        time.sleep(0.5)
        self._connect()

    # -----------------------------
    # LOW LEVEL IO
    # -----------------------------
    def write(self, cmd):
        try:
            self.sock.sendall((cmd + "\n").encode())
            time.sleep(0.1)
        except Exception:
            self._reconnect()
            self.sock.sendall((cmd + "\n").encode())
            time.sleep(0.1)

    def query(self, cmd):
        try:
            self.sock.sendall((cmd + "\n").encode())
            time.sleep(0.25)
            return self.sock.recv(1024).decode().strip()
        except Exception:
            self._reconnect()
            self.sock.sendall((cmd + "\n").encode())
            time.sleep(0.25)
            return self.sock.recv(1024).decode().strip()

    # Connection verification
    def is_connected(self):
        try:
            self.query("*IDN?")
            return True
        except Exception:
            return False

    # Get device ID
    def get_id(self):
        return self.query("*IDN?")

    # -----------------------------
    # OUTPUT CONTROL
    # Output commands use OUTPUT{N}, which is separate from SOURCE{N}
    # -----------------------------
    def output_on(self, channel=None):
        self.write(f"OUTPUT{self._ch(channel)} 1")

    def output_off(self, channel=None):
        self.write(f"OUTPUT{self._ch(channel)} 0")

    def get_output_state(self, channel=None):
        return self.query(f"OUTPUT{self._ch(channel)}?")

    # Aliases for consistency
    def enable(self, channel=None):
        self.output_on(channel)

    def disable(self, channel=None):
        self.output_off(channel)

    # -----------------------------
    # FREQUENCY
    # -----------------------------
    def set_frequency(self, freq: float, channel=None):
        """Set frequency in Hz."""
        self.write(f"{self._src(channel)}:FREQ {freq}")

    def get_frequency(self, channel=None):
        """Get current frequency in Hz."""
        return self.query(f"{self._src(channel)}:FREQ?")

    # -----------------------------
    # AMPLITUDE
    # -----------------------------
    def set_amplitude(self, amplitude: float, channel=None):
        """Set amplitude in Volts."""
        self.write(f"{self._src(channel)}:VOLT {amplitude}")

    def get_amplitude(self, channel=None):
        """Get current amplitude in Volts."""
        return self.query(f"{self._src(channel)}:VOLT?")

    # Alias for VOLT
    def set_voltage(self, voltage: float, channel=None):
        self.set_amplitude(voltage, channel)

    def get_voltage(self, channel=None):
        return self.get_amplitude(channel)

    # -----------------------------
    # DC OFFSET
    # -----------------------------
    def set_dc_offset(self, offset: float, channel=None):
        """Set DC offset in Volts."""
        self.write(f"{self._src(channel)}:VOLT:OFFS {offset}")

    def get_dc_offset(self, channel=None):
        """Get current DC offset in Volts."""
        return self.query(f"{self._src(channel)}:VOLT:OFFS?")

    # Alias
    def set_offset(self, offset: float, channel=None):
        self.set_dc_offset(offset, channel)

    def get_offset(self, channel=None):
        return self.get_dc_offset(channel)

    # -----------------------------
    # WAVEFORM TYPE
    # -----------------------------
    def set_waveform(self, waveform: str, channel=None):
        """Set waveform type: SIN, SQU, TRI, RAMP, etc."""
        self.write(f"{self._src(channel)}:FUNC {waveform}")

    def get_waveform(self, channel=None):
        """Get current waveform type."""
        return self.query(f"{self._src(channel)}:FUNC?")

    # Convenience methods for common waveforms
    def set_sine(self, channel=None):
        self.set_waveform("SIN", channel)

    def set_square(self, channel=None):
        self.set_waveform("SQU", channel)

    def set_triangle(self, channel=None):
        self.set_waveform("TRI", channel)

    def set_ramp(self, channel=None):
        self.set_waveform("RAMP", channel)

    # -----------------------------
    # PHASE
    # -----------------------------
    def set_phase(self, phase: float, channel=None):
        """Set phase in degrees."""
        self.write(f"{self._src(channel)}:PHAS {phase}")

    def get_phase(self, channel=None):
        """Get current phase in degrees."""
        return self.query(f"{self._src(channel)}:PHAS?")

    # -----------------------------
    # DUTY CYCLE (for square waves)
    # -----------------------------
    def set_duty_cycle(self, duty: float, channel=None):
        """Set duty cycle as percentage (0-100)."""
        self.write(f"{self._src(channel)}:FUNC:SQU:DCYC {duty}")

    def get_duty_cycle(self, channel=None):
        """Get current duty cycle percentage."""
        return self.query(f"{self._src(channel)}:FUNC:SQU:DCYC?")

    # -----------------------------
    # BURST MODE
    # -----------------------------
    def set_burst_mode(self, mode: str, channel=None):
        """Set burst mode: TRIGgered or MANUAL."""
        self.write(f"{self._src(channel)}:BURS:MODE {mode}")

    def get_burst_mode(self, channel=None):
        return self.query(f"{self._src(channel)}:BURS:MODE?")

    def enable_burst(self, channel=None):
        self.write(f"{self._src(channel)}:BURS ON")

    def disable_burst(self, channel=None):
        self.write(f"{self._src(channel)}:BURS OFF")

    def set_burst_cycles(self, cycles: int, channel=None):
        """Set number of cycles in burst."""
        self.write(f"{self._src(channel)}:BURS:NCYC {cycles}")

    def get_burst_cycles(self, channel=None):
        return self.query(f"{self._src(channel)}:BURS:NCYC?")

    # Trigger burst (global command, no channel prefix needed)
    def trigger_burst(self):
        self.write("*TRG")

    # Alias
    def trigger(self):
        self.trigger_burst()
