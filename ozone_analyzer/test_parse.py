import re

import re
from datetime import datetime
from typing import Optional


def parse_labeled_frame(raw: str) -> Optional[dict]:

    def get(label) -> Optional[float]:
        try:
            m = re.search(rf"{label}\s+([\d.]+)", raw)
            return float(m.group(1)) if m else None
        except Exception as e:
            print(f"Error parsing '{label}': {e} | raw={raw!r}")
            return None

    try:
        return {
            "timestamp": datetime.now(),
            "o3":        get("o3"),
            "hio3":      get("hio3"),
            "cellA":     get("cellai"),
            "cellB":     get("cellbi"),
            "benchT":    get("bncht"),
            "lampT":     get("lmpt"),
            "o3lamp":    get("o3lt"),
            "flowA":     get("flowa"),
            "flowB":     get("flowb"),
            "pression":  get("pres"),
        }
    except Exception as e:
        print(f"Data processing error: {e} | raw={raw!r}")
        return None
    
def main():
    rec1 = "14:14 05-26-26 flags 0C100000 o3 7.469 hio3 0.000 cellai 115685 cellbi 117893 bncht 31.6 lmpt 52.8 o3lt 67.3 flowa 0.751 flowb 0.717 pres 751.8"
    
    data = parse_labeled_frame(rec1)
    print(data)
    
main()