import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import pandas as pd
import os
import threading
import fnct_finales

# Tentative d'import de mplcursors (tooltip interactif)
try:
    import mplcursors
    MPLCURSORS_AVAILABLE = True
except ImportError:
    MPLCURSORS_AVAILABLE = False
    print("⚠️  mplcursors non installé. Utilisation du tooltip matplotlib natif.")
    print("   → pip install mplcursors")

# Délai entre deux relevés (secondes)
DELAIS_RELEVE = 60


# ===========================================================================
#  TOOLTIP NATIF (fallback si mplcursors absent)
# ===========================================================================

class NativeTooltip:
    def __init__(self, ax, canvas, line, x_label="X", y_label="Y", color="#2ecc71"):
        self.ax = ax
        self.canvas = canvas
        self.line = line
        self.x_label = x_label
        self.y_label = y_label
        self.color = color

        self.annot = ax.annotate(
            "",
            xy=(0, 0),
            xytext=(15, 15),
            textcoords="offset points",
            bbox=dict(boxstyle="round,pad=0.5", fc="#1a1a2e", ec=color, lw=1.5, alpha=0.92),
            arrowprops=dict(arrowstyle="->", color=color, lw=1.2),
            fontsize=9,
            color="#e0e0ff",
            fontfamily="monospace",
            visible=False,
            zorder=10,
        )

        self.highlight, = ax.plot(
            [], [], "o", color=color, markersize=10, alpha=0.85, zorder=9, visible=False,
        )

        self._cid_motion = canvas.mpl_connect("motion_notify_event", self._on_hover)
        self._cid_leave  = canvas.mpl_connect("axes_leave_event",   self._on_leave)

    _HIT_RADIUS = 6

    def _on_hover(self, event):
        if event.inaxes != self.ax:
            self._hide()
            return
        xdata = self.line.get_xdata()
        ydata = self.line.get_ydata()
        if len(xdata) == 0:
            return
        xy_pixels = self.ax.transData.transform(list(zip(xdata, ydata)))
        distances = ((xy_pixels[:, 0] - event.x) ** 2 + (xy_pixels[:, 1] - event.y) ** 2) ** 0.5
        idx = distances.argmin()
        changed = False
        if distances[idx] <= self._HIT_RADIUS:
            x, y = xdata[idx], ydata[idx]
            self.annot.xy = (x, y)
            self.annot.set_text(f"  {self.x_label}: {x}\n  {self.y_label}: {y:.4g}")
            if not self.annot.get_visible():
                self.annot.set_visible(True)
                self.highlight.set_data([x], [y])
                self.highlight.set_visible(True)
                changed = True
            elif self.highlight.get_xdata()[0] != x or self.highlight.get_ydata()[0] != y:
                self.highlight.set_data([x], [y])
                changed = True
        else:
            changed = self._hide()
        if changed:
            self.canvas.draw_idle()

    def _on_leave(self, event):
        if self._hide():
            self.canvas.draw_idle()

    def _hide(self):
        changed = self.annot.get_visible() or self.highlight.get_visible()
        self.annot.set_visible(False)
        self.highlight.set_visible(False)
        return changed

    def remove(self):
        self.canvas.mpl_disconnect(self._cid_motion)
        self.canvas.mpl_disconnect(self._cid_leave)


# ===========================================================================
#  UTILITAIRE : attacher le bon système de tooltip
# ===========================================================================

def attach_tooltip(ax, canvas, lines, x_label="X", y_label="Y", colors=None):
    tooltips = []
    if MPLCURSORS_AVAILABLE:
        cursor = mplcursors.cursor(lines, hover=mplcursors.HoverMode.Transient)

        @cursor.connect("add")
        def on_add(sel):
            x, y = sel.target
            line_color = sel.artist.get_color()
            sel.annotation.set_text(f"  {x_label}: {x}\n  {y_label}: {y:.4g}")
            sel.annotation.get_bbox_patch().set(
                facecolor="#1a1a2e", edgecolor=line_color, alpha=0.92, linewidth=1.5,
            )
            sel.annotation.set_fontsize(9)
            sel.annotation.set_color("#e0e0ff")
            sel.annotation.set_fontfamily("monospace")
            sel.annotation.draggable(False)

        tooltips.append(cursor)
    else:
        for i, line in enumerate(lines):
            color = colors[i] if colors and i < len(colors) else "#4f46e5"
            tip = NativeTooltip(ax, canvas, line, x_label, y_label, color)
            tooltips.append(tip)
    return tooltips


