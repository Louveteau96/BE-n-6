"""Virtual Thermo 49i-PS for com0com testing.

Open one end of your com0com pair here (COM11) while the app opens the other
end (COM10) via the normal SerialHandler. This emulator answers commands the
way the real analyzer does, so you exercise the REAL serial path end-to-end
(address byte, frame matching, terminators) — unlike `--simulate`, which
bypasses serial entirely.

Run (separate terminal, BEFORE or after launching the app):
    python device_emulator.py            # defaults to COM11 @ 9600
    python device_emulator.py COM11 9600
"""

import sys
import time
import math
import random
from datetime import datetime

import serial

PORT = sys.argv[1] if len(sys.argv) > 1 else "COM2"
BAUD = int(sys.argv[2]) if len(sys.argv) > 2 else 9600


def make_frame(t0: float) -> str:
    """One record line in the real device's format/ranges (calibrated to the
    captured sample). Starts with the time, plain decimals, includes hio3."""
    elapsed = time.time() - t0
    o3       = max(0.0, 7.5 + 2.0 * math.sin(elapsed / 120.0) + random.gauss(0, 0.3))
    hio3     = max(0.0, random.gauss(0.0, 0.002))
    cellA    = 115700 + random.gauss(0, 300)
    cellB    = 117900 + random.gauss(0, 300)
    benchT   = 31.6 + random.gauss(0, 0.15)
    lampT    = 52.8 + random.gauss(0, 0.20)
    o3lamp   = 67.3 + random.gauss(0, 0.20)
    flowA    = 0.751 + random.gauss(0, 0.005)
    flowB    = 0.717 + random.gauss(0, 0.005)
    pres     = 751.8 + random.gauss(0, 0.30)
    now = datetime.now()
    return (f"{now:%H:%M} {now:%m-%d-%y} flags 0C100000 "
            f"o3 {o3:.3f} hio3 {hio3:.3f} "
            f"cellai {cellA:.0f} cellbi {cellB:.0f} "
            f"bncht {benchT:.1f} lmpt {lampT:.1f} o3lt {o3lamp:.1f} "
            f"flowa {flowA:.3f} flowb {flowB:.3f} pres {pres:.1f}")


def main() -> None:
    ser = serial.Serial(PORT, BAUD, timeout=1)
    print(f"🧪 Emulated 49i-PS on {PORT} @ {BAUD}. Waiting for commands... (Ctrl-C to stop)")
    t0 = time.time()
    try:
        while True:
            # Commands are CR-terminated; read until '\r'.
            raw = ser.read_until(b"\r\n")
            if not raw:
                continue
            # decode tolerant of the leading address byte (0xB1 etc.) — it is
            # non-ASCII, so errors="ignore" drops it, leaving the command text.
            cmd = raw.decode("ascii", errors="ignore").strip()
            if not cmd:
                continue
            print(f"  <- received: {cmd!r}")

            if "set mode remote" in cmd:
                reply = "set mode remote ok\r\n"
            elif "lrec" in cmd:
                reply = make_frame(t0) + "\r\n"     # app's readline() needs the \n
            else:
                # echo unknown commands back as "<cmd> ok", like the instrument
                reply = f"{cmd} ok\r\n"

            ser.write(reply.encode("ascii"))
            ser.flush()
            print(f"  -> sent:     {reply.strip()!r}")
    except KeyboardInterrupt:
        print("\nStopping emulator.")
    finally:
        ser.close()


if __name__ == "__main__":
    main()
