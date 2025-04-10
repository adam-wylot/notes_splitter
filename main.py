import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from qt_material import apply_stylesheet


class DraggablePoint(QtWidgets.QGraphicsEllipseItem):
    """
    Reprezentacja punktu - umożliwia przeciąganie.
    Przy każdej zmianie pozycji informuje scenę, żeby odświeżyła obrys.
    """

    def __init__(self, x, y, radius=6, *args, **kwargs):
        super().__init__(-radius, -radius, 2 * radius, 2 * radius, *args, **kwargs)
        self.setBrush(QtGui.QBrush(QtCore.Qt.red))
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QtWidgets.QGraphicsItem.ItemSendsGeometryChanges, True)
        self.setPos(x, y)
        self.radius = radius

    def itemChange(self, change, value):
        if change == QtWidgets.QGraphicsItem.ItemPositionHasChanged:
            if self.scene() is not None and hasattr(self.scene(), "updatePolygon"):
                self.scene().updatePolygon()
        return super().itemChange(change, value)


class ImageScene(QtWidgets.QGraphicsScene):
    """
    Scena zawierająca obraz, punkty i rysowany obrys czworokąta.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.pixmap_item = None
        self.points = []  # Lista punktów (DraggablePoint)
        self.polygon_item = None  # QGraphicsPolygonItem rysujący linie

    def setImage(self, pixmap):
        self.clear()
        self.points = []
        # Dodaj obrazek
        self.pixmap_item = self.addPixmap(pixmap)
        # Ustaw rozmiar sceny na rozmiar obrazka
        self.setSceneRect(self.pixmap_item.boundingRect())
        # Dodaj pusty obrys
        self.polygon_item = self.addPolygon(QtGui.QPolygonF(), pen=QtGui.QPen(QtCore.Qt.green, 2))

    def addPoint(self, pos):
        if len(self.points) >= 4:
            return
        point = DraggablePoint(pos.x(), pos.y())
        self.points.append(point)
        self.addItem(point)
        self.updatePolygon()

    def updatePolygon(self):
        """
        Jeśli mamy 4 punkty, sortuje je i rysuje czworokąt.
        Sortowanie: lewy górny, prawy górny, prawy dolny, lewy dolny.
        """
        if self.pixmap_item is None or len(self.points) < 4:
            if self.polygon_item is not None:
                self.polygon_item.setPolygon(QtGui.QPolygonF())
            return

        # Pobierz aktualne pozycje punktów
        pts = [point.pos() for point in self.points]
        pts_sorted = sorted(pts, key=lambda p: p.y())
        top_points = sorted(pts_sorted[:2], key=lambda p: p.x())
        bottom_points = sorted(pts_sorted[2:], key=lambda p: p.x())
        ordered = [top_points[0], top_points[1], bottom_points[1], bottom_points[0]]
        polygon = QtGui.QPolygonF(ordered)
        self.polygon_item.setPolygon(polygon)

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton and len(self.points) < 4:
            # Sprawdzamy, czy kliknięto poza istniejącym punktem
            items = self.items(event.scenePos())
            if not any(isinstance(item, DraggablePoint) for item in items):
                self.addPoint(event.scenePos())
        super().mousePressEvent(event)


class ImageViewer(QtWidgets.QGraphicsView):
    """
    Widok z obsługą drag&drop oraz powiększania/oddalania obrazka (Ctrl + scroll).
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setRenderHints(QtGui.QPainter.Antialiasing | QtGui.QPainter.SmoothPixmapTransform)
        self.setTransformationAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        event.acceptProposedAction()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            # Używamy self.window(), aby dostać się do głównego okna i wywołać metodę loadImage
            main_window = self.window()
            if hasattr(main_window, "loadImage"):
                main_window.loadImage(file_path)
        event.acceptProposedAction()

    def wheelEvent(self, event):
        # Jeśli przytrzymany jest klawisz Ctrl, wykonaj zoom
        if QtWidgets.QApplication.keyboardModifiers() == QtCore.Qt.ControlModifier:
            zoom_in = event.angleDelta().y() > 0
            factor = 1.15 if zoom_in else 1 / 1.15
            self.scale(factor, factor)
        else:
            super().wheelEvent(event)


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Obrazek z zaznaczaniem punktów")
        self.resize(900, 700)

        self.scene = ImageScene()
        self.view = ImageViewer(self)
        self.view.setScene(self.scene)

        # Utworzenie przycisków
        self.load_button = QtWidgets.QPushButton("Wczytaj obrazek")
        self.load_button.clicked.connect(self.openImageDialog)
        self.send_button = QtWidgets.QPushButton("Wyślij współrzędne")
        self.send_button.clicked.connect(self.processPoints)

        # Układ pionowy: Widok + przyciski
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
        if pixmap.isNull():
            QtWidgets.QMessageBox.critical(self, "Błąd", "Nie udało się wczytać obrazka.")
            return
        self.scene.setImage(pixmap)
        # Dopasowanie widoku do rozmiaru obrazka
        self.view.fitInView(self.scene.sceneRect(), QtCore.Qt.KeepAspectRatio)

    def processPoints(self):
        if len(self.scene.points) != 4:
            QtWidgets.QMessageBox.information(self, "Informacja", "Należy zaznaczyć 4 punkty.")
            return

        # Przeliczanie współrzędnych punktów z uwzględnieniem skalowania
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

        # Sortowanie punktów w kolejności: lewy górny, prawy górny, prawy dolny, lewy dolny.
        pts = [QtCore.QPointF(x, y) for x, y in points_coords]
        pts_sorted = sorted(pts, key=lambda p: p.y())
        top_points = sorted(pts_sorted[:2], key=lambda p: p.x())
        bottom_points = sorted(pts_sorted[2:], key=lambda p: p.x())
        ordered_pts = [top_points[0], top_points[1], bottom_points[1], bottom_points[0]]

        msg = "\n".join([f"Punkt {i + 1}: ({p.x():.2f}, {p.y():.2f})" for i, p in enumerate(ordered_pts)])
        QtWidgets.QMessageBox.information(self, "Współrzędne", msg)


def main():
    app = QtWidgets.QApplication(sys.argv)
    # Użycie nowoczesnego ciemnego motywu
    apply_stylesheet(app, theme='dark_teal.xml')
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
