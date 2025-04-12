# main.py
# ==============================================================================
# ---------------------- ZMIENNA ŚRODOWISKOWA BIBLIOTEKI -----------------------
import os
os.environ.pop("QT_QPA_PLATFORM_PLUGIN_PATH", None)


from PyQt5.QtCore import QLibraryInfo
qt_plugins_path = QLibraryInfo.location(QLibraryInfo.PluginsPath)
os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = qt_plugins_path + "/platforms"

"""
Jak wyrzuci błędy to trzeba zmieniać to powyżej albo instalować/przeinstalować
biblioteki!!!
"""
# ==============================================================================


# PROGRAM
import sys
from PyQt5 import QtWidgets
from main_window import MainWindow
from qt_material import apply_stylesheet
import utils

def main():
    # ustawienie motywu
    app = QtWidgets.QApplication(sys.argv)
    apply_stylesheet(app, theme='dark_teal.xml')

    # włączenie okna aplikacji
    window = MainWindow()
    window.signals.array_ready.connect(utils.sheet_image_handler)
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
