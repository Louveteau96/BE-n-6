"""Tkinter GUI: notebook of live plots, driven by Tk's own event loop.

Design choice
-------------
We do NOT spawn a separate consumer thread. Instead, the GUI polls the
queue via ``root.after()`` every POLL_INTERVAL_MS milliseconds. This keeps
all dataframe and matplotlib operations on the main thread, eliminating
the thread-safety hazards of writing to ``self.df`` from a worker while
the main thread is reading from it.
"""

import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from queue import Queue, Empty
from datetime import datetime

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

from .plots import create_single_plot, create_dual_plot
from .components import Tooltip
from backend.data_processor import process_raw_data
from config import PLOT_CONFIGS

RECORD_DIR = "record"


class GraphApp:
    POLL_INTERVAL_MS = 200

    def __init__(self, root: tk.Tk, data_queue: Queue, max_points: int = 500):
        self.root = root
        self.data_queue = data_queue
        self.max_points = max_points
        self.df = pd.DataFrame()

        # Auto-save state
        self._autosave_path: str | None = None   # set on first data received

        self.root.title("Analyseur Ozone - Temps Réel")
        self.root.geometry("1250x820")

        self.figures: dict[str, tuple] = {}
        self.canvases: dict[str, FigureCanvasTkAgg] = {}

        # Ensure the record folder exists
        os.makedirs(RECORD_DIR, exist_ok=True)

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

        # ---- Bottom button bar ------------------------------------------
        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(fill="x", padx=10, pady=8)

        # Status label — shows the autosave path once active
        self._status_var = tk.StringVar(value="En attente de données...")
        ttk.Label(btn_frame, textvariable=self._status_var,
                  foreground="gray").pack(side="left")

        # Refresh button
        btn_refresh = ttk.Button(
            btn_frame, text="🔄 Rafraîchir", command=self.refresh_all
        )
        btn_refresh.pack(side="right", padx=(6, 0))
        Tooltip(btn_refresh, "Redessiner tous les graphiques manuellement")

        # Manual save button
        btn_save = ttk.Button(
            btn_frame, text="💾 Sauvegarder CSV", command=self.save_csv
        )
        btn_save.pack(side="right", padx=(6, 0))
        Tooltip(btn_save, "Sauvegarder les données dans un fichier CSV personnalisé")

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

            self._autosave()
            self.refresh_all()

        self.schedule_poll()

    # ---- Auto-save ------------------------------------------------------
    def _autosave(self) -> None:
        """Save to record/<start_datetime>.csv every time new data arrives.
        The filename is fixed at the moment the first data point is received.
        """
        # First data point — create the filename now
        if self._autosave_path is None:
            filename = datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".csv"
            self._autosave_path = os.path.join(RECORD_DIR, filename)
            self._status_var.set(f"Enregistrement : {self._autosave_path}")

        try:
            self.df.to_csv(self._autosave_path, index=False)
        except Exception as e:
            print(f"Autosave error: {e}")

    # ---- Manual save button ---------------------------------------------
    def save_csv(self) -> None:
        """Open a file dialog and save the current DataFrame to a chosen path."""
        if self.df.empty:
            messagebox.showwarning(
                "Aucune donnée",
                "Pas de données à sauvegarder.\nLancez l'acquisition d'abord.",
            )
            return

        default_name = datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".csv"
        path = filedialog.asksaveasfilename(
            title="Sauvegarder les données",
            defaultextension=".csv",
            initialdir=RECORD_DIR,
            initialfile=default_name,
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        )

        if not path:      # user cancelled
            return

        try:
            self.df.to_csv(path, index=False)
            messagebox.showinfo(
                "Sauvegarde réussie",
                f"{len(self.df)} lignes enregistrées.\n{path}",
            )
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d'écrire le fichier :\n{e}")

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
