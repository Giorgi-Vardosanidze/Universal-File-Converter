import sys
from pathlib import Path

COLOR_BG = "#0A111F"
COLOR_SIDEBAR = "#0C1426"
COLOR_CARD = "#121B30"
COLOR_CARD_HOVER = "#16213A"
COLOR_BORDER = "#1E2A45"
COLOR_TEXT = "#F1F5F9"
COLOR_TEXT_DIM = "#8B97AC"
COLOR_BLUE = "#3B82F6"
COLOR_BLUE_DIM = "#1E3A66"
COLOR_PURPLE = "#8B5CF6"
COLOR_PURPLE_DIM = "#2E2350"
COLOR_GREEN = "#22C55E"
COLOR_GREEN_DIM = "#173821"
COLOR_RED = "#EF4444"
COLOR_RED_DIM = "#3A1B1F"

SUPPORTED_SOURCE = ["DOC", "DOCX", "DOC/DOCX", "PDF", "TXT"]
SUPPORTED_TARGET = ["DOC", "DOCX", "PDF", "TXT"]

PRESETS = {
    "DOC/DOCX → PDF": ("doc/docx", "pdf", "Convert .doc and .docx to pdf"),
    "DOCX → PDF": ("docx", "pdf", "Convert .docx to pdf"),
    "DOC → PDF": ("doc", "pdf", "Convert .doc to pdf"),
    "PDF → DOCX": ("pdf", "docx", "Convert .pdf to docx"),
    "PDF → TXT": ("pdf", "txt", "Extract text from .pdf"),
    "TXT → DOCX": ("txt", "docx", "Convert .txt to docx"),
    "TXT → PDF": ("txt", "pdf", "Convert .txt to pdf"),
    "DOCX → TXT": ("docx", "txt", "Extract text from .docx"),
}

WORD_PDF_FORMAT = 17
ICONS_DIR = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent.parent)) / "icons"
