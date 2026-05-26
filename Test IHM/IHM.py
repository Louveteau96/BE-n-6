import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import pandas as pd
import os
import fnct_finales

# Tentative d'import de mplcursors (tooltip interactif)
try:
    import mplcursors
    MPLCURSORS_AVAILABLE = True
except ImportError:
    MPLCURSORS_AVAILABLE = False
    print("⚠️  mplcursors non installé. Utilisation du tooltip matplotlib natif.")
    print("   → pip install mplcursors")


# ===========================================================================
#  TOOLTIP NATIF (fallback si mplcursors absent)
# ===========================================================================

class NativeTooltip:
    """
    Tooltip de survol utilisant uniquement matplotlib (sans dépendance externe).
    Affiche les coordonnées X/Y du point le plus proche du curseur.
    """

    def __init__(self, ax, canvas, line, x_label="X", y_label="Y", color="#2ecc71"):
        self.ax = ax
        self.canvas = canvas
        self.line = line
        self.x_label = x_label
        self.y_label = y_label
        self.color = color

        # Annotation invisible au départ
        self.annot = ax.annotate(
            "",
            xy=(0, 0),
            xytext=(15, 15),
            textcoords="offset points",
            bbox=dict(
                boxstyle="round,pad=0.5",
                fc="#1a1a2e",
                ec=color,
                lw=1.5,
                alpha=0.92,
            ),
            arrowprops=dict(
                arrowstyle="->",
                color=color,
                lw=1.2,
            ),
            fontsize=9,
            color="#e0e0ff",
            fontfamily="monospace",
            visible=False,
            zorder=10,
        )

        # Point mis en évidence au survol
        self.highlight, = ax.plot(
            [], [], "o",
            color=color,
            markersize=10,
            alpha=0.85,
            zorder=9,
            visible=False,
        )

        self._cid_motion = canvas.mpl_connect("motion_notify_event", self._on_hover)
        self._cid_leave  = canvas.mpl_connect("axes_leave_event",   self._on_leave)

    # Rayon de détection en pixels — doit correspondre au markersize du tracé.
    # markersize=4 → rayon visuel ≈ 4 px ; on ajoute 2 px de tolérance.
    _HIT_RADIUS = 6

    def _on_hover(self, event):
        if event.inaxes != self.ax:
            self._hide()
            return

        xdata = self.line.get_xdata()
        ydata = self.line.get_ydata()
        if len(xdata) == 0:
            return

        # Transforme les données en pixels pour calculer la distance écran
        xy_pixels = self.ax.transData.transform(list(zip(xdata, ydata)))
        distances = (
            (xy_pixels[:, 0] - event.x) ** 2 +
            (xy_pixels[:, 1] - event.y) ** 2
        ) ** 0.5

        idx     = distances.argmin()
        changed = False

        if distances[idx] <= self._HIT_RADIUS:
            x, y = xdata[idx], ydata[idx]
            self.annot.xy = (x, y)
            self.annot.set_text(
                f"  {self.x_label}: {x:.4g}\n  {self.y_label}: {y:.4g}"
            )
            if not self.annot.get_visible():
                self.annot.set_visible(True)
                self.highlight.set_data([x], [y])
                self.highlight.set_visible(True)
                changed = True
            elif (self.highlight.get_xdata()[0] != x or
                  self.highlight.get_ydata()[0] != y):
                self.highlight.set_data([x], [y])
                changed = True
        else:
            changed = self._hide()

        if changed:
            self.canvas.draw_idle()

    def _on_leave(self, event):
        """Masque le tooltip dès que le curseur quitte la zone du graphique."""
        if self._hide():
            self.canvas.draw_idle()

    def _hide(self):
        """Masque annotation + highlight. Retourne True si un changement a eu lieu."""
        changed = self.annot.get_visible() or self.highlight.get_visible()
        self.annot.set_visible(False)
        self.highlight.set_visible(False)
        return changed

    def remove(self):
        """Déconnecte les événements (utile au rafraîchissement)."""
        self.canvas.mpl_disconnect(self._cid_motion)
        self.canvas.mpl_disconnect(self._cid_leave)


# ===========================================================================
#  UTILITAIRE : attacher le bon système de tooltip
# ===========================================================================

