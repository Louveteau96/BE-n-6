"""Parse raw serial frames ('lrec 1 1 ...') into typed dicts ready for pandas."""

from datetime import datetime
from typing import Optional


def process_raw_data(raw_data: str) -> Optional[dict]:  # return a dict or None
    """Clean and structure raw serial data.

    Returns None on parse failure (caller should skip the row).
    """
    try:
        params = raw_data.split()
        valeurs = params[3:]                # drop "lrec 1 1"
        if len(valeurs) > 4:
            valeurs.pop(4)                  # drop hio3 column

        return {                            # return a dictionary each time it is called
            "timestamp": datetime.now(),    # real datetime, used as plot x-axis
            "heure": valeurs[0],
            "date": valeurs[1],
            "flag" : valeurs[2],
            "o3": float(valeurs[3]),
            "cellA" : float(valeurs[4]),
            "cellB" : float(valeurs[5]),
            "benchT" : float(valeurs[6]),
            "lampT": float(valeurs[7]),
            "o3lamp": float(valeurs[8]),
            "flowA": float(valeurs[9]),
            "flowB": float(valeurs[10]),
            "pression": float(valeurs[11]),
            
            
        }
    except Exception as e:
        print(f"Data processing error: {e} | raw={raw_data!r}") # !r show special character, like \n
        return None

def main():
    rec1 = "lrec 1 1 09:53 03-02-26 0C105004 0.000 0.000 0 7 20.2 46.5 63.6 0.754 0.721 747.0"
    
    processed = process_raw_data(rec1)
    print(processed)
    
    
    
    