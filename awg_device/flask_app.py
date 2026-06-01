"""
Flask HTTP wrapper for the MP750513 two-channel AWG driver.

Launch::

    python -m flask --app awg_device.flask_app run --port 3000

All channel-specific endpoints carry a ``/ch<n>/`` segment (n = 1 or 2).
Channel-agnostic endpoints (device info, phase align) live at the root.

Quick reference
---------------
GET  /                          Serve index page
GET  /id                        *IDN? string
GET  /status                    Connection status + both-channel snapshot

Per-channel  (replace <ch> with 1 or 2)
POST /ch<ch>/output             {"state": true|false}
GET  /ch<ch>/output             {"state": true|false}
POST /ch<ch>/set/frequency      {"frequency": <Hz>}
GET  /ch<ch>/get/frequency      {"frequency": <Hz>}
POST /ch<ch>/set/amplitude      {"amplitude": <V>}
GET  /ch<ch>/get/amplitude      {"amplitude": <V>}
POST /ch<ch>/set/offset         {"offset": <V>}
GET  /ch<ch>/get/offset         {"offset": <V>}
POST /ch<ch>/set/waveform       {"waveform": "SIN"|"SQU"|"TRI"|"RAMP"}
GET  /ch<ch>/get/waveform       {"waveform": <str>}
POST /ch<ch>/set/phase          {"phase": <deg>}
GET  /ch<ch>/get/phase          {"phase": <deg>}
POST /ch<ch>/set/duty-cycle     {"duty_cycle": <pct>}
GET  /ch<ch>/get/duty-cycle     {"duty_cycle": <pct>}
POST /ch<ch>/burst/enable
POST /ch<ch>/burst/disable
POST /ch<ch>/burst/set-cycles   {"cycles": <int>}
GET  /ch<ch>/burst/get-cycles   {"cycles": <int>}
POST /ch<ch>/burst/set-mode     {"mode": "TRIGgered"|"MANUAL"}
GET  /ch<ch>/burst/get-mode     {"mode": <str>}
POST /ch<ch>/burst/trigger
GET  /ch<ch>/measure            Full per-channel snapshot

Device-level
POST /output/all                {"state": true|false}  — both channels at once
POST /phase/align               Reset phase accumulators (sync both channels)
"""

from flask import Flask, jsonify, request, render_template_string
from .mp750513 import MP750513, AWGError

app = Flask(__name__)

awg = MP750513("192.168.1.97")

# ------------------------------------------------------------------ #
# Helpers                                                             #
# ------------------------------------------------------------------ #

_INDEX_HTML = """
<!DOCTYPE html>
<html>
<head><title>MP750513 AWG Control</title></head>
<body>
  <h1>MP750513 Two-Channel AWG</h1>
  <p>REST API is running. See the
  <a href="https://github.com/mayermakes/MP750513_python">README</a>
  for endpoint documentation.</p>
</body>
</html>
"""


def _ok(**kwargs):
    return jsonify({"status": "ok", **kwargs})


def _err(msg: str, code: int = 500):
    return jsonify({"status": "error", "message": msg}), code


def _ch(channel_str: str):
    """Parse and validate a channel string from the URL."""
    try:
        ch = int(channel_str)
    except (TypeError, ValueError):
        raise ValueError(f"Invalid channel: {channel_str!r}")
    if ch not in (1, 2):
        raise ValueError(f"Channel must be 1 or 2, got {ch}")
    return ch


# ------------------------------------------------------------------ #
# Device-level endpoints                                              #
# ------------------------------------------------------------------ #

@app.get("/")
def index():
    return render_template_string(_INDEX_HTML)


@app.get("/id")
def get_id():
    try:
        return _ok(id=awg.get_id())
    except AWGError as exc:
        return _err(str(exc))


@app.get("/status")
def status():
    try:
        connected = awg.is_connected()
        state = awg.get_all_state() if connected else None
        return _ok(connected=connected, state=state)
    except AWGError as exc:
        return _err(str(exc))


@app.post("/output/all")
def output_all():
    data = request.get_json(force=True) or {}
    state = data.get("state")
    if state is None:
        return _err("Missing 'state' field", 400)
    try:
        if state:
            awg.all_outputs_on()
        else:
            awg.all_outputs_off()
        return _ok(state=bool(state))
    except AWGError as exc:
        return _err(str(exc))


@app.post("/phase/align")
def phase_align():
    try:
        awg.align_phases()
        return _ok()
    except AWGError as exc:
        return _err(str(exc))


# ------------------------------------------------------------------ #
# Per-channel endpoints                                               #
# ------------------------------------------------------------------ #