def attach_tooltip(ax, canvas, lines, x_label="X", y_label="Y", colors=None):
    """
    Attache un tooltip à une liste de lignes matplotlib.

    Utilise mplcursors si disponible, sinon NativeTooltip.
    Retourne la liste des objets tooltip créés (pour pouvoir les supprimer
    lors d'un rafraîchissement).
    """
    tooltips = []

    if MPLCURSORS_AVAILABLE:
        # HoverMode.Transient : l'annotation disparaît dès que le curseur
        # quitte le point (comportement strict demandé).
        cursor = mplcursors.cursor(lines, hover=mplcursors.HoverMode.Transient)

        @cursor.connect("add")
        def on_add(sel):
            x, y = sel.target
            line_color = sel.artist.get_color()
            sel.annotation.set_text(
                f"  {x_label}: {x:.4g}\n  {y_label}: {y:.4g}"
            )
            sel.annotation.get_bbox_patch().set(
                facecolor="#1a1a2e",
                edgecolor=line_color,
                alpha=0.92,
                linewidth=1.5,
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
    """Fenêtre de connexion par numéro de port."""
 
    def __init__(self, root, on_success):
        self.root = root
        self.on_success = on_success
 
        self.root.title("Connexion – Analyse de Données")
        self.root.geometry("420x420")
        self.root.resizable(False, False)
        self.root.configure(bg="#1a1a2e")
 
        self._build_ui()
        self.root.bind("<Return>", lambda e: self._handle_login())
 
    # ------------------------------------------------------------------ UI --
 
    def _build_ui(self):
        # ── Titre / logo ──────────────────────────────────────────────────
        header = tk.Frame(self.root, bg="#1a1a2e")
        header.pack(pady=(50, 10))
 
        tk.Label(
            header, text="📊", font=("Arial", 48),
            bg="#1a1a2e", fg="#e0e0ff"
        ).pack()
 
        tk.Label(
            header, text="Analyse de Données",
            font=("Georgia", 20, "bold"),
            bg="#1a1a2e", fg="#e0e0ff"
        ).pack(pady=(8, 0))
 
        tk.Label(
            header, text="Entrez le numéro de port pour vous connecter",
            font=("Arial", 10),
            bg="#1a1a2e", fg="#7070a0"
        ).pack(pady=(4, 0))
 
        # ── Champ port ────────────────────────────────────────────────────
        form = tk.Frame(self.root, bg="#16213e", bd=0, relief="flat")
        form.pack(padx=40, pady=30, fill="x", ipady=10)
 
        tk.Label(
            form, text="Numéro de port",
            font=("Arial", 10, "bold"),
            bg="#16213e", fg="#a0a0c0",
            anchor="w"
        ).pack(fill="x", padx=20, pady=(14, 2))
 
        self.port_entry = tk.Entry(
            form,
            font=("Arial", 14),
            bg="#0f3460", fg="#e0e0ff",
            insertbackground="#e0e0ff",
            relief="flat", bd=0,
            justify="center"
        )
        self.port_entry.pack(fill="x", padx=20, ipady=10)
        self.port_entry.focus()
 
        tk.Frame(form, bg="#4f46e5", height=2).pack(fill="x", padx=20)
 
        # ── Message d'erreur ──────────────────────────────────────────────
        self.error_var = tk.StringVar()
        tk.Label(
            self.root, textvariable=self.error_var,
            font=("Arial", 10), bg="#1a1a2e", fg="#e74c3c"
        ).pack()
 
        # ── Bouton Connexion ──────────────────────────────────────────────
        btn = tk.Button(
            self.root,
            text="  Connexion  ",
            font=("Arial", 12, "bold"),
            bg="#4f46e5", fg="white",
            activebackground="#6366f1", activeforeground="white",
            relief="flat", cursor="hand2",
            padx=20, pady=10,
            command=self._handle_login
        )
        btn.pack(pady=(10, 0))
 
        btn.bind("<Enter>", lambda e: btn.config(bg="#6366f1"))
        btn.bind("<Leave>", lambda e: btn.config(bg="#4f46e5"))
 
    # ------------------------------------------------------------ logique --
 
    def connexion(self, port: int) -> bool:
        """
        Fonction de connexion à personnaliser.
        Reçoit le numéro de port (entier) et retourne True si la connexion
        est établie, False sinon.
 
        Exemples d'implémentation :
          - Tentative de connexion socket sur le port donné
          - Vérification dans une liste de ports autorisés
          - Appel à une API avec le port comme paramètre
        """
        # ----  REMPLACEZ CET EXEMPLE PAR VOTRE VRAIE LOGIQUE  ----
        return port == 8080
        # ----------------------------------------------------------
 
    def _handle_login(self):
        """Appelée par le bouton ou la touche Entrée."""
        raw = self.port_entry.get().strip()
 
        if not raw:
            self.error_var.set("Veuillez entrer un numéro de port.")
            return
 
        if not raw.isdigit():
            self.error_var.set("Le port doit être un nombre entier.")
            return
 
        port = int(raw)
        if not (1 <= port <= 65535):
            self.error_var.set("Port invalide (plage : 1 – 65535).")
            return
 
        if self.connexion(port):
            self.error_var.set("")
            self._launch_app()
        else:
            self.error_var.set(f"Impossible de se connecter sur le port {port}.")
            self.port_entry.select_range(0, "end")
 
    def _launch_app(self):
        """Détruit l'écran de connexion et affiche l'application principale."""
        # Supprimer tous les widgets actuels
        for widget in self.root.winfo_children():
            widget.destroy()
 
        # Redimensionner la fenêtre pour l'application
        self.root.geometry("1000x700")
        self.root.resizable(True, True)
        self.root.configure(bg="")        # couleur par défaut du système
 
        # Lancer l'application principale dans la même fenêtre
        self.on_success(self.root)
 
# ===========================================================================
#  APPLICATION PRINCIPALE
# ===========================================================================

class GraphApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Analyse de Données")

        style = ttk.Style()
        style.configure("TNotebook.Tab", padding=[20, 10], font=("Arial", 10))

        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        self.tabs_config = {
            "Ozone":        {"file": "data/ozone.csv",        "color": "#2ecc71", "ylabel": "Concentration O₃ (ppb)"},
            "Pression":     {"file": "data/pression.csv",     "color": "#3498db", "ylabel": "Pression (hPa)"},
            "O3 Lamp":      {"file": "data/o3_lamp.csv",      "color": "#9b59b6", "ylabel": "Puissance (W)"},
            "Lamp Setting": {"file": "data/lamp_setting.csv", "color": "#1abc9c", "ylabel": "Réglage (%)"},
            "Coef":         {"file": "data/coef.csv",         "color": "#e67e22", "ylabel": "Coefficient"},
        }

        self.dual_tabs_config = {
            "Flow": {
                "A": {"file": "data/flow.csv", "col": "Débit A (L/min)", "color": "#e74c3c", "ylabel": "Débit (L/min)", "title": "Flow A"},
                "B": {"file": "data/flow.csv", "col": "Débit B (L/min)", "color": "#c0392b", "ylabel": "Débit (L/min)", "title": "Flow B"},
            },
            "Intensité": {
                "A": {"file": "data/intensite.csv", "col": "Intensité A (mA)", "color": "#f39c12", "ylabel": "Intensité (mA)", "title": "Intensité A"},
                "B": {"file": "data/intensite.csv", "col": "Intensité B (mA)", "color": "#d68910", "ylabel": "Intensité (mA)", "title": "Intensité B"},
            },
        }

        self.figures   = {}
        self.canvases  = {}
        # Stocke les tooltips actifs pour pouvoir les nettoyer au refresh
        self.tooltips  = {}

        self.create_tabs()

        refresh_frame = ttk.Frame(root)
        refresh_frame.pack(fill="x", padx=10, pady=5)

        ttk.Button(
            refresh_frame,
            text="🔄 Rafraîchir tous les graphiques",
            command=self.refresh_all,
        ).pack(side="right")

    # ---------------------------------------------------------------- tabs --

    def create_tabs(self):
        for tab_name, config in self.tabs_config.items():
            tab_frame = ttk.Frame(self.notebook)
            self.notebook.add(tab_frame, text=tab_name)
            self.create_graph(tab_frame, tab_name, config)

        for tab_name, configs in self.dual_tabs_config.items():
            tab_frame = ttk.Frame(self.notebook)
            self.notebook.add(tab_frame, text=tab_name)
            self.create_dual_graph(tab_frame, tab_name, configs)

    def create_graph(self, parent, tab_name, config):
        graph_frame = ttk.Frame(parent)
        graph_frame.pack(fill="both", expand=True, padx=5, pady=5)

        fig, ax = plt.subplots(figsize=(10, 6), dpi=100)
        fig.patch.set_facecolor("#f0f0f0")

        self.figures[tab_name] = (fig, ax)

        canvas = FigureCanvasTkAgg(fig, master=graph_frame)
        canvas.get_tk_widget().pack(fill="both", expand=True)
        self.canvases[tab_name] = canvas

        self.plot_data(ax, tab_name, config, canvas)

        canvas.draw()

        toolbar_frame = ttk.Frame(parent)
        toolbar_frame.pack(fill="x")
        NavigationToolbar2Tk(canvas, toolbar_frame).update()

        ttk.Button(
            toolbar_frame, text="🔄 Rafraîchir",
            command=lambda t=tab_name, c=config: self.refresh_single(t, c),
        ).pack(side="right", padx=5)

    def create_dual_graph(self, parent, tab_name, configs):
        graph_frame = ttk.Frame(parent)
        graph_frame.pack(fill="both", expand=True, padx=5, pady=5)

        fig, ax = plt.subplots(figsize=(10, 6), dpi=100)
        fig.patch.set_facecolor("#f0f0f0")

        self.figures[f"{tab_name}_dual"] = fig

        canvas = FigureCanvasTkAgg(fig, master=graph_frame)
        canvas.get_tk_widget().pack(fill="both", expand=True)
        self.canvases[f"{tab_name}_dual"] = canvas

        self.plot_dual_data(ax, tab_name, configs, canvas)

        canvas.draw()

        toolbar_frame = ttk.Frame(parent)
        toolbar_frame.pack(fill="x")
        NavigationToolbar2Tk(canvas, toolbar_frame).update()

        ttk.Button(
            toolbar_frame, text="🔄 Rafraîchir",
            command=lambda t=tab_name, c=configs: self.refresh_dual(t, c),
        ).pack(side="right", padx=5)

    # --------------------------------------------------------------- plot --

    def _clear_tooltips(self, key):
        """Supprime les tooltips existants pour une clé donnée."""
        for tip in self.tooltips.get(key, []):
            if MPLCURSORS_AVAILABLE:
                try:
                    tip.remove()
                except Exception:
                    pass
            else:
                try:
                    tip.remove()
                except Exception:
                    pass
        self.tooltips[key] = []

    def plot_data(self, ax, tab_name, config, canvas=None):
        ax.clear()
        self._clear_tooltips(tab_name)

        file_path = config["file"]
        lines = []

        try:
            if os.path.exists(file_path):
                df = pd.read_csv(file_path)
                if len(df.columns) >= 2:
                    x_col, y_col = df.columns[0], df.columns[1]
                    line, = ax.plot(
                        df[x_col], df[y_col],
                        color=config["color"],
                        linewidth=2, marker="o", markersize=4, alpha=0.8,
                    )
                    ax.fill_between(df[x_col], df[y_col], alpha=0.2, color=config["color"])
                    ax.set_xlabel(x_col, fontsize=11)
                    ax.set_ylabel(config["ylabel"], fontsize=11)
                    lines.append(line)

                    # ── Tooltip ──────────────────────────────────────────
                    if canvas:
                        tips = attach_tooltip(
                            ax, canvas, lines,
                            x_label=x_col,
                            y_label=y_col,
                            colors=[config["color"]],
                        )
                        self.tooltips[tab_name] = tips
                else:
                    ax.text(0.5, 0.5, "Format CSV invalide\n(minimum 2 colonnes requises)",
                            ha="center", va="center", fontsize=12, transform=ax.transAxes)
            else:
                ax.text(0.5, 0.5,
                        f"Fichier non trouvé:\n{file_path}\n\nCréez le fichier CSV avec vos données.",
                        ha="center", va="center", fontsize=12,
                        transform=ax.transAxes, color="gray")
        except Exception as e:
            ax.text(0.5, 0.5, f"Erreur de chargement:\n{str(e)}",
                    ha="center", va="center", fontsize=12,
                    transform=ax.transAxes, color="red")

        ax.set_title(config.get("title", tab_name), fontsize=14, fontweight="bold", pad=15)
        ax.grid(True, linestyle="--", alpha=0.7)
        ax.set_facecolor("#fafafa")

    def plot_dual_data(self, ax, tab_name, configs, canvas=None):
        ax.clear()
        key = f"{tab_name}_dual"
        self._clear_tooltips(key)

        x_label = None
        lines  = []
        colors = []

        for k in ("A", "B"):
            config    = configs[k]
            file_path = config["file"]
            try:
                if os.path.exists(file_path):
                    df    = pd.read_csv(file_path)
                    x_col = df.columns[0]
                    y_col = config.get("col", df.columns[1])
                    if y_col not in df.columns:
                        raise ValueError(f"Colonne '{y_col}' introuvable")
                    x_label = x_col
                    line, = ax.plot(
                        df[x_col], df[y_col],
                        color=config["color"], linewidth=2,
                        marker="o", markersize=4, alpha=0.8,
                        label=config["title"],
                    )
                    ax.fill_between(df[x_col], df[y_col], alpha=0.15, color=config["color"])
                    lines.append(line)
                    colors.append(config["color"])
                else:
                    ax.text(0.5, 0.5, f"Fichier non trouvé:\n{file_path}",
                            ha="center", va="center", fontsize=12,
                            transform=ax.transAxes, color="gray")
            except Exception as e:
                ax.text(0.5, 0.5, f"Erreur ({k}):\n{str(e)}",
                        ha="center", va="center", fontsize=12,
                        transform=ax.transAxes, color="red")

        # ── Tooltip sur les deux courbes ──────────────────────────────────
        if canvas and lines:
            # Pour les dual graphs, on prend le ylabel du premier config
            y_lbl = list(configs.values())[0]["ylabel"]
            tips = attach_tooltip(
                ax, canvas, lines,
                x_label=x_label or "X",
                y_label=y_lbl,
                colors=colors,
            )
            self.tooltips[key] = tips

        if x_label:
            ax.set_xlabel(x_label, fontsize=11)
        ax.set_title(tab_name, fontsize=14, fontweight="bold", pad=15)
        ax.grid(True, linestyle="--", alpha=0.7)
        ax.set_facecolor("#fafafa")
        ax.legend(fontsize=10)

    # ---------------------------------------------------------- refresh --

    def refresh_single(self, tab_name, config):
        fig, ax    = self.figures[tab_name]
        canvas     = self.canvases[tab_name]
        self.plot_data(ax, tab_name, config, canvas)
        canvas.draw()

    def refresh_dual(self, tab_name, configs):
        fig    = self.figures[f"{tab_name}_dual"]
        canvas = self.canvases[f"{tab_name}_dual"]
        ax     = fig.axes[0]
        self.plot_dual_data(ax, tab_name, configs, canvas)
        canvas.draw()

    def refresh_all(self):
        for tab_name, config in self.tabs_config.items():
            self.refresh_single(tab_name, config)
        for tab_name, configs in self.dual_tabs_config.items():
            self.refresh_dual(tab_name, configs)
        messagebox.showinfo("Rafraîchissement", "Tous les graphiques ont été mis à jour.")


# ===========================================================================
#  DONNÉES EXEMPLES
# ===========================================================================

def create_sample_data():
    import numpy as np
    if not os.path.exists("data"):
        os.makedirs("data")
    x = np.linspace(0, 100, 100)
    simple_samples = {
        "ozone.csv":        ("Temps (s)", "O3 (ppb)",       lambda x: 50  + 20*np.sin(x/10)  + np.random.normal(0, 2,   len(x))),
        "pression.csv":     ("Temps (s)", "Pression (hPa)", lambda x: 1013 + 5*np.cos(x/15)  + np.random.normal(0, 0.5, len(x))),
        "o3_lamp.csv":      ("Temps (s)", "Puissance (W)",  lambda x: 100 + 10*np.sin(x/8)   + np.random.normal(0, 1,   len(x))),
        "lamp_setting.csv": ("Temps (s)", "Réglage (%)",    lambda x: 75  + 15*np.sin(x/5)   + np.random.normal(0, 1,   len(x))),
        "coef.csv":         ("Temps (s)", "Coefficient",    lambda x: 1.2 + 0.3*np.sin(x/10) + np.random.normal(0, 0.02,len(x))),
    }
    for filename, (xl, yl, func) in simple_samples.items():
        pd.DataFrame({xl: x, yl: func(x)}).to_csv(f"data/{filename}", index=False)

    pd.DataFrame({
        "Temps (s)":       x,
        "Débit A (L/min)": 5.0 + 0.5*np.sin(x/12) + np.random.normal(0, 0.1,  len(x)),
        "Débit B (L/min)": 4.5 + 0.6*np.cos(x/10) + np.random.normal(0, 0.12, len(x)),
    }).to_csv("data/flow.csv", index=False)

    pd.DataFrame({
        "Temps (s)":        x,
        "Intensité A (mA)": 250 + 30*np.cos(x/20) + np.random.normal(0, 3,   len(x)),
        "Intensité B (mA)": 240 + 25*np.sin(x/18) + np.random.normal(0, 2.5, len(x)),
    }).to_csv("data/intensite.csv", index=False)

    print("Fichiers CSV créés dans 'data/'")


# ===========================================================================
#  POINT D'ENTRÉE
# ===========================================================================

if __name__ == "__main__":
    create_sample_data()

    root = tk.Tk()
    LoginScreen(root, on_success=lambda r: GraphApp(r))
    root.mainloop()
