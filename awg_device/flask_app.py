from flask import Flask, request, jsonify, send_from_directory
from .mp750513 import MP750513

app = Flask(__name__, static_folder="static")

awg = MP750513("192.168.1.97")


@app.route("/")
def index():
    return send_from_directory("static", "index.html")


@app.route("/id")
def get_id():
    return jsonify({"id": awg.get_id()})


@app.route("/output", methods=["POST"])
def output_control():
    d = request.json

    if d["state"]:
        awg.output_on()
    else:
        awg.output_off()

    return jsonify({"ok": True})


@app.route("/get/output")
def get_output():
    return jsonify({"state": awg.get_output_state()})


@app.route("/set/frequency", methods=["POST"])
def set_frequency():
    d = request.json
    awg.set_frequency(float(d["frequency"]))
    return jsonify({"ok": True})


@app.route("/get/frequency")
def get_frequency():
    return jsonify({"frequency": awg.get_frequency()})


@app.route("/set/amplitude", methods=["POST"])
def set_amplitude():
    d = request.json
    awg.set_amplitude(float(d["amplitude"]))
    return jsonify({"ok": True})


@app.route("/get/amplitude")
def get_amplitude():
    return jsonify({"amplitude": awg.get_amplitude()})


@app.route("/set/offset", methods=["POST"])
def set_offset():
    d = request.json
    awg.set_dc_offset(float(d["offset"]))
    return jsonify({"ok": True})


@app.route("/get/offset")
def get_offset():
    return jsonify({"offset": awg.get_dc_offset()})


@app.route("/set/waveform", methods=["POST"])
def set_waveform():
    d = request.json
    awg.set_waveform(d["waveform"])
    return jsonify({"ok": True})


@app.route("/get/waveform")
def get_waveform():
    return jsonify({"waveform": awg.get_waveform()})


@app.route("/set/phase", methods=["POST"])
def set_phase():
    d = request.json
    awg.set_phase(float(d["phase"]))
    return jsonify({"ok": True})


@app.route("/get/phase")
def get_phase():
    return jsonify({"phase": awg.get_phase()})


@app.route("/set/duty-cycle", methods=["POST"])
def set_duty_cycle():
    d = request.json
    awg.set_duty_cycle(float(d["duty"]))
    return jsonify({"ok": True})


@app.route("/get/duty-cycle")
def get_duty_cycle():
    return jsonify({"duty": awg.get_duty_cycle()})


@app.route("/burst/enable", methods=["POST"])
def burst_enable():
    awg.enable_burst()
    return jsonify({"ok": True})


@app.route("/burst/disable", methods=["POST"])
def burst_disable():
    awg.disable_burst()
    return jsonify({"ok": True})


@app.route("/burst/set-cycles", methods=["POST"])
def burst_set_cycles():
    d = request.json
    awg.set_burst_cycles(int(d["cycles"]))
    return jsonify({"ok": True})


@app.route("/burst/trigger", methods=["POST"])
def burst_trigger():
    awg.trigger_burst()
    return jsonify({"ok": True})


@app.route("/measure")
def measure():
    """Get current state of all parameters"""
    return jsonify({
        "output": awg.get_output_state(),
        "frequency": awg.get_frequency(),
        "amplitude": awg.get_amplitude(),
        "offset": awg.get_dc_offset(),
        "waveform": awg.get_waveform(),
        "phase": awg.get_phase(),
    })


if __name__ == "__main__":
    app.run(port=3000, debug=True)
