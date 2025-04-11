# main_window.py
import numpy as np
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import pyqtSignal

from image_scene import ImageScene
from image_viewer import ImageViewer
from signals import SignalEmitter
import cv2

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Czytanie nut")
        self.resize(900, 700)

        self.scene = ImageScene()
        self.view = ImageViewer(self)
        self.view.setScene(self.scene)

        self.signals = SignalEmitter()
        self.image = None

        self.load_button = QtWidgets.QPushButton("📁 Wczytaj obraz")
        self.load_button.clicked.connect(self.openImageDialog)
        self.send_button = QtWidgets.QPushButton("💡 Procesuj")
        self.send_button.clicked.connect(self.processPoints)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.view)
        layout.addWidget(self.load_button)
        layout.addWidget(self.send_button)

        container = QtWidgets.QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def openImageDialog(self):
        options = QtWidgets.QFileDialog.Options()
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Wczytaj obrazek", "",
            "Pliki obrazów (*.png *.jpg *.bmp *.jpeg);;Wszystkie pliki (*.*)",
            options=options)
        if file_path:
            self.loadImage(file_path)

    def loadImage(self, file_path):
        pixmap = QtGui.QPixmap(file_path)
        self.image = cv2.imread(file_path)
        if pixmap.isNull():
            QtWidgets.QMessageBox.critical(self, "⚠️ Błąd", "Nie udało się wczytać obrazka!")
            return
        self.scene.setImage(pixmap)
        self.view.fitInView(self.scene.sceneRect(), QtCore.Qt.KeepAspectRatio)

    def processPoints(self):
        if self.scene.pixmap_item is None:
            QtWidgets.QMessageBox.information(self, "ℹ️ Informacja", "Należy wczytać obrazek.")
            return

        if self.image is None:
            QtWidgets.QMessageBox.critical(self, "⚠️ Błąd", "Wystąpił problem podczas przetwarzania obrazka!")
            return

        if 0 < len(self.scene.points) < 4:
            QtWidgets.QMessageBox.information(self, "ℹ️ Informacja", f"Zaznacz pozostałe {4 - len(self.scene.points)} punkty.")
            return

        ordered_pts = []

        if len(self.scene.points) == 0:
            ordered_pts = [QtCore.QPointF(0, 0), QtCore.QPointF(self.scene.pixmap_item.pixmap().width(), 0), QtCore.QPointF(0, self.scene.pixmap_item.pixmap().height()), QtCore.QPointF(self.scene.pixmap_item.pixmap().width(), self.scene.pixmap_item.pixmap().height())]
        else:
            pixmap_item = self.scene.pixmap_item
            if pixmap_item is not None:
                original_size = pixmap_item.pixmap().size()
                scene_rect = self.scene.sceneRect()
                scale_x = original_size.width() / scene_rect.width()
                scale_y = original_size.height() / scene_rect.height()
            else:
                scale_x = scale_y = 1.0

            points_coords = []
            for point in self.scene.points:
                pos = point.pos()
                orig_x = pos.x() * scale_x
                orig_y = pos.y() * scale_y
                points_coords.append((orig_x, orig_y))

            pts = [QtCore.QPointF(x, y) for x, y in points_coords]
            # Sortowanie w celu uzyskania kolejności: lewy górny, prawy górny, lewy dolny, prawy dolny.
            pts_sorted = sorted(pts, key=lambda p: p.y())
            top_points = sorted(pts_sorted[:2], key=lambda p: p.x())
            bottom_points = sorted(pts_sorted[2:], key=lambda p: p.x())
            ordered_pts = [top_points[0], top_points[1], bottom_points[0], bottom_points[1]]

        array = np.array([[p.x(), p.y()] for p in ordered_pts], dtype=np.float32)
        self.signals.array_ready.emit(self.image, array)

