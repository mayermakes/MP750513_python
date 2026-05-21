#!/usr/bin/env python3
"""AWG telnet debug helper for MP750513 at 192.168.1.97:3000."""

import argparse
import asyncio
import sys

import telnetlib3

DEFAULT_HOST = "192.168.1.97"
DEFAULT_PORT = 3000
DEFAULT_TIMEOUT = 5

COMMAND_VARIANTS = {
    "*IDN?": ["*IDN?"],
    "FUNC?": [
        "FUNC?",
        "FUNCTION?",
        ":FUNC?",
        ":FUNCTION?",
        ":SOUR:FUNC?",
        ":SOUR:FUNCTION?",
        ":SOUR1:FUNC?",
        ":SOUR1:FUNCTION?",
        ":SOURce1:FUNC?",
        ":SOURce1:FUNCTION?",
    ],
    "FREQ?": [
        "FREQ?",
        "FREQUENCY?",
        ":FREQ?",
        ":FREQUENCY?",
        ":SOUR:FREQ?",
        ":SOUR:FREQUENCY?",
        ":SOUR1:FREQ?",
        ":SOUR1:FREQUENCY?",
        ":SOURce1:FREQ?",
        ":SOURce1:FREQUENCY?",
    ],
    "VOLT?": [
        "VOLT?",
        "VOLTAGE?",
        ":VOLT?",
        ":VOLTAGE?",
        ":SOUR:VOLT?",
        ":SOUR:VOLTAGE?",
        ":SOUR1:VOLT?",
        ":SOUR1:VOLTAGE?",
        ":SOURce1:VOLT?",
        ":SOURce1:VOLTAGE?",
    ],
    "VOLT:OFFS?": [
        "VOLT:OFFS?",
        "VOLTAGE:OFFS?",
        ":VOLT:OFFS?",
        ":VOLTAGE:OFFS?",
        ":SOUR:VOLT:OFFS?",
        ":SOUR:VOLTAGE:OFFS?",
        ":SOUR1:VOLT:OFFS?",
        ":SOUR1:VOLTAGE:OFFS?",
        ":SOURce1:VOLT:OFFS?",
        ":SOURce1:VOLTAGE:OFFS?",
    ],
    "OUTP?": [
        "OUTP?",
        "OUTPUT?",
        ":OUTP?",
        ":OUTPUT?",
        "OUTP:STAT?",
        "OUTPUT:STAT?",
        ":OUTP:STAT?",
        ":OUTPUT:STAT?",
        "OUTP:STATE?",
        "OUTPUT:STATE?",
    ],
}


async def _read_response(reader, timeout):
    response = None
    try:
        try:
            response = await asyncio.wait_for(reader.readuntil("\n"), timeout=timeout)
        except (TypeError, AttributeError):
            response = await asyncio.wait_for(reader.readuntil(b"\n"), timeout=timeout)
    except asyncio.TimeoutError:
        response = None

    if response is None:
        if hasattr(reader, "read"):
            try:
                response = await asyncio.wait_for(reader.read(1024), timeout=0.25)
            except Exception:
                response = b""

    if response is None:
        return ""

    if isinstance(response, bytes):
        response = response.decode("ascii", errors="ignore")
    return response.strip()


async def send_command(reader, writer, cmd, timeout=DEFAULT_TIMEOUT):
    raw = cmd.strip()
    if not raw:
        return ""

    try:
        writer.write(raw + "\n")
    except TypeError:
        writer.write((raw + "\n").encode("ascii"))
    await writer.drain()

    try:
        response = await _read_response(reader, timeout)
        if response == "":
            return "<timeout>"
        return response
    except EOFError:
        return "<EOF>"
    except Exception as exc:
        return f"<error: {exc}>"


async def probe_device(reader, writer, timeout):
    print("Running probe commands...")
    for label, variants in COMMAND_VARIANTS.items():
        response = "<timeout>"
        used_variant = None
        for variant in variants:
            response = await send_command(reader, writer, variant, timeout)
            if response and response not in {"<timeout>", "<EOF>"}:
                used_variant = variant
                break
        if used_variant:
            print(f"{label} -> {response}  (via {used_variant})")
        else:
            print(f"{label} -> {response}")


async def interactive_loop(reader, writer, timeout):
    print("Enter SCPI commands to send to the AWG. Type 'quit' or 'exit' to leave.")
    while True:
        try:
            cmd = await asyncio.to_thread(input, "> ")
        except EOFError:
            print()
            break
        cmd = cmd.strip()
        if not cmd:
            continue
        if cmd.lower() in {"quit", "exit", "q"}:
            break
        response = await send_command(reader, writer, cmd, timeout)
        print(response)


async def main_async(args):
    try:
        print(f"Connecting to {args.host}:{args.port}...")
        reader, writer = await telnetlib3.open_connection(args.host, args.port)
    except Exception as exc:
        print(f"Failed to connect: {exc}")
        return 1

    try:
        if args.probe:
            await probe_device(reader, writer, args.timeout)

        if args.command:
            for cmd in args.command:
                response = await send_command(reader, writer, cmd, args.timeout)
                print(f"{cmd} -> {response}")

        if not args.no_interactive:
            print()
            await interactive_loop(reader, writer, args.timeout)
    finally:
        try:
            writer.close()
            await writer.wait_closed()
        except Exception:
            pass

    return 0


def main():
    parser = argparse.ArgumentParser(description="Telnet debug helper for MP750513 AWG")
    parser.add_argument("--host", default=DEFAULT_HOST, help="AWG IP address")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="AWG TCP port")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT, help="Read timeout in seconds")
    parser.add_argument("--command", "-c", action="append", help="Send a single command and print the response")
    parser.add_argument("--probe", action="store_true", help="Send a set of common probe commands")
    parser.add_argument("--no-interactive", action="store_true", help="Do not enter interactive mode after commands")
    args = parser.parse_args()

    sys.exit(asyncio.run(main_async(args)))


if __name__ == "__main__":
    main()