# Output ---------------------------------------------------------------

@app.post("/ch<channel>/output")
def set_output(channel):
    try:
        ch = _ch(channel)
    except ValueError as exc:
        return _err(str(exc), 400)
    data = request.get_json(force=True) or {}
    state = data.get("state")
    if state is None:
        return _err("Missing 'state' field", 400)
    try:
        if state:
            awg.output_on(ch)
        else:
            awg.output_off(ch)
        return _ok(channel=ch, state=bool(state))
    except AWGError as exc:
        return _err(str(exc))


@app.get("/ch<channel>/output")
def get_output(channel):
    try:
        ch = _ch(channel)
        return _ok(channel=ch, state=awg.get_output_state(ch))
    except (ValueError, AWGError) as exc:
        return _err(str(exc), 400 if isinstance(exc, ValueError) else 500)


# Frequency ------------------------------------------------------------

@app.post("/ch<channel>/set/frequency")
def set_frequency(channel):
    try:
        ch = _ch(channel)
    except ValueError as exc:
        return _err(str(exc), 400)
    data = request.get_json(force=True) or {}
    freq = data.get("frequency")
    if freq is None:
        return _err("Missing 'frequency' field", 400)
    try:
        awg.set_frequency(float(freq), ch)
        return _ok(channel=ch, frequency=float(freq))
    except AWGError as exc:
        return _err(str(exc))


@app.get("/ch<channel>/get/frequency")
def get_frequency(channel):
    try:
        ch = _ch(channel)
        return _ok(channel=ch, frequency=awg.get_frequency(ch))
    except (ValueError, AWGError) as exc:
        return _err(str(exc), 400 if isinstance(exc, ValueError) else 500)


# Amplitude ------------------------------------------------------------

@app.post("/ch<channel>/set/amplitude")
def set_amplitude(channel):
    try:
        ch = _ch(channel)
    except ValueError as exc:
        return _err(str(exc), 400)
    data = request.get_json(force=True) or {}
    amp = data.get("amplitude")
    if amp is None:
        return _err("Missing 'amplitude' field", 400)
    try:
        awg.set_amplitude(float(amp), ch)
        return _ok(channel=ch, amplitude=float(amp))
    except AWGError as exc:
        return _err(str(exc))


@app.get("/ch<channel>/get/amplitude")
def get_amplitude(channel):
    try:
        ch = _ch(channel)
        return _ok(channel=ch, amplitude=awg.get_amplitude(ch))
    except (ValueError, AWGError) as exc:
        return _err(str(exc), 400 if isinstance(exc, ValueError) else 500)


# DC offset ------------------------------------------------------------

@app.post("/ch<channel>/set/offset")
def set_offset(channel):
    try:
        ch = _ch(channel)
    except ValueError as exc:
        return _err(str(exc), 400)
    data = request.get_json(force=True) or {}
    offset = data.get("offset")
    if offset is None:
        return _err("Missing 'offset' field", 400)
    try:
        awg.set_dc_offset(float(offset), ch)
        return _ok(channel=ch, offset=float(offset))
    except AWGError as exc:
        return _err(str(exc))


@app.get("/ch<channel>/get/offset")
def get_offset(channel):
    try:
        ch = _ch(channel)
        return _ok(channel=ch, offset=awg.get_dc_offset(ch))
    except (ValueError, AWGError) as exc:
        return _err(str(exc), 400 if isinstance(exc, ValueError) else 500)


# Waveform -------------------------------------------------------------

@app.post("/ch<channel>/set/waveform")
def set_waveform(channel):
    try:
        ch = _ch(channel)
    except ValueError as exc:
        return _err(str(exc), 400)
    data = request.get_json(force=True) or {}
    wf = data.get("waveform")
    if wf is None:
        return _err("Missing 'waveform' field", 400)
    try:
        awg.set_waveform(str(wf).upper(), ch)
        return _ok(channel=ch, waveform=str(wf).upper())
    except (ValueError, AWGError) as exc:
        return _err(str(exc), 400 if isinstance(exc, ValueError) else 500)


@app.get("/ch<channel>/get/waveform")
def get_waveform(channel):
    try:
        ch = _ch(channel)
        return _ok(channel=ch, waveform=awg.get_waveform(ch))
    except (ValueError, AWGError) as exc:
        return _err(str(exc), 400 if isinstance(exc, ValueError) else 500)


# Phase ----------------------------------------------------------------

