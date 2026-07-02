from app.ui.app import ConverterApp
from app.core.constants import ICONS_DIR
import sys

if __name__ == "__main__":
    if not ICONS_DIR.exists():
        print(
            f"გაფრთხილება: აიქონების ფოლდერი ვერ მოიძებნა: {ICONS_DIR}\n"
            "შექმენი ფოლდერი 'icons' სკრიპტის გვერდით და ჩადე PNG აიქონები."
        )

    if sys.platform != "win32":
        print(
            "გაფრთხილება: DOC/DOCX <-> PDF კონვერტაციები Word COM-ით მუშაობს მხოლოდ "
            "Windows-ზე, დაინსტალირებული Microsoft Word-ით. PDF<->TXT და TXT<->DOCX "
            "ყველგან მუშაობს."
        )

    app = ConverterApp()
    app.mainloop()