# ===========================================================================
#  ÉCRAN DE CONNEXION
# ===========================================================================

class LoginScreen:
    """
    Collecte port, baudrate et id_analyseur, appelle fnct_finales.connexion(),
    crée le CSV de session via fnct_finales.creer_csv(), démarre le thread de
    récupération, puis lance GraphApp avec le chemin CSV.
    """

    BAUDRATES = [1200, 2400, 4800, 9600, 19200, 38400, 57600, 115200]

    def __init__(self, root, on_success):
        self.root = root
        self.on_success = on_success   # appelé avec (root, csv_path)

        self.root.title("Connexion – Analyse de Données")
        self.root.geometry("460x580")
        self.root.resizable(False, False)
        self.root.configure(bg="#1a1a2e")

        self._build_ui()
        self.root.bind("<Return>", lambda e: self._handle_login())

    # ------------------------------------------------------------------ UI --

    def _build_ui(self):
        header = tk.Frame(self.root, bg="#1a1a2e")
        header.pack(pady=(40, 6))

        tk.Label(header, text="📡", font=("Arial", 44), bg="#1a1a2e", fg="#e0e0ff").pack()
        tk.Label(
            header, text="Analyse de Données",
            font=("Georgia", 20, "bold"), bg="#1a1a2e", fg="#e0e0ff",
        ).pack(pady=(6, 0))
        tk.Label(
            header, text="Configurez la connexion série à l'analyseur",
            font=("Arial", 10), bg="#1a1a2e", fg="#7070a0",
        ).pack(pady=(4, 0))

        form = tk.Frame(self.root, bg="#16213e", bd=0, relief="flat")
        form.pack(padx=40, pady=20, fill="x", ipady=8)

        # Port série
        self._add_label(form, "Port série  (ex. COM3, /dev/ttyUSB0)")
        self.port_entry = self._add_entry(form)
        self.port_entry.insert(0, "COM3")
        self.port_entry.focus()
        self._add_separator(form)

        # Baudrate
        self._add_label(form, "Baudrate")
        self.baudrate_var = tk.StringVar(value="9600")
        ttk.Combobox(
            form,
            textvariable=self.baudrate_var,
            values=[str(b) for b in self.BAUDRATES],
            state="readonly",
            font=("Arial", 13),
            width=20,
        ).pack(fill="x", padx=20, pady=(0, 6))
        self._add_separator(form)

        # ID analyseur
        self._add_label(form, "ID analyseur  (entier ≥ 0)")
        self.id_entry = self._add_entry(form)
        self.id_entry.insert(0, "0")
        self._add_separator(form)

        # Délai de relevé
        self._add_label(form, f"Délai de relevé (secondes, défaut {DELAIS_RELEVE})")
        self.delai_entry = self._add_entry(form)
        self.delai_entry.insert(0, str(DELAIS_RELEVE))
        self._add_separator(form)

        # Message d'erreur
        self.error_var = tk.StringVar()
        tk.Label(
            self.root, textvariable=self.error_var,
            font=("Arial", 10), bg="#1a1a2e", fg="#e74c3c",
            wraplength=380, justify="center",
        ).pack(pady=(4, 0))

        # Bouton
        btn = tk.Button(
            self.root,
            text="  Connexion  ",
            font=("Arial", 12, "bold"),
            bg="#4f46e5", fg="white",
            activebackground="#6366f1", activeforeground="white",
            relief="flat", cursor="hand2",
            padx=20, pady=10,
            command=self._handle_login,
        )
        btn.pack(pady=(16, 0))
        btn.bind("<Enter>", lambda e: btn.config(bg="#6366f1"))
        btn.bind("<Leave>", lambda e: btn.config(bg="#4f46e5"))

    def _add_label(self, parent, text):
        tk.Label(
            parent, text=text,
            font=("Arial", 10, "bold"), bg="#16213e", fg="#a0a0c0", anchor="w",
        ).pack(fill="x", padx=20, pady=(14, 2))

    def _add_entry(self, parent):
        e = tk.Entry(
            parent,
            font=("Arial", 13), bg="#0f3460", fg="#e0e0ff",
            insertbackground="#e0e0ff", relief="flat", bd=0, justify="left",
        )
        e.pack(fill="x", padx=20, ipady=8)
        return e

    def _add_separator(self, parent):
        tk.Frame(parent, bg="#4f46e5", height=2).pack(fill="x", padx=20)

    # ------------------------------------------------------------ logique --

    def _handle_login(self):
        self.error_var.set("")

        # Validation port
        port = self.port_entry.get().strip()
        if not port:
            self.error_var.set("Veuillez saisir un port série.")
            return

        # Validation baudrate
        baudrate_str = self.baudrate_var.get().strip()
        if not baudrate_str.isdigit():
            self.error_var.set("Baudrate invalide.")
            return
        baudrate = int(baudrate_str)

        # Validation ID analyseur
        id_str = self.id_entry.get().strip()
        if not id_str.isdigit():
            self.error_var.set("L'ID analyseur doit être un entier positif.")
            return
        id_analyseur = int(id_str)

        # Validation délai
        delai_str = self.delai_entry.get().strip()
        if not delai_str.isdigit() or int(delai_str) <= 0:
            self.error_var.set("Le délai doit être un entier strictement positif.")
            return
        delai = int(delai_str)

        # Connexion série
        try:
            ser = fnct_finales.connexion(port, baudrate, id_analyseur)
        except Exception as exc:
            self.error_var.set(f"Erreur connexion : {exc}")
            return

        if not ser:
            self.error_var.set(
                f"Impossible de se connecter sur {port} "
                f"(baudrate={baudrate}, id={id_analyseur})."
            )
            return

        # Création du CSV de session
        try:
            csv_path = fnct_finales.creer_csv()
        except Exception as exc:
            self.error_var.set(f"Erreur création CSV : {exc}")
            return

        # Démarrage du thread de récupération (daemon → s'arrête avec l'appli)
        t = threading.Thread(
            target=fnct_finales.recuperation_donnees,
            args=(ser, csv_path, delai),
            daemon=True,
        )
        t.start()

        self._launch_app(csv_path)

    def _launch_app(self, csv_path):
        for widget in self.root.winfo_children():
            widget.destroy()

        self.root.geometry("1100x720")
        self.root.resizable(True, True)

        self.on_success(self.root, csv_path)


