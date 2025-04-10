# main.py
import os
os.environ.pop("QT_QPA_PLATFORM_PLUGIN_PATH", None)

from PyQt5.QtCore import QLibraryInfo
qt_plugins_path = QLibraryInfo.location(QLibraryInfo.PluginsPath)
os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = qt_plugins_path + "/platforms"



import sys
from PyQt5 import QtWidgets
from main_window import MainWindow
from qt_material import apply_stylesheet
import utils

def main():
    app = QtWidgets.QApplication(sys.argv)
    # Ustawienie nowoczesnego ciemnego motywu
    apply_stylesheet(app, theme='dark_teal.xml')
    window = MainWindow()
    window.signals.array_ready.connect(utils.handle_array)
    # warped = psp.perspective_with_scaling(image, ordered_pts)
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
