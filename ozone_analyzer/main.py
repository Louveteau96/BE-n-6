"""Entry point for the Ozone Analyzer GUI.

Usage:
    python main.py                # real serial acquisition (needs hardware)
    python main.py --simulate     # mock backend, no hardware required
"""

import sys # read command line arguments 
import tkinter as tk
from queue import Queue

from backend.serial_handler import SerialHandler
from backend.mock_serial_handler import MockSerialHandler
from frontend.gui import GraphApp
from config import AppConfig


def main() -> None:
    simulate = "--simulate" in sys.argv

    config = AppConfig()
    data_queue: Queue = Queue(maxsize=config.QUEUE_MAXSIZE)

    # GUI is built first so it's ready to receive the first sample.
    root = tk.Tk()
    app = GraphApp(root, data_queue, max_points=config.MAX_DATA_POINTS)

    if simulate:
        backend = MockSerialHandler(data_queue)
        interval = 1                      # tighter cadence so the demo feels live
        root.title(root.title() + "  [SIMULATION]")
    else:
        backend = SerialHandler(data_queue)
        interval = config.ACQUISITION_INTERVAL

    started = backend.start_acquisition(
        config.PORT,
        config.BAUDRATE,
        config.ID_ANALYSEUR,
        interval,
    )
    if not started:
        print("⚠️  Acquisition could not start — check serial port / device.")

    def on_close() -> None:
        backend.stop()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)

    try:
        root.mainloop()
    finally:
        backend.stop()


if __name__ == "__main__":
    main()
