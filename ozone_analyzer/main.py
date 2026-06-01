"""Entry point for the Ozone Analyzer GUI.

Usage:
    python main.py                # real serial acquisition (needs hardware)
    python main.py --simulate     # mock backend, no hardware required
"""

import sys
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

    root = tk.Tk()

    if simulate:
        backend = MockSerialHandler(data_queue)
        interval = 1
        root.title("Analyseur Ozone - Temps Réel  [SIMULATION]")
    else:
        backend = SerialHandler(data_queue)
        interval = config.ACQUISITION_INTERVAL

    # Pass backend + config so the GUI button can start it
    app = GraphApp(root, data_queue, backend, config, interval,
                   max_points=config.MAX_DATA_POINTS)

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