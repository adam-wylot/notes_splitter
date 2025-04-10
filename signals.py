from PyQt5.QtCore import QObject, pyqtSignal
import numpy as np

class SignalEmitter(QObject):
    array_ready = pyqtSignal(np.ndarray)