# ===========================================================================
#  APPLICATION PRINCIPALE
# ===========================================================================

# Colonnes produites par fnct_finales.creer_csv() / ajouter_donnees() :
#   heure | date | flag | o3 | cellA | cellB | benchT | lampT | o3lamp | flowA | flowB | pression
#
# On utilise "heure" comme axe X pour tous les graphiques.

X_COL = "heure"

TABS_CONFIG = {
    "Ozone":     {"col": "o3",       "color": "#2ecc71", "ylabel": "Concentration O₃ (ppb)"},
    "Pression":  {"col": "pression", "color": "#3498db", "ylabel": "Pression (hPa)"},
    "O3 Lamp":   {"col": "o3lamp",   "color": "#9b59b6", "ylabel": "Puissance lampe O₃"},
    "Bench T":   {"col": "benchT",   "color": "#e67e22", "ylabel": "Température bench (°C)"},
    "Lamp T":    {"col": "lampT",    "color": "#e74c3c", "ylabel": "Température lampe (°C)"},
}

DUAL_TABS_CONFIG = {
    "Cell": {
        "A": {"col": "cellA", "color": "#1abc9c", "ylabel": "Signal cellule", "title": "Cell A"},
        "B": {"col": "cellB", "color": "#16a085", "ylabel": "Signal cellule", "title": "Cell B"},
    },
    "Flow": {
        "A": {"col": "flowA", "color": "#e74c3c", "ylabel": "Débit (L/min)", "title": "Flow A"},
        "B": {"col": "flowB", "color": "#c0392b", "ylabel": "Débit (L/min)", "title": "Flow B"},
    },
}


