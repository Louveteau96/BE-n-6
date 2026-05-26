"""Mock serial handler for testing without hardware.

Generates realistic 'lrec 1 1 ...' frames at the configured interval so the
GUI, plotting pipeline, and shutdown logic can be exercised end-to-end
without a physical analyzer. Drop-in replacement for SerialHandler — same
public interface (start_acquisition / stop).
"""

import math
import random
import time
from datetime import datetime
from queue import Full, Queue
from threading import Event, Thread


class MockSerialHandler:
    def __init__(self, data_queue: Queue):
        self.data_queue = data_queue
        self.stop_event = Event()
        self.thread: Thread | None = None
        self._t0: float = 0.0

    # Same signature as SerialHandler.start_acquisition so main.py can swap them.
    def start_acquisition(
        self, port: str, baudrate: int, id_analyseur: int, interval: int
    ) -> bool:
        print(f"🧪 MockSerialHandler running (port={port!r} ignored)")
        self.stop_event.clear()
        self._t0 = time.time()
        self.thread = Thread(target=self._loop, args=(interval,), daemon=True)
        self.thread.start()
        return True

    def _generate_frame(self) -> str:
    #Build a frame matching the layout parsed by data_processor.process_raw_data.

    #Frame layout (15 tokens):
    #  "lrec" "1" "1" <heure> <date> <flag> <o3>
    #  <cellA> <cellB> <benchT> <lampT> <o3lamp> <flowA> <flowB> <pression>
    
        elapsed = time.time() - self._t0

        o3     = 40 + 15 * math.sin(elapsed / 60.0) + random.gauss(0, 1.5)
        cellA  = max(0.0, o3 * 0.98 + random.gauss(0, 0.5))   # closely tracks o3
        cellB  = max(0.0, o3 * 0.97 + random.gauss(0, 0.5))   # slightly offset
        benchT = 25 + random.gauss(0, 0.2)                     # bench temperature °C
        pression = 1013 + random.gauss(0, 0.4)
        o3lamp   = 7.5  + random.gauss(0, 0.08)
        lampT    = 50   + random.gauss(0, 0.3)
        flowA    = 800  + random.gauss(0, 5)
        flowB    = 800  + random.gauss(0, 5)

        now   = datetime.now()
        heure = now.strftime("%H:%M:%S")
        date  = now.strftime("%d/%m/%y")

        tokens = [
            "lrec", "1", "1",
            heure, date,
            "0",                        # flag
                
            f"{o3:.2f}",                # o3        → valeurs[3]
            "0.000",                     # hio3
            f"{cellA:.2f}",             # cellA     → valeurs[4]
            f"{cellB:.2f}",             # cellB     → valeurs[5]
            f"{benchT:.2f}",            # benchT    → valeurs[6]
            f"{lampT:.2f}",             # lampT     → valeurs[7]
            f"{o3lamp:.2f}",            # o3lamp    → valeurs[8]
            f"{flowA:.1f}",             # flowA     → valeurs[9]
            f"{flowB:.1f}",             # flowB     → valeurs[10]
            f"{pression:.2f}",          # pression  → valeurs[11]
        ]
        return " ".join(tokens)

    def _enqueue(self, raw: str) -> None:
        """Drop-oldest policy, mirroring SerialHandler."""
        try:
            self.data_queue.put_nowait(raw)
        except Full:
            try:
                self.data_queue.get_nowait()
            except Exception:
                pass
            try:
                self.data_queue.put_nowait(raw)
            except Full:
                pass

    def _loop(self, interval: int) -> None:
        while not self.stop_event.is_set():
            self._enqueue(self._generate_frame())
            if self.stop_event.wait(timeout=interval):
                break

    def stop(self) -> None:
        self.stop_event.set()
        if self.thread is not None:
            self.thread.join(timeout=2)
            self.thread = None
