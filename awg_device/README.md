# AWG Device - MP750513 Driver

Arbitrary Waveform Generator control library using SCPI protocol over TCP.

## Device Info

- **Model**: MP750513 Arbitrary Waveform Generator
- **Interface**: Ethernet (TCP Socket)
- **Default Port**: 5025
- **Protocol**: SCPI (Standard Commands for Programmable Instruments)
- **IP Address**: 192.168.1.97

## Installation

The MP750513 driver is part of the `awg_device` package:

```python
from awg_device import MP750513
```

## Quick Start

```python
from awg_device import MP750513

# Connect to AWG
awg = MP750513("192.168.1.97")

# Set sine wave at 1 kHz
awg.set_waveform("SIN")
awg.set_frequency(1000)
awg.set_amplitude(5.0)

# Enable output
awg.output_on()

# Read back parameters
print(awg.get_frequency())
print(awg.get_amplitude())

# Disable output
awg.output_off()
```

## API Reference

### Initialization

```python
awg = MP750513(ip, port=5025, timeout=2)
```

**Parameters:**
- `ip` (str): Device IP address
- `port` (int): TCP port (default: 5025)
- `timeout` (float): Socket timeout in seconds

### Output Control

```python
awg.output_on()           # Enable output
awg.output_off()          # Disable output
awg.get_output_state()    # Get output state
awg.enable()              # Alias for output_on()
awg.disable()             # Alias for output_off()
```

### Frequency

```python
awg.set_frequency(freq)   # Set frequency in Hz
awg.get_frequency()       # Get frequency in Hz
```

**Example:**
```python
awg.set_frequency(5000)   # 5 kHz
```

### Amplitude

```python
awg.set_amplitude(amp)    # Set amplitude in Volts
awg.get_amplitude()       # Get amplitude in Volts
awg.set_voltage(volt)     # Alias
awg.get_voltage()         # Alias
```

**Example:**
```python
awg.set_amplitude(3.3)    # 3.3V amplitude
```

### DC Offset

```python
awg.set_dc_offset(offset) # Set offset in Volts
awg.get_dc_offset()       # Get offset in Volts
awg.set_offset(offset)    # Alias
awg.get_offset()          # Alias
```

**Example:**
```python
awg.set_dc_offset(1.5)    # 1.5V offset
```

### Waveform Type

```python
awg.set_waveform(waveform)  # Set waveform: SIN, SQU, TRI, RAMP
awg.get_waveform()          # Get current waveform type

# Convenience methods:
awg.set_sine()              # Set to sine wave
awg.set_square()            # Set to square wave
awg.set_triangle()          # Set to triangle wave
awg.set_ramp()              # Set to ramp wave
```

**Example:**
```python
awg.set_sine()              # sine wave
awg.set_frequency(1000)
awg.set_amplitude(5.0)
```

### Phase

```python
awg.set_phase(phase)    # Set phase in degrees
awg.get_phase()         # Get phase in degrees
```

**Example:**
```python
awg.set_phase(45)       # 45 degree phase shift
```

### Duty Cycle (for square waves)

```python
awg.set_duty_cycle(duty)  # Set duty cycle (0-100%)
awg.get_duty_cycle()      # Get duty cycle
```

**Example:**
```python
awg.set_square()
awg.set_duty_cycle(75)    # 75% duty cycle
```

### Burst Mode

```python
awg.enable_burst()            # Enable burst mode
awg.disable_burst()           # Disable burst mode
awg.set_burst_mode(mode)      # Set burst mode: TRIGgered or MANUAL
awg.get_burst_mode()          # Get burst mode
awg.set_burst_cycles(cycles)  # Set number of cycles per burst
awg.get_burst_cycles()        # Get burst cycle count
awg.trigger_burst()           # Trigger a burst
awg.trigger()                 # Alias for trigger_burst()
```

**Example:**
```python
awg.enable_burst()
awg.set_burst_mode("TRIGgered")
awg.set_burst_cycles(10)      # 10 cycles per burst
awg.trigger()                 # Fire one burst
```

### Device Info

```python
awg.get_id()              # Get device identification (*IDN?)
awg.is_connected()        # Check if device is reachable
```

## Flask Server

A Flask app is included to expose the AWG over HTTP on port 3000.

**Launch:**
```bash
python -m flask --app awg_device.flask_app run --port 3000
```

**API Endpoints:**

- `GET /` - Index page
- `GET /id` - Device identification
- `POST /output` - Enable/disable output
- `GET /get/output` - Get output state
- `POST /set/frequency` - Set frequency
- `GET /get/frequency` - Get frequency
- `POST /set/amplitude` - Set amplitude
- `GET /get/amplitude` - Get amplitude
- `POST /set/offset` - Set DC offset
- `GET /get/offset` - Get DC offset
- `POST /set/waveform` - Set waveform type
- `GET /get/waveform` - Get waveform type
- `POST /set/phase` - Set phase
- `GET /get/phase` - Get phase
- `POST /set/duty-cycle` - Set duty cycle
- `GET /get/duty-cycle` - Get duty cycle
- `POST /burst/enable` - Enable burst mode
- `POST /burst/disable` - Disable burst mode
- `POST /burst/set-cycles` - Set burst cycle count
- `POST /burst/trigger` - Trigger a burst
- `GET /measure` - Get all current parameters

**Example REST calls:**

```bash
# Enable output
curl -X POST http://192.168.1.97:3000/output \
  -H "Content-Type: application/json" \
  -d '{"state": true}'

# Set 1kHz sine wave at 5V
curl -X POST http://192.168.1.97:3000/set/frequency \
  -H "Content-Type: application/json" \
  -d '{"frequency": 1000}'

curl -X POST http://192.168.1.97:3000/set/waveform \
  -H "Content-Type: application/json" \
  -d '{"waveform": "SIN"}'

curl -X POST http://192.168.1.97:3000/set/amplitude \
  -H "Content-Type: application/json" \
  -d '{"amplitude": 5.0}'
```

## Notes

- The driver is designed to be blocking and safe (no polling loops)
- Connection issues trigger automatic reconnection
- All socket operations include timeout handling
- DC offset is useful for biasing signals (e.g., for AC coupling)
- Burst mode allows generation of a finite number of waveform cycles triggered by command or external signal