class GraphApp:
    def __init__(self, root, csv_path: str):
        """
        csv_path : chemin du fichier CSV créé par fnct_finales.creer_csv()
                   et alimenté en continu par le thread recuperation_donnees.
        """
        self.root     = root
        self.csv_path = csv_path
        self.root.title(f"Analyse de Données — {os.path.basename(csv_path)}")

        style = ttk.Style()
        style.configure("TNotebook.Tab", padding=[18, 8], font=("Arial", 10))

        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        self.figures  = {}
        self.canvases = {}
        self.tooltips = {}

        self._create_tabs()

        # Barre du bas : info fichier + bouton rafraîchir
        bottom = ttk.Frame(root)
        bottom.pack(fill="x", padx=10, pady=(0, 6))

        ttk.Label(
            bottom,
            text=f"📁 {csv_path}",
            font=("Arial", 9),
            foreground="#666666",
        ).pack(side="left")

        ttk.Button(
            bottom,
            text="🔄 Rafraîchir tous les graphiques",
            command=self.refresh_all,
        ).pack(side="right")

    # ---------------------------------------------------------------- tabs --

    def _create_tabs(self):
        for tab_name, config in TABS_CONFIG.items():
            frame = ttk.Frame(self.notebook)
            self.notebook.add(frame, text=tab_name)
            self._create_graph(frame, tab_name, config)

        for tab_name, configs in DUAL_TABS_CONFIG.items():
            frame = ttk.Frame(self.notebook)
            self.notebook.add(frame, text=tab_name)
            self._create_dual_graph(frame, tab_name, configs)

    def _create_graph(self, parent, tab_name, config):
        graph_frame = ttk.Frame(parent)
        graph_frame.pack(fill="both", expand=True, padx=5, pady=5)

        fig, ax = plt.subplots(figsize=(10, 6), dpi=100)
        fig.patch.set_facecolor("#f0f0f0")
        self.figures[tab_name]  = (fig, ax)

        canvas = FigureCanvasTkAgg(fig, master=graph_frame)
        canvas.get_tk_widget().pack(fill="both", expand=True)
        self.canvases[tab_name] = canvas

        self._plot(ax, tab_name, config, canvas)
        canvas.draw()

        toolbar_frame = ttk.Frame(parent)
        toolbar_frame.pack(fill="x")
        NavigationToolbar2Tk(canvas, toolbar_frame).update()

        ttk.Button(
            toolbar_frame, text="🔄 Rafraîchir",
            command=lambda t=tab_name, c=config: self._refresh_single(t, c),
        ).pack(side="right", padx=5)

    def _create_dual_graph(self, parent, tab_name, configs):
        graph_frame = ttk.Frame(parent)
        graph_frame.pack(fill="both", expand=True, padx=5, pady=5)

        fig, ax = plt.subplots(figsize=(10, 6), dpi=100)
        fig.patch.set_facecolor("#f0f0f0")
        key = f"{tab_name}_dual"
        self.figures[key]  = (fig, ax)

        canvas = FigureCanvasTkAgg(fig, master=graph_frame)
        canvas.get_tk_widget().pack(fill="both", expand=True)
        self.canvases[key] = canvas

        self._plot_dual(ax, tab_name, configs, canvas)
        canvas.draw()

        toolbar_frame = ttk.Frame(parent)
        toolbar_frame.pack(fill="x")
        NavigationToolbar2Tk(canvas, toolbar_frame).update()

        ttk.Button(
            toolbar_frame, text="🔄 Rafraîchir",
            command=lambda t=tab_name, c=configs: self._refresh_dual(t, c),
        ).pack(side="right", padx=5)

    # --------------------------------------------------------------- plot --

    def _load_csv(self):
        """Charge le CSV de session. Retourne un DataFrame ou None."""
        if not os.path.exists(self.csv_path):
            return None
        try:
            df = pd.read_csv(self.csv_path)
            return df if not df.empty else None
        except Exception:
            return None

    def _clear_tooltips(self, key):
        for tip in self.tooltips.get(key, []):
            try:
                tip.remove()
            except Exception:
                pass
        self.tooltips[key] = []

    def _plot(self, ax, tab_name, config, canvas=None):
        ax.clear()
        self._clear_tooltips(tab_name)

        df = self._load_csv()

        if df is None:
            ax.text(0.5, 0.5,
                    f"En attente de données…\n{self.csv_path}",
                    ha="center", va="center", fontsize=12,
                    transform=ax.transAxes, color="gray")
        elif config["col"] not in df.columns:
            ax.text(0.5, 0.5,
                    f"Colonne '{config['col']}' introuvable dans le CSV.",
                    ha="center", va="center", fontsize=12,
                    transform=ax.transAxes, color="red")
        else:
            x_data = df[X_COL]
            y_data = pd.to_numeric(df[config["col"]], errors="coerce")

            line, = ax.plot(
                x_data, y_data,
                color=config["color"], linewidth=2,
                marker="o", markersize=4, alpha=0.8,
            )
            ax.fill_between(range(len(y_data)), y_data, alpha=0.2, color=config["color"])
            ax.set_xticks(range(len(x_data)))
            ax.set_xticklabels(x_data, rotation=45, ha="right", fontsize=8)
            ax.set_ylabel(config["ylabel"], fontsize=11)

            if canvas:
                tips = attach_tooltip(
                    ax, canvas, [line],
                    x_label=X_COL, y_label=config["col"],
                    colors=[config["color"]],
                )
                self.tooltips[tab_name] = tips

        ax.set_title(tab_name, fontsize=14, fontweight="bold", pad=15)
        ax.grid(True, linestyle="--", alpha=0.7)
        ax.set_facecolor("#fafafa")

    def _plot_dual(self, ax, tab_name, configs, canvas=None):
        ax.clear()
        key = f"{tab_name}_dual"
        self._clear_tooltips(key)

        df     = self._load_csv()
        lines  = []
        colors = []

        if df is None:
            ax.text(0.5, 0.5,
                    "En attente de données…",
                    ha="center", va="center", fontsize=12,
                    transform=ax.transAxes, color="gray")
        else:
            x_data = df[X_COL]
            for k in ("A", "B"):
                cfg = configs[k]
                if cfg["col"] not in df.columns:
                    continue
                y_data = pd.to_numeric(df[cfg["col"]], errors="coerce")
                line, = ax.plot(
                    x_data, y_data,
                    color=cfg["color"], linewidth=2,
                    marker="o", markersize=4, alpha=0.8,
                    label=cfg["title"],
                )
                ax.fill_between(range(len(y_data)), y_data, alpha=0.15, color=cfg["color"])
                lines.append(line)
                colors.append(cfg["color"])

            ax.set_xticks(range(len(x_data)))
            ax.set_xticklabels(x_data, rotation=45, ha="right", fontsize=8)
            ax.set_ylabel(list(configs.values())[0]["ylabel"], fontsize=11)

            if canvas and lines:
                tips = attach_tooltip(
                    ax, canvas, lines,
                    x_label=X_COL,
                    y_label=list(configs.values())[0]["ylabel"],
                    colors=colors,
                )
                self.tooltips[key] = tips

        ax.set_title(tab_name, fontsize=14, fontweight="bold", pad=15)
        ax.grid(True, linestyle="--", alpha=0.7)
        ax.set_facecolor("#fafafa")
        ax.legend(fontsize=10)

    # ---------------------------------------------------------- refresh --

    def _refresh_single(self, tab_name, config):
        fig, ax = self.figures[tab_name]
        canvas  = self.canvases[tab_name]
        self._plot(ax, tab_name, config, canvas)
        canvas.draw()

    def _refresh_dual(self, tab_name, configs):
        key    = f"{tab_name}_dual"
        fig, ax = self.figures[key]
        canvas  = self.canvases[key]
        self._plot_dual(ax, tab_name, configs, canvas)
        canvas.draw()

    def refresh_all(self):
        for tab_name, config in TABS_CONFIG.items():
            self._refresh_single(tab_name, config)
        for tab_name, configs in DUAL_TABS_CONFIG.items():
            self._refresh_dual(tab_name, configs)
        messagebox.showinfo("Rafraîchissement", "Tous les graphiques ont été mis à jour.")


# ===========================================================================
#  POINT D'ENTRÉE
# ===========================================================================

if __name__ == "__main__":
    root = tk.Tk()
    LoginScreen(root, on_success=lambda r, csv_path: GraphApp(r, csv_path))
    root.mainloop()