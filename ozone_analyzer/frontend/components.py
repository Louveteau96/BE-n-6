"""Reusable Tkinter components."""

import tkinter as tk


class Tooltip:
    """Lightweight hover-tooltip for any Tk widget."""

    def __init__(self, widget: tk.Widget, text: str):
        self.widget = widget #Tkinter button/label
        self.text = text     # message to display on hover


        self.tipwindow: tk.Toplevel | None = None
        widget.bind("<Enter>", self._show) # Tells Tkinter: "when the mouse enters this widget, call self._show"
        widget.bind("<Leave>", self._hide) # "when the mouse leaves, call self._hide"

    def _show(self, event=None) -> None:
        if self.tipwindow or not self.text: # if tooltip is already visible or text is empty
            return
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
        tw = tk.Toplevel(self.widget) #creates a second independent window alongside your main window
        tw.wm_overrideredirect(True)  # remove title bar and border
        tw.wm_geometry(f"+{x}+{y}")   # position it near the button
        tk.Label(
            tw, text=self.text, background="#ffffe0",
            relief="solid", borderwidth=1, padx=4, pady=2,
        ).pack()
        self.tipwindow = tw

    def _hide(self, event=None) -> None:
        if self.tipwindow is not None:
            self.tipwindow.destroy()
            self.tipwindow = None
