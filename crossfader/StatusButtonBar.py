import typing as t

from PyQt6.QtCore import (
    pyqtSlot,
    QTimer,
)
from PyQt6.QtWidgets import (
    QCheckBox,
    QDialogButtonBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QWidget,
)


class StatusButtonBar(QWidget):
    def __init__(self, parent: t.Optional[QWidget] = None) -> None:
        super().__init__(parent)

        self._label = QLabel(self)
        self._label.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Sunken)
        self._checkBox = QCheckBox('&Show Images', self)
        self._buttonBox = QDialogButtonBox(self)

        self.layout = QHBoxLayout(self)
        self.layout.addWidget(self._label, 1)
        self.layout.addWidget(self._checkBox)
        self.layout.addWidget(self._buttonBox)

    def buttonBox(self) -> QDialogButtonBox:
        return self._buttonBox

    def checkBox(self) -> QCheckBox:
        return self._checkBox

    @pyqtSlot()
    def clear(self) -> None:
        self._label.clear()

    @pyqtSlot()
    def showMessage(self, message: str, timeoutMSec: int = 0) -> None:
        self._label.setText(message)
        if timeoutMSec:
            QTimer.singleShot(timeoutMSec, self.clear)