@app.post("/ch<channel>/set/phase")
def set_phase(channel):
    try:
        ch = _ch(channel)
    except ValueError as exc:
        return _err(str(exc), 400)
    data = request.get_json(force=True) or {}
    phase = data.get("phase")
    if phase is None:
        return _err("Missing 'phase' field", 400)
    try:
        awg.set_phase(float(phase), ch)
        return _ok(channel=ch, phase=float(phase))
    except AWGError as exc:
        return _err(str(exc))


@app.get("/ch<channel>/get/phase")
def get_phase(channel):
    try:
        ch = _ch(channel)
        return _ok(channel=ch, phase=awg.get_phase(ch))
    except (ValueError, AWGError) as exc:
        return _err(str(exc), 400 if isinstance(exc, ValueError) else 500)


# Duty cycle -----------------------------------------------------------

@app.post("/ch<channel>/set/duty-cycle")
def set_duty_cycle(channel):
    try:
        ch = _ch(channel)
    except ValueError as exc:
        return _err(str(exc), 400)
    data = request.get_json(force=True) or {}
    duty = data.get("duty_cycle")
    if duty is None:
        return _err("Missing 'duty_cycle' field", 400)
    try:
        awg.set_duty_cycle(float(duty), ch)
        return _ok(channel=ch, duty_cycle=float(duty))
    except AWGError as exc:
        return _err(str(exc))


@app.get("/ch<channel>/get/duty-cycle")
def get_duty_cycle(channel):
    try:
        ch = _ch(channel)
        return _ok(channel=ch, duty_cycle=awg.get_duty_cycle(ch))
    except (ValueError, AWGError) as exc:
        return _err(str(exc), 400 if isinstance(exc, ValueError) else 500)


# Burst ----------------------------------------------------------------

@app.post("/ch<channel>/burst/enable")
def burst_enable(channel):
    try:
        ch = _ch(channel)
        awg.enable_burst(ch)
        return _ok(channel=ch, burst=True)
    except (ValueError, AWGError) as exc:
        return _err(str(exc), 400 if isinstance(exc, ValueError) else 500)


@app.post("/ch<channel>/burst/disable")
def burst_disable(channel):
    try:
        ch = _ch(channel)
        awg.disable_burst(ch)
        return _ok(channel=ch, burst=False)
    except (ValueError, AWGError) as exc:
        return _err(str(exc), 400 if isinstance(exc, ValueError) else 500)


@app.post("/ch<channel>/burst/set-cycles")
def burst_set_cycles(channel):
    try:
        ch = _ch(channel)
    except ValueError as exc:
        return _err(str(exc), 400)
    data = request.get_json(force=True) or {}
    cycles = data.get("cycles")
    if cycles is None:
        return _err("Missing 'cycles' field", 400)
    try:
        awg.set_burst_cycles(int(cycles), ch)
        return _ok(channel=ch, cycles=int(cycles))
    except AWGError as exc:
        return _err(str(exc))


@app.get("/ch<channel>/burst/get-cycles")
def burst_get_cycles(channel):
    try:
        ch = _ch(channel)
        return _ok(channel=ch, cycles=awg.get_burst_cycles(ch))
    except (ValueError, AWGError) as exc:
        return _err(str(exc), 400 if isinstance(exc, ValueError) else 500)


@app.post("/ch<channel>/burst/set-mode")
def burst_set_mode(channel):
    try:
        ch = _ch(channel)
    except ValueError as exc:
        return _err(str(exc), 400)
    data = request.get_json(force=True) or {}
    mode = data.get("mode")
    if mode is None:
        return _err("Missing 'mode' field", 400)
    try:
        awg.set_burst_mode(str(mode), ch)
        return _ok(channel=ch, mode=str(mode))
    except AWGError as exc:
        return _err(str(exc))


@app.get("/ch<channel>/burst/get-mode")
def burst_get_mode(channel):
    try:
        ch = _ch(channel)
        return _ok(channel=ch, mode=awg.get_burst_mode(ch))
    except (ValueError, AWGError) as exc:
        return _err(str(exc), 400 if isinstance(exc, ValueError) else 500)


@app.post("/ch<channel>/burst/trigger")
def burst_trigger(channel):
    try:
        ch = _ch(channel)
        awg.trigger_burst(ch)
        return _ok(channel=ch)
    except (ValueError, AWGError) as exc:
        return _err(str(exc), 400 if isinstance(exc, ValueError) else 500)


# Snapshot -------------------------------------------------------------

@app.get("/ch<channel>/measure")
def measure(channel):
    try:
        ch = _ch(channel)
        return _ok(**awg.get_channel_state(ch))
    except (ValueError, AWGError) as exc:
        return _err(str(exc), 400 if isinstance(exc, ValueError) else 500)
