import customtkinter as ctk
from tkinter import Canvas
from PIL import Image

from app.core.constants import (
    COLOR_BG,
    COLOR_CARD,
    COLOR_CARD_HOVER,
    COLOR_BORDER,
    COLOR_TEXT,
    COLOR_TEXT_DIM,
    COLOR_BLUE,
    COLOR_BLUE_DIM,
    COLOR_PURPLE,
    COLOR_PURPLE_DIM,
    COLOR_GREEN,
    COLOR_GREEN_DIM,
    COLOR_RED,
    COLOR_RED_DIM,
    ICONS_DIR,
)

_icon_cache = {}


def icon(name, size=20):
    key = (name, size)
    if key in _icon_cache:
        return _icon_cache[key]

    path = ICONS_DIR / f"{name}.png"
    if not path.exists():
        _icon_cache[key] = None
        return None

    try:
        img = Image.open(path).convert("RGBA")
        alpha = img.getchannel("A")
        white_img = Image.new("RGBA", img.size, (255, 255, 255, 255))
        white_img.putalpha(alpha)
        ctk_img = ctk.CTkImage(light_image=white_img, dark_image=white_img, size=(size, size))
        _icon_cache[key] = ctk_img
        return ctk_img
    except Exception:
        _icon_cache[key] = None
        return None


class CircularProgress(Canvas):
    def __init__(self, master, size=84, thickness=8, **kwargs):
        super().__init__(master, width=size, height=size, bg=COLOR_CARD, highlightthickness=0, **kwargs)
        self.size = size
        self.thickness = thickness
        self.percent = 0
        self._draw()

    def _draw(self):
        self.delete("all")
        pad = self.thickness
        x0, y0 = pad, pad
        x1, y1 = self.size - pad, self.size - pad

        self.create_oval(x0, y0, x1, y1, outline=COLOR_BORDER, width=self.thickness)

        if self.percent > 0:
            extent = -360 * (self.percent / 100)
            self.create_arc(x0, y0, x1, y1, start=90, extent=extent, style="arc", outline=COLOR_BLUE, width=self.thickness)

        self.create_text(self.size / 2, self.size / 2, text=f"{self.percent}%", fill=COLOR_TEXT, font=("Arial", 15, "bold"))

    def set_percent(self, value):
        self.percent = max(0, min(100, int(value)))
        self._draw()


class ActionCard(ctk.CTkFrame):
    def __init__(self, master, icon_name, title, subtitle, accent, accent_bg, command=None, **kwargs):
        super().__init__(master, fg_color=accent_bg, corner_radius=12, border_width=1, border_color=accent, cursor="hand2", **kwargs)
        self.command = command

        icon_box = ctk.CTkFrame(self, width=38, height=38, corner_radius=9, fg_color=accent)
        icon_box.grid(row=0, column=0, rowspan=2, padx=14, pady=12)
        icon_box.grid_propagate(False)
        ctk.CTkLabel(icon_box, image=icon(icon_name, 18), text="").place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(self, text=title, font=("Arial", 14, "bold"), text_color=COLOR_TEXT, anchor="w").grid(row=0, column=1, sticky="w", pady=(12, 0), padx=(0, 14))
        ctk.CTkLabel(self, text=subtitle, font=("Arial", 11), text_color=COLOR_TEXT_DIM, anchor="w").grid(row=1, column=1, sticky="w", pady=(0, 12), padx=(0, 14))

        for widget in (self, icon_box):
            widget.bind("<Button-1>", self._on_click)
        for child in self.winfo_children():
            child.bind("<Button-1>", self._on_click)

    def _on_click(self, _event=None):
        if self.command:
            self.command()

    def set_enabled(self, enabled: bool):
        self.configure(cursor="hand2" if enabled else "arrow")
