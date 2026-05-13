import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import pandas as pd
import os


class GraphApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Analyse de Données")
        self.root.geometry("1000x700")
        
        # Configuration du style
        style = ttk.Style()
        style.configure("TNotebook.Tab", padding=[20, 10], font=("Arial", 10))
        
        # Création du notebook (conteneur de tabs)
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Configuration des tabs avec leurs fichiers CSV associés
        self.tabs_config = {
            "Ozone": {"file": "data/ozone.csv", "color": "#2ecc71", "ylabel": "Concentration O₃ (ppb)"},
            "Pression": {"file": "data/pression.csv", "color": "#3498db", "ylabel": "Pression (hPa)"},
            "O3 Lamp": {"file": "data/o3_lamp.csv", "color": "#9b59b6", "ylabel": "Puissance (W)"},
            "Flow": {"file": "data/flow.csv", "color": "#e74c3c", "ylabel": "Débit (L/min)"},
            "Intensité": {"file": "data/intensite.csv", "color": "#f39c12", "ylabel": "Intensité (mA)"},
            "Lamp Setting": {"file": "data/lamp_setting.csv", "color": "#1abc9c", "ylabel": "Réglage (%)"},
            "Coef": {"file": "data/coef.csv", "color": "#e67e22", "ylabel": "Coefficient"}
        }
        
        # Dictionnaire pour stocker les références des figures
        self.figures = {}
        self.canvases = {}
        
        # Création des tabs
        self.create_tabs()
        
        # Bouton de rafraîchissement global
        refresh_frame = ttk.Frame(root)
        refresh_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Button(
            refresh_frame, 
            text="🔄 Rafraîchir tous les graphiques",
            command=self.refresh_all
        ).pack(side="right")
        
    def create_tabs(self):
        """Crée tous les onglets avec leurs graphiques."""
        for tab_name, config in self.tabs_config.items():
            # Création du frame pour chaque tab
            tab_frame = ttk.Frame(self.notebook)
            self.notebook.add(tab_frame, text=tab_name)
            
            # Création du graphique
            self.create_graph(tab_frame, tab_name, config)
    
    def create_graph(self, parent, tab_name, config):
        """Crée un graphique dans le frame parent."""
        # Frame pour le graphique
        graph_frame = ttk.Frame(parent)
        graph_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Création de la figure matplotlib
        fig, ax = plt.subplots(figsize=(10, 6), dpi=100)
        fig.patch.set_facecolor("#f0f0f0")
        
        # Stockage de la référence
        self.figures[tab_name] = (fig, ax)
        
        # Chargement et affichage des données
        self.plot_data(ax, tab_name, config)
        
        # Intégration dans Tkinter
        canvas = FigureCanvasTkAgg(fig, master=graph_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        
        self.canvases[tab_name] = canvas
        
        # Barre d'outils de navigation
        toolbar_frame = ttk.Frame(parent)
        toolbar_frame.pack(fill="x")
        toolbar = NavigationToolbar2Tk(canvas, toolbar_frame)
        toolbar.update()
        
        # Bouton de rafraîchissement individuel
        ttk.Button(
            toolbar_frame,
            text="🔄 Rafraîchir",
            command=lambda t=tab_name, c=config: self.refresh_single(t, c)
        ).pack(side="right", padx=5)
    
    def plot_data(self, ax, tab_name, config):
        """Charge les données CSV et trace le graphique."""
        ax.clear()
        
        file_path = config["file"]
        
        try:
            if os.path.exists(file_path):
                # Chargement du CSV
                df = pd.read_csv(file_path)
                
                # Détection automatique des colonnes
                if len(df.columns) >= 2:
                    x_col = df.columns[0]
                    y_col = df.columns[1]
                    
                    # Tracé des données
                    ax.plot(
                        df[x_col], 
                        df[y_col], 
                        color=config["color"],
                        linewidth=2,
                        marker="o",
                        markersize=4,
                        alpha=0.8
                    )
                    
                    # Remplissage sous la courbe
                    ax.fill_between(
                        df[x_col], 
                        df[y_col], 
                        alpha=0.2, 
                        color=config["color"]
                    )
                    
                    ax.set_xlabel(x_col, fontsize=11)
                    ax.set_ylabel(config["ylabel"], fontsize=11)
                else:
                    ax.text(
                        0.5, 0.5, 
                        "Format CSV invalide\n(minimum 2 colonnes requises)",
                        ha="center", va="center", fontsize=12,
                        transform=ax.transAxes
                    )
            else:
                # Affichage d'un message si le fichier n'existe pas
                ax.text(
                    0.5, 0.5,
                    f"Fichier non trouvé:\n{file_path}\n\nCréez le fichier CSV avec vos données.",
                    ha="center", va="center", fontsize=12,
                    transform=ax.transAxes, color="gray"
                )
                
        except Exception as e:
            ax.text(
                0.5, 0.5,
                f"Erreur de chargement:\n{str(e)}",
                ha="center", va="center", fontsize=12,
                transform=ax.transAxes, color="red"
            )
        
        # Style du graphique
        ax.set_title(tab_name, fontsize=14, fontweight="bold", pad=15)
        ax.grid(True, linestyle="--", alpha=0.7)
        ax.set_facecolor("#fafafa")
        
        # Ajustement automatique des marges
        plt.tight_layout()
    
    def refresh_single(self, tab_name, config):
        """Rafraîchit un seul graphique."""
        fig, ax = self.figures[tab_name]
        self.plot_data(ax, tab_name, config)
        self.canvases[tab_name].draw()
    
    def refresh_all(self):
        """Rafraîchit tous les graphiques."""
        for tab_name, config in self.tabs_config.items():
            self.refresh_single(tab_name, config)
        messagebox.showinfo("Rafraîchissement", "Tous les graphiques ont été mis à jour.")


def create_sample_data():
    """Crée des fichiers CSV d'exemple si le dossier data n'existe pas."""
    import numpy as np
    
    if not os.path.exists("data"):
        os.makedirs("data")
        
        # Données d'exemple pour chaque fichier
        samples = {
            "ozone.csv": ("Temps (s)", "O3 (ppb)", lambda x: 50 + 20*np.sin(x/10) + np.random.normal(0, 2, len(x))),
            "pression.csv": ("Temps (s)", "Pression (hPa)", lambda x: 1013 + 5*np.cos(x/15) + np.random.normal(0, 0.5, len(x))),
            "o3_lamp.csv": ("Temps (s)", "Puissance (W)", lambda x: 100 + 10*np.sin(x/8) + np.random.normal(0, 1, len(x))),
            "flow.csv": ("Temps (s)", "Débit (L/min)", lambda x: 5 + 0.5*np.sin(x/12) + np.random.normal(0, 0.1, len(x))),
            "intensite.csv": ("Temps (s)", "Intensité (mA)", lambda x: 250 + 30*np.cos(x/20) + np.random.normal(0, 3, len(x))),
            "lamp_setting.csv": ("Temps (s)", "Réglage (%)", lambda x: 75 + 15*np.sin(x/5) + np.random.normal(0, 1, len(x))),
            "coef.csv": ("Temps (s)", "Coefficient", lambda x: 1.2 + 0.3*np.sin(x/10) + np.random.normal(0, 0.02, len(x)))
        }
        
        x = np.linspace(0, 100, 100)
        
        for filename, (x_label, y_label, func) in samples.items():
            df = pd.DataFrame({x_label: x, y_label: func(x)})
            df.to_csv(f"data/{filename}", index=False)
        
        print("Fichiers CSV d'exemple créés dans le dossier 'data/'")


if __name__ == "__main__":
    # Création des données d'exemple (optionnel)
    create_sample_data()
    
    # Lancement de l'application
    root = tk.Tk()
    app = GraphApp(root)
    root.mainloop()
