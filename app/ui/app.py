import os
import sys
import threading
from pathlib import Path
from queue import Queue
from concurrent.futures import ThreadPoolExecutor

import customtkinter as ctk
from tkinter import filedialog

from app.core.constants import (
    COLOR_BG,
    COLOR_SIDEBAR,
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
    PRESETS,
    SUPPORTED_SOURCE,
    SUPPORTED_TARGET,
    ICONS_DIR,
)
from app.core.converter import FileConverter
from app.core.word_session import WORD_COM_AVAILABLE, WordSession
from app.ui.widgets import ActionCard, CircularProgress, icon

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class ConverterApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Universal File Converter")
        self.geometry("1320x880")
        self.configure(fg_color=COLOR_BG)
        self.minsize(1100, 760)

        self.input_folder = None
        self.output_folder = None
        self.converter = FileConverter(log_callback=None)

        self.cancel_flag = threading.Event()
        self.log_queue = Queue()
        self.log_entries = []

        self.total_files = 0
        self.done_files = 0
        self.error_files = 0
        self.skipped_files = 0
        self.counter_lock = threading.Lock()

        self.safe_mode = ctk.BooleanVar(value=True)
        self.source_ext = ctk.StringVar(value="doc/docx")
        self.target_ext = ctk.StringVar(value="pdf")
        self.source_ext_display = ctk.StringVar(value="DOC/DOCX")
        self.target_ext_display = ctk.StringVar(value="PDF")
        self.preset_var = ctk.StringVar(value="DOC/DOCX → PDF")

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.build_sidebar()
        self.build_main_area()
        self.show_converter_page()

        self.process_log_queue()

    def build_sidebar(self):
        sidebar = ctk.CTkFrame(self, width=270, fg_color=COLOR_SIDEBAR, corner_radius=0)
        sidebar.grid(row=0, column=0, sticky="nsw")
        sidebar.grid_propagate(False)
        sidebar.grid_rowconfigure(5, weight=1)

        logo_box = ctk.CTkFrame(sidebar, width=64, height=64, corner_radius=16, fg_color=COLOR_BLUE)
        logo_box.grid(row=0, column=0, pady=(36, 12), padx=0)
        logo_box.grid_propagate(False)
        ctk.CTkLabel(logo_box, image=icon("arrow-left-right", 28), text="").place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(sidebar, text="Universal", font=("Arial", 22, "bold"), text_color=COLOR_TEXT, anchor="center").grid(row=1, column=0, sticky="ew", padx=24)
        ctk.CTkLabel(sidebar, text="File Converter V1.0.0", font=("Arial", 14, "bold"), text_color=COLOR_BLUE, anchor="center").grid(row=2, column=0, sticky="ew", padx=24, pady=(0, 28))

        nav_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        nav_frame.grid(row=3, column=0, sticky="new", padx=16)
        nav_frame.grid_columnconfigure(0, weight=1)

        self.nav_buttons = {}
        nav_items = [
            ("converter", "arrow-left-right", "Converter"),
            ("history", "clock-history", "History"),
            ("settings", "gear", "Settings"),
        ]
        for i, (key, icon_name, label) in enumerate(nav_items):
            item = ctk.CTkFrame(nav_frame, fg_color="transparent", corner_radius=10, height=44, cursor="hand2")
            item.grid(row=i, column=0, sticky="ew", pady=4)
            item.grid_propagate(False)
            item.grid_columnconfigure(1, weight=1)

            icon_label = ctk.CTkLabel(item, image=icon(icon_name, 18), text="", width=26)
            icon_label.grid(row=0, column=0, padx=(14, 8), pady=10)

            text_label = ctk.CTkLabel(item, text=label, font=("Arial", 14, "bold"), text_color=COLOR_TEXT, anchor="w")
            text_label.grid(row=0, column=1, sticky="w", pady=10)

            for widget in (item, icon_label, text_label):
                widget.bind("<Button-1>", lambda _e, k=key: self.switch_page(k))

            self.nav_buttons[key] = (item, icon_label, text_label)

        safe_card = ctk.CTkFrame(sidebar, fg_color=COLOR_CARD, corner_radius=12, border_width=1, border_color=COLOR_BORDER)
        safe_card.grid(row=6, column=0, sticky="sew", padx=16, pady=20)
        safe_card.grid_columnconfigure(1, weight=1)

        shield_box = ctk.CTkFrame(safe_card, width=34, height=34, corner_radius=8, fg_color=COLOR_GREEN_DIM)
        shield_box.grid(row=0, column=0, rowspan=2, padx=12, pady=12)
        shield_box.grid_propagate(False)
        ctk.CTkLabel(shield_box, image=icon("shield-check", 16), text="").place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(safe_card, text="Safe Mode", font=("Arial", 13, "bold"), text_color=COLOR_TEXT, anchor="w").grid(row=0, column=1, sticky="w", pady=(10, 0))
        ctk.CTkLabel(safe_card, text="Reduces speed but\nincreases stability.", font=("Arial", 10), text_color=COLOR_TEXT_DIM, justify="left", anchor="w").grid(row=1, column=1, sticky="w", pady=(0, 10))

        switch = ctk.CTkSwitch(safe_card, text="", variable=self.safe_mode, width=40, progress_color=COLOR_GREEN)
        switch.grid(row=0, column=2, rowspan=2, padx=12)

    def switch_page(self, key):
        for k, (item, icon_label, text_label) in self.nav_buttons.items():
            if k == key:
                item.configure(fg_color=COLOR_BLUE)
                text_label.configure(text_color="#FFFFFF")
            else:
                item.configure(fg_color="transparent")
                text_label.configure(text_color=COLOR_TEXT)

        self.converter_page.grid_remove()
        self.placeholder_page.grid_remove()

        if key == "converter":
            self.converter_page.grid(row=0, column=0, sticky="nsew")
        else:
            title = "History" if key == "history" else "Settings"
            self.placeholder_title.configure(text=title)
            self.placeholder_page.grid(row=0, column=0, sticky="nsew")

    def show_converter_page(self):
        self.switch_page("converter")

    def build_main_area(self):
        container = ctk.CTkFrame(self, fg_color=COLOR_BG, corner_radius=0)
        container.grid(row=0, column=1, sticky="nsew")
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.converter_page = ctk.CTkFrame(container, fg_color="transparent")
        self.converter_page.grid_columnconfigure(0, weight=1)
        self.converter_page.grid_rowconfigure(0, weight=0)
        self.converter_page.grid_rowconfigure(1, weight=0)
        self.converter_page.grid_rowconfigure(2, weight=0)
        self.converter_page.grid_rowconfigure(3, weight=0)
        self.converter_page.grid_rowconfigure(4, weight=1)
        self.converter_page.grid(row=0, column=0, sticky="nsew")

        self.build_header(self.converter_page)
        self.build_format_row(self.converter_page)
        self.build_action_row(self.converter_page)
        self.build_stats_row(self.converter_page)
        self.build_log_panel(self.converter_page)
        ctk.CTkLabel(self.converter_page, text="Created by Andromeda.", font=("Arial", 12), text_color=COLOR_TEXT_DIM, anchor="center").grid(row=5, column=0, sticky="ew", padx=32, pady=(0, 24))

        self.placeholder_page = ctk.CTkFrame(container, fg_color="transparent")
        self.placeholder_page.grid_columnconfigure(0, weight=1)
        self.placeholder_page.grid_rowconfigure(0, weight=1)
        inner = ctk.CTkFrame(self.placeholder_page, fg_color="transparent")
        inner.grid(row=0, column=0)
        ctk.CTkLabel(inner, image=icon("info-circle", 40), text="").pack(pady=(0, 10))
        self.placeholder_title = ctk.CTkLabel(inner, text="", font=("Arial", 20, "bold"), text_color=COLOR_TEXT)
        self.placeholder_title.pack()
        ctk.CTkLabel(inner, text="ეს სექცია მალე დაემატება.", font=("Arial", 13), text_color=COLOR_TEXT).pack(pady=(4, 0))

    def build_header(self, parent):
        header = ctk.CTkFrame(parent, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=32, pady=(32, 18))
        header.grid_columnconfigure(0, weight=1)
        header.grid_columnconfigure(1, weight=0)

        ctk.CTkLabel(header, text="Convert Files Easily", font=("Arial", 32, "bold"), text_color=COLOR_TEXT, anchor="w").grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(header, text="Fast. Reliable. Universal.", font=("Arial", 14), text_color=COLOR_TEXT_DIM, anchor="w").grid(row=1, column=0, sticky="w", pady=(4, 0))

        icons_row = ctk.CTkFrame(header, fg_color="transparent")
        icons_row.grid(row=0, column=1, rowspan=2, sticky="e")
        icons_row.grid_columnconfigure((0, 1, 2), weight=1)
        glyphs = [("file-earmark-text", COLOR_BLUE, COLOR_BLUE_DIM), ("arrow-left-right", COLOR_TEXT_DIM, COLOR_CARD), ("file-earmark-pdf", COLOR_PURPLE, COLOR_PURPLE_DIM)]
        for i, (name, fg, bg) in enumerate(glyphs):
            box = ctk.CTkFrame(icons_row, width=46, height=46, corner_radius=12, fg_color=bg)
            box.grid(row=0, column=i, padx=6)
            box.grid_propagate(False)
            ctk.CTkLabel(box, image=icon(name, 20), text="").place(relx=0.5, rely=0.5, anchor="center")

    @staticmethod
    def _display_ext(value):
        mapping = {
            "doc": "DOC",
            "docx": "DOCX",
            "doc/docx": "DOC/DOCX",
            "pdf": "PDF",
            "txt": "TXT",
        }
        return mapping.get(str(value).strip().lower(), str(value).upper())

    @staticmethod
    def _normalize_ext(value):
        mapping = {
            "doc": "doc",
            "docx": "docx",
            "doc/docx": "doc/docx",
            "pdf": "pdf",
            "txt": "txt",
            "DOC": "doc",
            "DOCX": "docx",
            "DOC/DOCX": "doc/docx",
            "PDF": "pdf",
            "TXT": "txt",
        }
        return mapping.get(str(value).strip(), str(value).strip().lower())

    def _set_format_value(self, variable, display_var, value):
        normalized = self._normalize_ext(value)
        variable.set(normalized)
        display_var.set(self._display_ext(normalized))
        if variable is self.source_ext:
            self.on_format_changed()

    def build_format_row(self, parent):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.grid(row=1, column=0, sticky="ew", padx=32, pady=8)
        row.grid_columnconfigure((0, 1, 2), weight=1)

        from_card = self.build_format_card(row, "file-earmark-text", COLOR_BLUE, COLOR_BLUE_DIM, "FROM", "Select Source Format", "Choose input file type", self.source_ext, self.source_ext_display, SUPPORTED_SOURCE)
        from_card.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        to_card = self.build_format_card(row, "file-earmark-pdf", COLOR_PURPLE, COLOR_PURPLE_DIM, "TO", "Select Target Format", "Choose output file type", self.target_ext, self.target_ext_display, SUPPORTED_TARGET)
        to_card.grid(row=0, column=1, sticky="ew", padx=8)

        preset_card = self.build_preset_card(row)
        preset_card.grid(row=0, column=2, sticky="ew", padx=(8, 0))

    def _bind_click_to_menu(self, widgets, menu):
        def open_menu(_event=None):
            menu._clicked()

        for widget in widgets:
            if widget is not None:
                widget.bind("<Button-1>", open_menu)

    def build_format_card(self, parent, icon_name, accent, accent_bg, eyebrow, title, subtitle, variable, display_var, values):
        card = ctk.CTkFrame(parent, fg_color=COLOR_CARD, corner_radius=12, border_width=1, border_color=COLOR_BORDER)
        card.grid_columnconfigure((0, 1), weight=1)

        eyebrow_label = ctk.CTkLabel(card, text=eyebrow, font=("Arial", 10, "bold"), text_color=COLOR_TEXT_DIM, anchor="center")
        eyebrow_label.grid(row=0, column=0, columnspan=2, sticky="ew", padx=16, pady=(12, 2))

        icon_box = ctk.CTkFrame(card, width=38, height=38, corner_radius=9, fg_color=accent_bg)
        icon_box.grid(row=1, column=0, columnspan=2, padx=0, pady=(0, 10))
        icon_box.grid_propagate(False)
        ctk.CTkLabel(icon_box, image=icon(icon_name, 18), text="").place(relx=0.5, rely=0.5, anchor="center")

        menu = ctk.CTkOptionMenu(card, values=values, variable=display_var, width=170, fg_color=COLOR_CARD, button_color=COLOR_CARD, button_hover_color=COLOR_CARD_HOVER, text_color=COLOR_TEXT, font=("Arial", 14, "bold"), dropdown_fg_color=COLOR_CARD, dropdown_hover_color=COLOR_CARD_HOVER, anchor="center", command=lambda v: self._set_format_value(variable, display_var, v))
        menu.grid(row=2, column=0, columnspan=2, sticky="ew", padx=(40, 16))

        subtitle_label = ctk.CTkLabel(card, text=subtitle, font=("Arial", 11), text_color=COLOR_TEXT_DIM, anchor="center")
        subtitle_label.grid(row=3, column=0, columnspan=2, sticky="ew", padx=16, pady=(6, 12))

        self._bind_click_to_menu([card, icon_box, eyebrow_label, subtitle_label], menu)
        return card

    def build_preset_card(self, parent):
        card = ctk.CTkFrame(parent, fg_color=COLOR_CARD, corner_radius=12, border_width=1, border_color=COLOR_BORDER)
        card.grid_columnconfigure((0, 1), weight=1)

        preset_label = ctk.CTkLabel(card, text="PRESET", font=("Arial", 10, "bold"), text_color=COLOR_TEXT_DIM, anchor="center")
        preset_label.grid(row=0, column=0, columnspan=2, sticky="ew", padx=16, pady=(12, 2))

        icon_box = ctk.CTkFrame(card, width=38, height=38, corner_radius=9, fg_color=COLOR_GREEN_DIM)
        icon_box.grid(row=1, column=0, columnspan=2, padx=0, pady=(0, 10))
        icon_box.grid_propagate(False)
        ctk.CTkLabel(icon_box, image=icon("file-earmark-text", 18), text="").place(relx=0.5, rely=0.5, anchor="center")

        menu = ctk.CTkOptionMenu(card, values=list(PRESETS.keys()), variable=self.preset_var, width=190, fg_color=COLOR_CARD, button_color=COLOR_CARD, button_hover_color=COLOR_CARD_HOVER, text_color=COLOR_TEXT, font=("Arial", 14, "bold"), dropdown_fg_color=COLOR_CARD, dropdown_hover_color=COLOR_CARD_HOVER, anchor="center", command=self.on_preset_selected)
        menu.grid(row=2, column=0, columnspan=2, sticky="ew", padx=(40, 16))

        self.preset_subtitle = ctk.CTkLabel(card, text=PRESETS[self.preset_var.get()][2], font=("Arial", 11), text_color=COLOR_TEXT_DIM, anchor="center")
        self.preset_subtitle.grid(row=3, column=0, columnspan=2, sticky="ew", padx=16, pady=(6, 12))

        self._bind_click_to_menu([card, icon_box, preset_label, self.preset_subtitle], menu)
        return card

    def on_preset_selected(self, name):
        src, tgt, desc = PRESETS[name]
        self.source_ext.set(src)
        self.source_ext_display.set(self._display_ext(src))
        self.target_ext.set(tgt)
        self.target_ext_display.set(self._display_ext(tgt))
        self.preset_subtitle.configure(text=desc)

    def on_format_changed(self):
        if self.source_ext.get() == "doc/docx":
            self.target_ext.set("pdf")
            self.target_ext_display.set("PDF")

    def build_action_row(self, parent):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.grid(row=2, column=0, sticky="ew", padx=32, pady=8)
        row.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="actions")

        ActionCard(row, "folder", "Select Input Folder", "Choose the folder to scan", COLOR_BLUE, COLOR_CARD, command=self.select_input).grid(row=0, column=0, sticky="ew", padx=(0, 8))
        ActionCard(row, "folder2-open", "Select Output Folder", "Choose where to save files", COLOR_BLUE, COLOR_CARD, command=self.select_output).grid(row=0, column=1, sticky="ew", padx=8)
        self.start_card = ActionCard(row, "play-fill", "Start Conversion", "Begin the conversion process", COLOR_GREEN, COLOR_GREEN_DIM, command=self.start_conversion)
        self.start_card.grid(row=0, column=2, sticky="ew", padx=8)
        ActionCard(row, "stop-fill", "Cancel", "Stop conversion", COLOR_RED, COLOR_RED_DIM, command=self.cancel_conversion).grid(row=0, column=3, sticky="ew", padx=(8, 0))

    def build_stats_row(self, parent):
        row = ctk.CTkFrame(parent, fg_color=COLOR_CARD, corner_radius=12, border_width=1, border_color=COLOR_BORDER)
        row.grid(row=3, column=0, sticky="ew", padx=32, pady=14)
        row.grid_columnconfigure((0, 1, 2), weight=1)
        row.grid_columnconfigure(3, weight=2)

        self.total_stat = self.build_inline_stat(row, "file-earmark-text", COLOR_PURPLE, COLOR_PURPLE_DIM, "Total Files")
        self.total_stat.grid(row=0, column=0, sticky="w", padx=24, pady=18)

        self.converted_stat = self.build_inline_stat(row, "check-circle", COLOR_GREEN, COLOR_GREEN_DIM, "Converted")
        self.converted_stat.grid(row=0, column=1, sticky="w", padx=24, pady=18)

        self.error_stat = self.build_inline_stat(row, "x-circle", COLOR_RED, COLOR_RED_DIM, "Errors")
        self.error_stat.grid(row=0, column=2, sticky="w", padx=24, pady=18)

        progress_box = ctk.CTkFrame(row, fg_color="transparent")
        progress_box.grid(row=0, column=3, sticky="e", padx=24, pady=14)

        self.progress_ring = CircularProgress(progress_box, size=84)
        self.progress_ring.grid(row=0, column=0, rowspan=2, padx=(0, 16))

        ctk.CTkLabel(progress_box, text="Progress", font=("Arial", 13, "bold"), text_color=COLOR_TEXT, anchor="w").grid(row=0, column=1, sticky="w")
        self.progress_caption = ctk.CTkLabel(progress_box, text="Please select folders and start conversion", font=("Arial", 11), text_color=COLOR_TEXT_DIM, anchor="w", wraplength=220, justify="left")
        self.progress_caption.grid(row=1, column=1, sticky="w")

    def build_inline_stat(self, parent, icon_name, color, color_bg, label):
        box = ctk.CTkFrame(parent, fg_color="transparent")
        icon_box = ctk.CTkFrame(box, width=40, height=40, corner_radius=10, fg_color=color_bg)
        icon_box.grid(row=0, column=0, rowspan=2, padx=(0, 10))
        icon_box.grid_propagate(False)
        ctk.CTkLabel(icon_box, image=icon(icon_name, 18), text="").place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(box, text=label, font=("Arial", 12), text_color=COLOR_TEXT_DIM, anchor="w").grid(row=0, column=1, sticky="w")
        value_label = ctk.CTkLabel(box, text="0", font=("Arial", 20, "bold"), text_color=color, anchor="w")
        value_label.grid(row=1, column=1, sticky="w")
        box.value_label = value_label
        return box

    def build_log_panel(self, parent):
        panel = ctk.CTkFrame(parent, fg_color=COLOR_CARD, corner_radius=12, border_width=1, border_color=COLOR_BORDER)
        panel.grid(row=4, column=0, sticky="nsew", padx=32, pady=(0, 32))
        parent.grid_rowconfigure(4, weight=1)
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(panel, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=18, pady=14)
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(header, image=icon("list", 16), text=" Conversion Log", compound="left", font=("Arial", 14, "bold"), text_color=COLOR_TEXT, anchor="w").grid(row=0, column=0, sticky="w")
        ctk.CTkButton(header, image=icon("trash", 14), text=" Clear Log", compound="left", width=110, height=30, fg_color=COLOR_BG, hover_color=COLOR_CARD_HOVER, text_color=COLOR_TEXT, font=("Arial", 11), corner_radius=8, command=self.clear_log).grid(row=0, column=1, sticky="e")

        self.log_box = ctk.CTkTextbox(panel, fg_color=COLOR_BG, text_color=COLOR_TEXT, corner_radius=10, font=("Consolas", 12), border_width=1, border_color=COLOR_BORDER, height=320)
        self.log_box.grid(row=1, column=0, sticky="nsew", padx=18, pady=(0, 12))
        self.log_box.configure(state="disabled")

        self.log_empty_state = ctk.CTkFrame(panel, fg_color="transparent")
        self.log_empty_state.grid(row=1, column=0, sticky="nsew", padx=18, pady=(0, 12))
        self.log_empty_state.grid_columnconfigure(0, weight=1)
        self.log_empty_state.grid_rowconfigure(0, weight=1)

        empty_inner = ctk.CTkFrame(self.log_empty_state, fg_color="transparent")
        empty_inner.place(relx=0.5, rely=0.5, anchor="center")
        ctk.CTkLabel(empty_inner, image=icon("file-earmark-text", 38), text="").pack(pady=(0, 8))
        ctk.CTkLabel(empty_inner, text="No logs yet\nLogs will appear here during conversion", font=("Arial", 13), text_color=COLOR_TEXT, justify="center", anchor="center").pack()

        self.show_empty_log_state()

    def show_empty_log_state(self):
        self.log_empty_state.grid()
        self.log_box.configure(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.configure(state="disabled")

    def clear_log(self):
        self.log_entries = []
        self.show_empty_log_state()

    def log(self, text):
        self.log_queue.put(text)

    def process_log_queue(self):
        new_entries = False
        while not self.log_queue.empty():
            msg = self.log_queue.get()
            self.log_entries.append(msg)
            new_entries = True

        if new_entries:
            self.log_empty_state.grid_remove()
            self.log_box.configure(state="normal")
            self.log_box.delete("1.0", "end")
            for entry in self.log_entries:
                self.log_box.insert("end", entry + "\n")
            self.log_box.see("end")
            self.log_box.configure(state="disabled")

        self.after(100, self.process_log_queue)

    def select_input(self):
        folder = filedialog.askdirectory()
        if folder:
            self.input_folder = Path(folder)
            self.log(f"Input: {folder}")

    def select_output(self):
        folder = filedialog.askdirectory()
        if folder:
            self.output_folder = Path(folder)
            self.log(f"Output: {folder}")

    def convert_single(self, src: Path):
        if self.cancel_flag.is_set():
            return

        rel = src.relative_to(self.input_folder)
        dst = self.output_folder / rel.with_suffix(f".{self.target_ext.get()}")
        dst.parent.mkdir(parents=True, exist_ok=True)

        if dst.exists():
            self.log(f"გამოტოვებული (უკვე არსებობს): {dst.name}")
            self.file_done(skipped=True)
            return

        try:
            self.converter.convert_file(src, dst, self.target_ext.get())
            self.log(f"✓ გადაკონვერტირდა: {src.name} -> {dst.name}")
        except Exception as e:
            self.log(f"✕ შეცდომა: {src.name} -> {e}")
            self.file_done(error=True)
            return

        self.file_done()

    def file_done(self, error=False, skipped=False):
        with self.counter_lock:
            self.done_files += 1
            if error:
                self.error_files += 1
            if skipped:
                self.skipped_files += 1
            progress = self.done_files / self.total_files if self.total_files else 0
            percent = int(progress * 100)
            converted = self.done_files - self.error_files

        def update_ui():
            self.progress_ring.set_percent(percent)
            self.total_stat.value_label.configure(text=str(self.total_files))
            self.converted_stat.value_label.configure(text=str(converted))
            self.error_stat.value_label.configure(text=str(self.error_files))
            self.progress_caption.configure(text=f"{self.done_files}/{self.total_files} დამუშავდა ({self.skipped_files} გამოტოვებული)")

        self.after(0, update_ui)

    def get_thread_count(self):
        if self.safe_mode.get():
            return 1
        if self.source_ext.get() in ("doc", "docx", "doc/docx"):
            return 1
        cpu = os.cpu_count() or 2
        return max(2, cpu - 1)

    def collect_files(self):
        src = self.source_ext.get()
        if src == "doc/docx":
            exts = {".doc", ".docx"}
        else:
            exts = {f".{src}"}
        return [f for f in self.input_folder.rglob("*") if f.suffix.lower() in exts]

    def run_conversion(self):
        self.cancel_flag.clear()

        files = self.collect_files()
        self.total_files = len(files)
        self.done_files = 0
        self.error_files = 0
        self.skipped_files = 0

        threads = int(self.get_thread_count())

        self.log(f"ნაპოვნი ფაილები: {self.total_files}")
        self.log(f"გამოყენებული thread-ები: {threads}")

        self.after(0, lambda: self.total_stat.value_label.configure(text=str(self.total_files)))
        self.after(0, lambda: self.progress_ring.set_percent(0))

        needs_word = self.source_ext.get() in ("doc", "docx", "doc/docx") or (self.target_ext.get() in ("doc", "docx") and self.source_ext.get() == "pdf")

        if needs_word and not WORD_COM_AVAILABLE:
            self.log("შეცდომა: ეს კონვერტაცია მოითხოვს Microsoft Word-სა და pywin32-ს (მუშაობს მხოლოდ Windows-ზე).")
            self.after(0, lambda: self.start_card.set_enabled(True))
            return

        try:
            if threads == 1:
                for f in files:
                    if self.cancel_flag.is_set():
                        self.log("გაუქმდა.")
                        break
                    self.convert_single(f)
            else:
                with ThreadPoolExecutor(max_workers=threads) as ex:
                    list(ex.map(self.convert_single, files))
        finally:
            WordSession.close()

        self.log(f"დასრულდა. სულ: {self.total_files}, შეცდომები: {self.error_files}, გამოტოვებული: {self.skipped_files}")
        self.after(0, lambda: self.start_card.set_enabled(True))

    def start_conversion(self):
        if not self.input_folder or not self.output_folder:
            self.log("აირჩიე ორივე ფოლდერი")
            return
        if self.source_ext.get() == self.target_ext.get():
            self.log("იგივე ფორმატია")
            return

        self.start_card.set_enabled(False)
        threading.Thread(target=self.run_conversion, daemon=True).start()

    def cancel_conversion(self):
        self.cancel_flag.set()
        self.log("Cancel...")
