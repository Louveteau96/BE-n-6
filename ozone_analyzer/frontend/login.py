"""Login / connection screen shown before the main GraphApp window.

Presents two tabs:
  - Serial connection  (port, baudrate, analyser ID, acquisition interval)
  - Open CSV file      (read-only / offline mode — not wired to new backend yet)

on_success signature
--------------------
    on_success(port: str, baudrate: int, id_analyseur: int, interval: int)

Called only for the serial tab. The login screen destroys itself and resizes
the root window before handing control to GraphApp.
"""

import tkinter as tk
from tkinter import ttk, filedialog


DELAIS_RELEVE = 5   # default acquisition interval in seconds


class LoginScreen:
    BAUDRATES = [1200, 2400, 4800, 9600, 19200, 38400, 57600, 115200]

    def __init__(self, root: tk.Tk, on_success):
        self.root       = root
        self.on_success = on_success  # callable(port, baudrate, id_analyseur, interval)

        self.root.title("Connexion – Analyseur Ozone")
        self.root.geometry("500x660")
        self.root.resizable(False, False)
        self.root.configure(bg="#1a1a2e")
        self._build_ui()

    # ------------------------------------------------------------------ UI --

    def _build_ui(self) -> None:
        # Header
        header = tk.Frame(self.root, bg="#1a1a2e")
        header.pack(pady=(32, 4))
        tk.Label(header, text="📡", font=("Arial", 42),
                 bg="#1a1a2e", fg="#e0e0ff").pack()
        tk.Label(header, text="Analyseur Ozone", font=("Georgia", 20, "bold"),
                 bg="#1a1a2e", fg="#e0e0ff").pack(pady=(4, 0))
        tk.Label(header, text="Configurez la connexion série", font=("Arial", 10),
                 bg="#1a1a2e", fg="#7070a0").pack(pady=(3, 0))

        # Notebook style
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Login.TNotebook",     background="#1a1a2e", borderwidth=0)
        style.configure("Login.TNotebook.Tab", background="#16213e", foreground="#a0a0c0",
                        padding=[20, 8], font=("Arial", 10, "bold"))
        style.map("Login.TNotebook.Tab",
                  background=[("selected", "#4f46e5")],
                  foreground=[("selected", "white")])

        self.nb = ttk.Notebook(self.root, style="Login.TNotebook")
        self.nb.pack(padx=30, pady=16, fill="both", expand=True)

        tab_serial = tk.Frame(self.nb, bg="#16213e")
        self.nb.add(tab_serial, text="  🔌 Connexion série  ")
        self._build_serial_tab(tab_serial)

        tab_file = tk.Frame(self.nb, bg="#16213e")
        self.nb.add(tab_file, text="  📂 Ouvrir un fichier  ")
        self._build_file_tab(tab_file)

        # Error label (shared, below the notebook)
        self.error_var = tk.StringVar()
        tk.Label(self.root, textvariable=self.error_var, font=("Arial", 10),
                 bg="#1a1a2e", fg="#e74c3c",
                 wraplength=440, justify="center").pack(pady=(0, 4))

    def _build_serial_tab(self, parent: tk.Frame) -> None:
        self._add_label(parent, "Port série  (ex. COM3, /dev/ttyUSB0)")
        self.port_entry = self._add_entry(parent)
        self.port_entry.insert(0, "COM3")
        self._add_separator(parent)

        self._add_label(parent, "Baudrate")
        self.baudrate_var = tk.StringVar(value="9600")
        ttk.Combobox(parent, textvariable=self.baudrate_var,
                     values=[str(b) for b in self.BAUDRATES],
                     state="readonly", font=("Arial", 13)).pack(fill="x", padx=20, pady=(0, 6))
        self._add_separator(parent)

        self._add_label(parent, "ID analyseur  (entier ≥ 0)")
        self.id_entry = self._add_entry(parent)
        self.id_entry.insert(0, "49")
        self._add_separator(parent)

        self._add_label(parent, f"Intervalle d'acquisition (secondes, défaut {DELAIS_RELEVE})")
        self.delai_entry = self._add_entry(parent)
        self.delai_entry.insert(0, str(DELAIS_RELEVE))
        self._add_separator(parent)

        btn = self._make_button(parent, "  Se connecter  ", self._handle_serial)
        btn.pack(pady=20)
        parent.bind_all(
            "<Return>",
            lambda e: self._handle_serial()
            if self.nb.index(self.nb.select()) == 0 else None,
        )

    def _build_file_tab(self, parent: tk.Frame) -> None:
        tk.Frame(parent, bg="#16213e", height=30).pack()
        tk.Label(parent,
                 text="Sélectionnez un fichier CSV enregistré\nlors d'une session précédente.",
                 font=("Arial", 11), bg="#16213e", fg="#c0c0e0",
                 justify="center").pack(pady=(10, 20))

        path_frame = tk.Frame(parent, bg="#0f3460", bd=0)
        path_frame.pack(fill="x", padx=20)
        self.file_path_var = tk.StringVar(value="Aucun fichier sélectionné")
        tk.Label(path_frame, textvariable=self.file_path_var, font=("Arial", 9),
                 bg="#0f3460", fg="#a0c0e0",
                 wraplength=400, justify="left", anchor="w").pack(fill="x", padx=10, pady=8)
        tk.Frame(parent, bg="#4f46e5", height=2).pack(fill="x", padx=20)

        self._make_button(parent, "  Parcourir…  ", self._browse_file,
                          bg="#0f3460", active_bg="#1a4a80").pack(pady=(20, 6))
        self.open_btn = self._make_button(parent, "  Ouvrir  ", self._handle_file)
        self.open_btn.pack(pady=6)
        self.open_btn.config(state="disabled")

    # -------------------------------------------------------- UI helpers --

    def _add_label(self, parent: tk.Frame, text: str) -> None:
        tk.Label(parent, text=text, font=("Arial", 10, "bold"),
                 bg="#16213e", fg="#a0a0c0", anchor="w").pack(fill="x", padx=20, pady=(14, 2))

    def _add_entry(self, parent: tk.Frame) -> tk.Entry:
        e = tk.Entry(parent, font=("Arial", 13),
                     bg="#0f3460", fg="#e0e0ff",
                     insertbackground="#e0e0ff", relief="flat", bd=0, justify="left")
        e.pack(fill="x", padx=20, ipady=8)
        return e

    def _add_separator(self, parent: tk.Frame) -> None:
        tk.Frame(parent, bg="#4f46e5", height=2).pack(fill="x", padx=20)

    def _make_button(self, parent: tk.Frame, text: str, command,
                     bg: str = "#4f46e5", active_bg: str = "#6366f1") -> tk.Button:
        btn = tk.Button(parent, text=text, font=("Arial", 12, "bold"),
                        bg=bg, fg="white",
                        activebackground=active_bg, activeforeground="white",
                        relief="flat", cursor="hand2", padx=20, pady=10,
                        command=command)
        btn.bind("<Enter>", lambda e: btn.config(bg=active_bg))
        btn.bind("<Leave>", lambda e: btn.config(bg=bg))
        return btn

    # ------------------------------------------------------- handlers --

    def _handle_serial(self) -> None:
        """Validate fields, then call on_success with connection parameters."""
        self.error_var.set("")

        port = self.port_entry.get().strip()
        if not port:
            self.error_var.set("Veuillez saisir un port série."); return

        baudrate_str = self.baudrate_var.get().strip()
        if not baudrate_str.isdigit():
            self.error_var.set("Baudrate invalide."); return
        baudrate = int(baudrate_str)

        id_str = self.id_entry.get().strip()
        if not id_str.isdigit():
            self.error_var.set("L'ID analyseur doit être un entier positif."); return
        id_analyseur = int(id_str)

        delai_str = self.delai_entry.get().strip()
        if not delai_str.isdigit() or int(delai_str) <= 0:
            self.error_var.set("L'intervalle doit être un entier strictement positif."); return
        interval = int(delai_str)

        self._launch(port, baudrate, id_analyseur, interval)

    def _browse_file(self) -> None:
        path = filedialog.askopenfilename(
            title="Ouvrir un fichier CSV",
            filetypes=[("Fichiers CSV", "*.csv"), ("Tous les fichiers", "*.*")],
        )
        if path:
            self.file_path_var.set(path)
            self.open_btn.config(state="normal")

    def _handle_file(self) -> None:
        """File-mode: not connected to the new backend yet — shows an info message."""
        self.error_var.set(
            "Le mode fichier n'est pas encore disponible dans cette version."
        )

    # ---------------------------------------------------- transition --

    def _launch(self, port: str, baudrate: int, id_analyseur: int, interval: int) -> None:
        """Destroy login widgets, resize the window, hand off to GraphApp."""
        for widget in self.root.winfo_children():
            widget.destroy()
        self.root.geometry("1250x820")
        self.root.resizable(True, True)
        self.on_success(port, baudrate, id_analyseur, interval)
