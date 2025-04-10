# image_viewer.py
from PyQt5 import QtCore, QtGui, QtWidgets

class ImageViewer(QtWidgets.QGraphicsView):
    """
    Widok z obsługą drag & drop oraz powiększania/oddalania obrazka (Ctrl + scroll).
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
            # Używamy self.window(), by uzyskać referencję do głównego okna
            main_window = self.window()
            if hasattr(main_window, "loadImage"):
                main_window.loadImage(file_path)
        event.acceptProposedAction()

    def wheelEvent(self, event):
        modifiers = QtWidgets.QApplication.keyboardModifiers()
        # Jeśli wciśnięty jest Shift, przesuwamy horyzontalnie
        if modifiers & QtCore.Qt.ShiftModifier:
            delta = event.angleDelta().y()  # używamy wartości y
            # Przesuwamy pasek horyzontalny – wartość dopasuj eksperymentalnie
            h_scroll = self.horizontalScrollBar()
            h_scroll.setValue(h_scroll.value() - delta)
        # Jeśli wciśnięty jest Ctrl – wykonujemy zoom
        elif modifiers & QtCore.Qt.ControlModifier:
            zoom_in = event.angleDelta().y() > 0
            factor = 1.15 if zoom_in else 1/1.15
            self.scale(factor, factor)
        else:
            super().wheelEvent(event)