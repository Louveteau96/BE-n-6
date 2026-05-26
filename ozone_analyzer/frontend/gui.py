"""Tkinter GUI: notebook of live plots, driven by Tk's own event loop.

Design choice
-------------
We do NOT spawn a separate consumer thread. Instead, the GUI polls the
queue via ``root.after()`` every POLL_INTERVAL_MS milliseconds. This keeps
all dataframe and matplotlib operations on the main thread, eliminating
the thread-safety hazards of writing to ``self.df`` from a worker while
the main thread is reading from it.
"""

import tkinter as tk
from tkinter import ttk
from queue import Queue, Empty

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

from .plots import create_single_plot, create_dual_plot
from backend.data_processor import process_raw_data
from config import PLOT_CONFIGS


class GraphApp:
    POLL_INTERVAL_MS = 200

    def __init__(self, root: tk.Tk, data_queue: Queue, max_points: int = 500):
        self.root = root
        self.data_queue = data_queue
        self.max_points = max_points
        self.df = pd.DataFrame()

        self.root.title("Analyseur Ozone - Temps Réel")
        self.root.geometry("1250x820")

        self.figures: dict[str, tuple] = {}
        self.canvases: dict[str, FigureCanvasTkAgg] = {}

        self.create_interface()
        self.schedule_poll()

    # ---- UI construction ------------------------------------------------
    def create_interface(self) -> None:
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        for name, config in PLOT_CONFIGS.items():
            frame = ttk.Frame(self.notebook)
            self.notebook.add(frame, text=name)

            fig, ax = plt.subplots(figsize=(10, 6))
            canvas = FigureCanvasTkAgg(fig, master=frame)
            canvas.get_tk_widget().pack(fill="both", expand=True)

            self.figures[name] = (fig, ax)
            self.canvases[name] = canvas

            NavigationToolbar2Tk(canvas, frame).update()

            if config.get("dual"):
                create_dual_plot(ax, self.df, config)
            else:
                create_single_plot(ax, self.df, config)
            canvas.draw()

        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(fill="x", padx=10, pady=8)
        ttk.Button(btn_frame, text="🔄 Rafraîchir",
                   command=self.refresh_all).pack(side="right")

    # ---- Queue polling on the Tk event loop -----------------------------
    def schedule_poll(self) -> None:
        self.root.after(self.POLL_INTERVAL_MS, self._poll_queue)

    def _poll_queue(self) -> None:
        new_rows = []
        try:
            while True:
                raw = self.data_queue.get_nowait()
                processed = process_raw_data(raw)
                if processed is not None:
                    new_rows.append(processed)
        except Empty:
            pass

        if new_rows:
            self.df = pd.concat(
                [self.df, pd.DataFrame(new_rows)], ignore_index=True
            )
            if len(self.df) > self.max_points:
                self.df = self.df.iloc[-self.max_points:].reset_index(drop=True)
            self.refresh_all()

        self.schedule_poll()

    # ---- Drawing --------------------------------------------------------
    def refresh_all(self) -> None:
        for name, config in PLOT_CONFIGS.items():
            fig, ax = self.figures[name]
            canvas = self.canvases[name]
            if config.get("dual"):
                create_dual_plot(ax, self.df, config)
            else:
                create_single_plot(ax, self.df, config)
            canvas.draw_idle()
