import socket
import time


class MP750513:
    """
    Simple SCPI driver for Multicomp-Pro MP750513 Arbitrary Waveform Generator.
    Designed to be stable, blocking, and safe (no polling loops inside).
    """

    def __init__(self, ip, port=5025, timeout=2):
        self.ip = ip
        self.port = port
        self.timeout = timeout

        self._connect()

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
        except:
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
        except:
            self._reconnect()
            self.sock.sendall((cmd + "\n").encode())
            time.sleep(0.1)

    def query(self, cmd):
        try:
            self.sock.sendall((cmd + "\n").encode())
            time.sleep(0.25)
            return self.sock.recv(1024).decode().strip()
        except:
            self._reconnect()
            self.sock.sendall((cmd + "\n").encode())
            time.sleep(0.25)
            return self.sock.recv(1024).decode().strip()

    # Connection verification
    def is_connected(self):
        try:
            self.query("*IDN?")
            return True
        except:
            return False

    # Get device ID
    def get_id(self):
        return self.query("*IDN?")

    # -----------------------------
    # OUTPUT CONTROL
    # -----------------------------
    def output_on(self):
        self.write("OUTP 1")

    def output_off(self):
        self.write("OUTP 0")

    def get_output_state(self):
        return self.query("OUTP?")

    # Aliases for consistency
    def enable(self):
        self.output_on()

    def disable(self):
        self.output_off()

    # -----------------------------
    # FREQUENCY
    # -----------------------------
    def set_frequency(self, freq: float):
        """Set frequency in Hz"""
        self.write(f":FREQ {freq}")

    def get_frequency(self):
        """Get current frequency in Hz"""
        return self.query(":FREQ?")

    # -----------------------------
    # AMPLITUDE
    # -----------------------------
    def set_amplitude(self, amplitude: float):
        """Set amplitude in Volts"""
        self.write(f":VOLT {amplitude}")

    def get_amplitude(self):
        """Get current amplitude in Volts"""
        return self.query(":VOLT?")

    # Alias for VOLT
    def set_voltage(self, voltage: float):
        self.set_amplitude(voltage)

    def get_voltage(self):
        return self.get_amplitude()

    # -----------------------------
    # DC OFFSET
    # -----------------------------
    def set_dc_offset(self, offset: float):
        """Set DC offset in Volts"""
        self.write(f":VOLT:OFFS {offset}")

    def get_dc_offset(self):
        """Get current DC offset in Volts"""
        return self.query(":VOLT:OFFS?")

    # Alias
    def set_offset(self, offset: float):
        self.set_dc_offset(offset)

    def get_offset(self):
        return self.get_dc_offset()

    # -----------------------------
    # WAVEFORM TYPE
    # -----------------------------
    def set_waveform(self, waveform: str):
        """Set waveform type: SIN, SQU, TRI, RAMP, etc."""
        self.write(f":FUNC {waveform}")

    def get_waveform(self):
        """Get current waveform type"""
        return self.query(":FUNC?")

    # Convenience methods for common waveforms
    def set_sine(self):
        self.set_waveform("SIN")

    def set_square(self):
        self.set_waveform("SQU")

    def set_triangle(self):
        self.set_waveform("TRI")

    def set_ramp(self):
        self.set_waveform("RAMP")

    # -----------------------------
    # PHASE
    # -----------------------------
    def set_phase(self, phase: float):
        """Set phase in degrees"""
        self.write(f":PHAS {phase}")

    def get_phase(self):
        """Get current phase in degrees"""
        return self.query(":PHAS?")

    # -----------------------------
    # DUTY CYCLE (for square waves)
    # -----------------------------
    def set_duty_cycle(self, duty: float):
        """Set duty cycle as percentage (0-100)"""
        self.write(f":FUNC:SQU:DCYC {duty}")

    def get_duty_cycle(self):
        """Get current duty cycle percentage"""
        return self.query(":FUNC:SQU:DCYC?")

    # -----------------------------
    # BURST MODE
    # -----------------------------
    def set_burst_mode(self, mode: str):
        """Set burst mode: TRIGgered or MANUAL"""
        self.write(f":BURS:MODE {mode}")

    def get_burst_mode(self):
        return self.query(":BURS:MODE?")

    def enable_burst(self):
        self.write(":BURS ON")

    def disable_burst(self):
        self.write(":BURS OFF")

    # Set number of cycles in burst
    def set_burst_cycles(self, cycles: int):
        self.write(f":BURS:NCYC {cycles}")

    def get_burst_cycles(self):
        return self.query(":BURS:NCYC?")

    # Trigger burst
    def trigger_burst(self):
        self.write("*TRG")

    # Alias
    def trigger(self):
        self.trigger_burst()
