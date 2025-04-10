#draggable_point.py
from PyQt5 import QtCore, QtGui, QtWidgets

class DraggablePoint(QtWidgets.QGraphicsEllipseItem):
    """
    Reprezentacja punktu – umożliwia przeciąganie.
    Ustawienie flagi ItemIgnoresTransformations powoduje, że punkt ma stały rozmiar
    niezależnie od przybliżania/oddalania.
    """
    def __init__(self, x, y, radius=4, *args, **kwargs):
        super().__init__(-radius, -radius, 2 * radius, 2 * radius, *args, **kwargs)
        self.setBrush(QtGui.QBrush(QtCore.Qt.red))
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QtWidgets.QGraphicsItem.ItemSendsGeometryChanges, True)
        # To sprawia, że rozmiar punktu nie zmienia się przy skalowaniu widoku:
        self.setFlag(QtWidgets.QGraphicsItem.ItemIgnoresTransformations, True)
        self.setPos(x, y)
        self.radius = radius

    def itemChange(self, change, value):
        if change == QtWidgets.QGraphicsItem.ItemPositionHasChanged:
            if self.scene() is not None and hasattr(self.scene(), "updatePolygon"):
                self.scene().updatePolygon()
        return super().itemChange(change, value)
