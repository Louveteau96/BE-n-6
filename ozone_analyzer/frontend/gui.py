"""Tkinter GUI: notebook of live plots, driven by Tk's own event loop.

Design choice
-------------
We do NOT spawn a separate consumer thread. Instead, the GUI polls the
queue via ``root.after()`` every POLL_INTERVAL_MS milliseconds. This keeps
all dataframe and matplotlib operations on the main thread, eliminating
the thread-safety hazards of writing to ``self.df`` from a worker while
the main thread is reading from it.

File mode
---------
Pass csv_path=<path> and leave data_queue/backend/config/interval as None.
GraphApp will load the CSV immediately, display it, and disable acquisition
controls. Queue polling is still scheduled but does nothing (queue is None).
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

    def __init__(self, root: tk.Tk, data_queue: Queue | None,
                 backend, config, interval: int | None,
                 max_points: int = 500,
                 csv_path: str | None = None):
        self.root       = root
        self.data_queue = data_queue
        self.max_points = max_points
        self.df         = pd.DataFrame()

        self._backend   = backend
        self._config    = config
        self._interval  = interval
        self._acquisition_running = False

        self._file_mode       = csv_path is not None
        self._csv_source_path = csv_path

        self._btn_start = None
        self._btn_stop  = None

        self._autosave_path: str | None = None
        self._poll_after_id = None

        if self._file_mode:
            self.root.title(f"Analyseur Ozone — {os.path.basename(csv_path)}  [Lecture seule]")
        else:
            self.root.title("Analyseur Ozone - Temps Réel")

        self.root.state("zoomed")

        self.figures:  dict[str, tuple]               = {}
        self.canvases: dict[str, FigureCanvasTkAgg]   = {}
        self.toolbars: dict[str, NavigationToolbar2Tk] = {}

        os.makedirs(RECORD_DIR, exist_ok=True)

        self.create_interface()

        if self._file_mode:
            self._load_file(csv_path)
        else:
            self.schedule_poll()

    # ---- Clean shutdown -------------------------------------------------
    def close(self) -> None:
        if self._poll_after_id is not None:
            self.root.after_cancel(self._poll_after_id)
            self._poll_after_id = None

    # ---- UI construction ------------------------------------------------
    def create_interface(self) -> None:
        # ---- Shared bottom bar (toolbar left, buttons right) ------------
        bottom_bar = ttk.Frame(self.root)
        bottom_bar.pack(fill="x", side="bottom", padx=10, pady=4)

        # Left side: placeholder that holds the active tab's toolbar
        self._toolbar_frame = ttk.Frame(bottom_bar)
        self._toolbar_frame.pack(side="left")

        # Right side: action buttons
        btn_frame = ttk.Frame(bottom_bar)
        btn_frame.pack(side="right")

        self._status_var = tk.StringVar(
            value="Fichier chargé." if self._file_mode else "En attente de données..."
        )
        ttk.Label(bottom_bar, textvariable=self._status_var,
                  foreground="gray").pack(side="left", padx=(12, 0))

        btn_refresh = ttk.Button(btn_frame, text="🔄 Refresh", command=self.refresh_all)
        btn_refresh.pack(side="right", padx=(6, 0))
        Tooltip(btn_refresh, "Redessiner tous les graphiques manuellement")

        btn_save = ttk.Button(btn_frame, text="💾 Save as CSV", command=self.save_csv)
        btn_save.pack(side="right", padx=(6, 0))
        Tooltip(btn_save, "Save data in a specified CSV file")

        if not self._file_mode:
            self._btn_start = ttk.Button(
                btn_frame, text="▶ Start acquisition",
                command=self._start_acquisition
            )
            self._btn_start.pack(side="right", padx=(6, 0))
            Tooltip(self._btn_start, "Connect to a serial port and start the acquisition")

            self._btn_stop = ttk.Button(
                btn_frame, text="⏹ Stop acquisition",
                command=self._stop_acquisition,
                state="disabled"
            )
            self._btn_stop.pack(side="right", padx=(6, 0))
            Tooltip(self._btn_stop, "Stop the acquisition and close serial port")
        else:
            ttk.Label(btn_frame,
                      text=f"📂 {self._csv_source_path}",
                      foreground="#555555",
                      font=("TkDefaultFont", 9)).pack(side="right", padx=(6, 0))

        # ---- Notebook of plots ------------------------------------------
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=(10, 0))

        for name, config in PLOT_CONFIGS.items():
            frame = ttk.Frame(self.notebook)
            self.notebook.add(frame, text=name)

            fig, ax = plt.subplots(figsize=(10, 6))
            canvas = FigureCanvasTkAgg(fig, master=frame)
            canvas.get_tk_widget().pack(fill="both", expand=True)

            self.figures[name]  = (fig, ax)
            self.canvases[name] = canvas

            # Toolbar lives in the shared toolbar_frame but is hidden until
            # its tab is selected
            toolbar = NavigationToolbar2Tk(canvas, self._toolbar_frame)
            toolbar.update()
            toolbar.pack_forget()          # hidden by default
            self.toolbars[name] = toolbar

            if config.get("dual"):
                create_dual_plot(ax, self.df, config)
            else:
                create_single_plot(ax, self.df, config)
            canvas.draw()

        # Show the first tab's toolbar immediately
        first = next(iter(self.toolbars))
        self.toolbars[first].pack(side="left")

        # Switch toolbar when the user changes tab
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_change)

    def _on_tab_change(self, event=None) -> None:
        selected = self.notebook.tab(self.notebook.select(), "text")
        for name, toolbar in self.toolbars.items():
            if name == selected:
                toolbar.pack(side="left")
            else:
                toolbar.pack_forget()

    # ---- File mode ------------------------------------------------------
    def _load_file(self, path: str) -> None:
        try:
            df = pd.read_csv(path)
            if df.empty:
                self._status_var.set("⚠️ Le fichier est vide.")
                return
            if "timestamp" in df.columns:
                df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
            self.df = df
            self.refresh_all()
            self._status_var.set(
                f"✅ {len(self.df)} ligne(s) chargée(s) depuis {os.path.basename(path)}"
            )
        except Exception as e:
            messagebox.showerror("Erreur de lecture", f"Impossible de lire le fichier :\n{e}")
            self._status_var.set("❌ Erreur lors du chargement.")

    # ---- Start / stop acquisition ---------------------------------------
    def _start_acquisition(self) -> None:
        if self._acquisition_running:
            return
        started = self._backend.start_acquisition(
            self._config.PORT,
            self._config.BAUDRATE,
            self._config.ID_ANALYSEUR,
            self._interval,
        )
        if started:
            self._acquisition_running = True
            self._btn_start.config(state="disabled")
            self._btn_stop.config(state="normal")
            self._status_var.set("Acquisition démarrée...")
        else:
            self._status_var.set("⚠️ Impossible de démarrer — vérifiez le port série.")

    def _stop_acquisition(self) -> None:
        if not self._acquisition_running:
            return
        self._backend.stop()
        self._acquisition_running = False
        self._btn_stop.config(state="disabled")
        self._btn_start.config(state="normal")
        self._status_var.set("Acquisition arrêtée. Cliquez ▶ pour redémarrer.")

    # ---- Queue polling --------------------------------------------------
    def schedule_poll(self) -> None:
        self._poll_after_id = self.root.after(self.POLL_INTERVAL_MS, self._poll_queue)

    def _poll_queue(self) -> None:
        if self.data_queue is None:
            return
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
        if self._autosave_path is None:
            filename = datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".csv"
            self._autosave_path = os.path.join(RECORD_DIR, filename)
            self._status_var.set(f"Enregistrement : {self._autosave_path}")
        try:
            self.df.to_csv(self._autosave_path, index=False)
        except Exception as e:
            print(f"Autosave error: {e}")

    # ---- Manual save ----------------------------------------------------
    def save_csv(self) -> None:
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
        if not path:
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
            canvas  = self.canvases[name]
            if config.get("dual"):
                create_dual_plot(ax, self.df, config)
            else:
                create_single_plot(ax, self.df, config)
            canvas.draw_idle()