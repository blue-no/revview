# __main__.py
import sys
from pathlib import Path

from PyQt5 import QtWidgets

from revview._const import _settings_file
from revview._style import enable_process_dpi_awareness
from revview.main.controller import MainWindowController
from revview.settings.model import Settings

if __name__ == "__main__":
    fp = Path(_settings_file)
    fp.parent.mkdir(parents=True, exist_ok=True)
    settings = Settings.initialize(fp=_settings_file)
    if settings.enable_process_dpi_awareness:
        enable_process_dpi_awareness()
    app = QtWidgets.QApplication(sys.argv)
    MainWindowController(settings=settings).show_window()
    sys.exit(app.exec_())
