# Ozone Analyzer

Real-time GUI for a serial-connected ozone analyzer. Data acquisition runs
on a background thread; the GUI polls a thread-safe queue from Tk's own
event loop.

## Project layout

```
ozone_analyzer/
├── main.py                    # Entry point
├── config.py                  # Constants & plot styling
├── requirements.txt
├── backend/
│   ├── serial_handler.py      # Serial I/O + acquisition thread
│   └── data_processor.py      # Parse raw frames -> typed dicts
├── frontend/
│   ├── gui.py                 # Tk GraphApp (notebook + polling)
│   ├── plots.py               # Matplotlib renderers
│   └── components.py          # Reusable widgets (Tooltip)
└── utils/
    └── helpers.py
```

## Setup

```bash
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Edit `config.py` to set the correct `PORT` for your machine
(e.g. `"COM3"` on Windows, `"/dev/ttyUSB0"` on Linux).

## Run

```bash
python main.py               # real hardware
python main.py --simulate    # mock backend - no hardware required
```

In simulation mode, `backend/mock_serial_handler.py` produces realistic
`lrec 1 1 …` frames every second (sinusoidal O₃ trend + noise on all
channels), exercising the full pipeline: queue → parser → dataframe → plots.
The window title is tagged `[SIMULATION]` so you can tell at a glance.

## What was fixed from the original draft

1. **Missing matplotlib imports in `gui.py`** — `plt`, `FigureCanvasTkAgg`,
   `NavigationToolbar2Tk` are now imported where they are used.
2. **`tk.time.sleep(0.2)`** — removed entirely. There is no longer a
   consumer thread; the GUI polls the queue via `root.after()`.
3. **Thread-safety on `self.df`** — all dataframe mutations now happen on
   the Tk main thread, so there is no race between worker and renderer.
4. **`queue.empty()` busy-poll** — replaced with `get_nowait()` + `Empty`.
5. **Acquisition started before GUI** — order swapped, plus a
   `WM_DELETE_WINDOW` handler ensures clean shutdown of the serial thread
   and port.
6. **Unbounded `read_response()` sleep** — now uses `stop_event.wait()`
   so shutdown is prompt.
7. **`put()` could block on full queue** — switched to a drop-oldest
   policy via `put_nowait()` so the producer never stalls.
8. **Plots used `df.index`** — now use the real `timestamp` column with
   an `HH:MM:SS` formatter.
