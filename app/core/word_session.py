import threading

try:
    import win32com.client as win32
    import pythoncom
    WORD_COM_AVAILABLE = True
except ImportError:
    WORD_COM_AVAILABLE = False


class WordSession:
    """Thread-local Word.Application session."""

    _local = threading.local()

    @classmethod
    def get(cls):
        if not WORD_COM_AVAILABLE:
            raise RuntimeError(
                "pywin32 (win32com) ან Microsoft Word ვერ მოიძებნა. "
                "ეს ფუნქცია მუშაობს მხოლოდ Windows-ზე, დაინსტალირებული MS Word-ით."
            )
        if not getattr(cls._local, "initialized", False):
            pythoncom.CoInitialize()
            app = win32.gencache.EnsureDispatch("Word.Application")
            app.Visible = False
            app.DisplayAlerts = 0
            cls._local.app = app
            cls._local.initialized = True
        return cls._local.app

    @classmethod
    def close(cls):
        if getattr(cls._local, "initialized", False):
            try:
                cls._local.app.Quit()
            except Exception:
                pass
            try:
                pythoncom.CoUninitialize()
            except Exception:
                pass
            cls._local.initialized = False
