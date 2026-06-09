"""Application configuration: serial settings, acquisition cadence, plot styling."""

from dataclasses import dataclass


@dataclass
class AppConfig:
    #PORT: str = "/dev/ttyUSB0"            # change to your port (e.g. "/dev/ttyUSB0")
    PORT: str = "COM1"
    BAUDRATE: int = 9600
    ID_ANALYSEUR: int = 49 
    ACQUISITION_INTERVAL: int = 5      # seconds between samples
    MAX_DATA_POINTS: int = 500         # rolling window length
    QUEUE_MAXSIZE: int = 200


PLOT_CONFIGS = {
    "Ozone": {
        "col": "o3",
        "color": "#2ecc71",
        "ylabel": "Concentration O₃ (ppb)",
        "title": "Ozone",
    },
    "Cell": {
        "dual": True,
        "cols": ["cellA", "cellB"],
        "colors": ["#e67e22", "#e74c3c"],
        "title": "Cellules",
    },
    "Pression": {
        "col": "pression",
        "color": "#3498db",
        "ylabel": "Pression (hPa)",
        "title": "Pression",
    },
    "Flow": {
        "dual": True,
        "cols": ["flowA", "flowB"],
        "colors": ["#e74c3c", "#3498db"], 
        "title": "Débit",
    },
    "O3 Lamp": {
        "col": "o3lamp",
        "color": "#9b59b6",
        "ylabel": "Puissance Lampe (W)",
        "title": "O3 Lamp",
    },
    "Temperatures": {
        "dual": True,
        "cols": ["lampT", "benchT"],
        "colors": ["#f39c12", "#1abc9c"],
        "title": "Températures (°C)",
    },
}