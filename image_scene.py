# image_scene.py
from PyQt5 import QtCore, QtGui, QtWidgets
from draggable_point import DraggablePoint


class ImageScene(QtWidgets.QGraphicsScene):
    """
    Scena zawierająca obraz, punkty i rysowany obrys czworokąta.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.pixmap_item = None
        self.points = []  # Lista obiektów DraggablePoint (rogi zaznaczonej perspektywy)
        self.polygon_item = None  # QGraphicsPolygonItem do rysowania obrysu perspektywy (krawędzi)

    def setImage(self, pixmap):
        self.clear()
        self.points = []
        self.setBackgroundBrush(QtGui.QBrush(QtCore.Qt.white))
        self.pixmap_item = self.addPixmap(pixmap) # dodaj obrazek do sceny
        self.setSceneRect(self.pixmap_item.boundingRect())
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
        Sortowanie: lewy górny, prawy górny, lewy dolny, prawy dolny.
        """
        if self.pixmap_item is None or len(self.points) < 4:
            if self.polygon_item is not None:
                self.polygon_item.setPolygon(QtGui.QPolygonF())
            return

        # Pobierz aktualne pozycje punktów
        pts = [point.pos() for point in self.points]
        # Najpierw sortujemy punkty po współrzędnej y, dzięki czemu dwa górne są na początku
        pts_sorted = sorted(pts, key=lambda p: p.y())
        # Dla dwóch punktów o najmniejszej wartości y: lewy i prawy
        top_points = sorted(pts_sorted[:2], key=lambda p: p.x())
        # Dla dwóch pozostałych: lewy i prawy (przyjmujemy, że są dolne)
        bottom_points = sorted(pts_sorted[2:], key=lambda p: p.x())
        # Nowa kolejność: lewy górny, prawy górny, lewy dolny, prawy dolny.
        ordered = [top_points[0], top_points[1], bottom_points[1], bottom_points[0]]
        polygon = QtGui.QPolygonF(ordered)
        self.polygon_item.setPolygon(polygon)

    def mousePressEvent(self, event):
        # Jeśli obraz nie został wczytany, ignoruj kliknięcia
        if self.pixmap_item is None:
            return
        if event.button() == QtCore.Qt.LeftButton and len(self.points) < 4:
            # Sprawdzamy, czy kliknięto poza istniejącym punktem
            items = self.items(event.scenePos())
            if not any(isinstance(item, DraggablePoint) for item in items):
                self.addPoint(event.scenePos())
        super().mousePressEvent(event)

