"""Serial communication with the ozone analyzer.

Runs the acquisition loop on a background thread and pushes raw response
strings into a thread-safe Queue. The GUI drains the queue on its own
event loop (see frontend/gui.py).
"""

import re
import serial
from queue import Queue, Full
from threading import Event, Thread


class SerialHandler:
    def __init__(self, data_queue: Queue):
        self.data_queue = data_queue
        self.ser: serial.Serial | None = None
        self.stop_event = Event()
        self.thread: Thread | None = None

    # ---- Connection -----------------------------------------------------
    def connect(self, port: str, baudrate: int, device_id: int) -> bool:
        try:
            self.ser = serial.Serial(port, baudrate=baudrate, timeout=1)
            if not self._set_remote_mode(device_id):
                self.ser.close()
                return False
            return True
        except Exception as e:
            print(f"Connection error: {e}")
            return False

    def _set_remote_mode(self, device_id: int) -> bool:
        self._send_command("set mode remote", device_id)
        for _ in range(12):
            if self.stop_event.is_set(): # if user close the window
                return False
            if self.read_response().strip() == "set mode remote ok": # success
                print("✅ Mode remote activated")
                return True
            if self.stop_event.wait(timeout=0.3): 
                return False
        print("⚠️  Remote mode confirmation never received.")
        return False          # ← exhausted all 12 attempts

    # ---- Low-level I/O --------------------------------------------------
    def _send_command(self, cmd: str, device_id: int) -> None:
        commande = f"{device_id}{cmd}\r\n"
        self.ser.write(commande.encode('utf-8'))

    def read_response(self) -> str:
        """Poll the serial port until a non-empty line arrives or we are stopped.

        Uses stop_event.wait() instead of time.sleep() so shutdown is prompt.
        """
        reponse = ""
        for _ in range(80): # 8 seconds
            if self.stop_event.wait(timeout=0.1):
                break
            try:
                reponse = self.ser.readline().decode('utf-8').strip()
                print(f"Response received: {reponse}")
            except Exception:
                break
            if reponse: # string is true if non empty
                break
        return reponse

    # ---- Acquisition loop ----------------------------------------------
    def start_acquisition(
        self, port: str, baudrate: int, id_analyseur: int, interval: int
    ) -> bool:
        device_id = chr(id_analyseur + 128)
        
        if not self.connect(port, baudrate, device_id):
            return False

        self.stop_event.clear()
        self.thread = Thread(
            target=self._acquisition_loop,
            args=(device_id, interval),
            daemon=True,
        )
        self.thread.start()
        return True

    def _acquisition_loop(self, device_id, interval: int) -> None:
        while not self.stop_event.is_set():
            try:
                self._send_command("lrec 1 1", device_id)
                print("send lrec 1 1s")
                raw_data = self.read_response()

                for _ in range(6):
                    if self.stop_event.is_set():
                        return
                    if re.match(r"^lrec 1 1\b", raw_data):
                        break
                    raw_data = self.read_response()

                if re.match(r"^lrec 1 1\b", raw_data):
                    self._enqueue(raw_data)
                else:
                    print(f"⚠️  Unrecognized response, dropping: {raw_data!r}")

            except Exception as e:
                print(f"Acquisition error: {e}")

            # Interruptible sleep
            if self.stop_event.wait(timeout=interval):
                break

    def _enqueue(self, raw_data: str) -> None:
        """Put with drop-oldest policy so the producer never blocks."""
        try:
            self.data_queue.put_nowait(raw_data)
        except Full:
            try:
                self.data_queue.get_nowait()
            except Exception:
                pass
            try:
                self.data_queue.put_nowait(raw_data)
            except Full:
                pass

    # ---- Shutdown -------------------------------------------------------
    def stop(self) -> None:
        self.stop_event.set()
        if self.thread is not None:
            self.thread.join(timeout=2)
            self.thread = None
        if self.ser is not None and self.ser.is_open:
            try:
                self.ser.close()
            except Exception:
                pass


