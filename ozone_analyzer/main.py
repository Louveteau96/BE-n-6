"""Entry point for the Ozone Analyzer GUI.

Usage:
    python main.py                # shows login screen, then real serial acquisition
    python main.py --simulate     # mock backend, skips login screen
"""

import sys
import signal
import tkinter as tk
from queue import Queue

from backend.serial_handler import SerialHandler
from backend.mock_serial_handler import MockSerialHandler
from frontend.gui import GraphApp
from frontend.login import LoginScreen
from config import AppConfig


def main() -> None:
    simulate = "--simulate" in sys.argv

    root = tk.Tk()
    app: GraphApp | None = None   # reference so on_close can call app.close()
    _closing = False              # guard against double-close

    if simulate:
        config = AppConfig()
        data_queue: Queue = Queue(maxsize=config.QUEUE_MAXSIZE)
        backend = MockSerialHandler(data_queue)
        interval = 1
        root.title("Analyseur Ozone - Temps Réel  [SIMULATION]")
        app = GraphApp(root, data_queue, backend, config, interval,
                       max_points=config.MAX_DATA_POINTS)

    else:
        data_queue: Queue = Queue(maxsize=200)
        backend = SerialHandler(data_queue)

        def on_login_success(port, baudrate, id_analyseur, interval,
                             csv_path=None) -> None:
            nonlocal app
            if csv_path is not None:
                app = GraphApp(root, data_queue=None, backend=None,
                               config=None, interval=None,
                               csv_path=csv_path)
            else:
                config = AppConfig()
                config.PORT         = port
                config.BAUDRATE     = baudrate
                config.ID_ANALYSEUR = id_analyseur
                app = GraphApp(root, data_queue, backend, config, interval,
                               max_points=config.MAX_DATA_POINTS)

        LoginScreen(root, on_success=on_login_success)

    def on_close() -> None:
        nonlocal _closing
        if _closing:          # already shutting down — ignore second call
            return
        _closing = True
        if app is not None:
            app.close()       # cancel pending root.after() poll job
        backend.stop()
        root.destroy()

    # Ctrl+C in terminal → same clean shutdown as clicking X
    signal.signal(signal.SIGINT, lambda sig, frame: on_close())

    root.protocol("WM_DELETE_WINDOW", on_close)

    try:
        root.mainloop()
    except KeyboardInterrupt:
        on_close()
    finally:
        backend.stop()


if __name__ == "__main__":
    main()