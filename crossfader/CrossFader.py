import typing as t

from PyQt6.QtCore import (
    pyqtSignal,
    pyqtSlot,
    Qt,
    QObject,
    QThread,
)
from PyQt6.QtGui import (
    qBlue,
    qGreen,
    qRed,
    qRgb,
    QImage,
)


class CrossFader(QThread):
    progress = pyqtSignal(int)
    saving = pyqtSignal(str)
    saved = pyqtSignal(bool, str)

    def __init__(
        self,
        filename: str,
        first: QImage,
        firstWeight: float,
        last: QImage,
        lastWeight: float,
        parent: t.Optional[QObject] = None
    ) -> None:
        super().__init__(parent)
        self._filename = filename
        self._firstWeight = firstWeight
        self._lastWeight = lastWeight
        self._stopped = False

        size = first.size().boundedTo(last.size())
        self._first = first.scaled(
            size,
            Qt.AspectRatioMode.IgnoreAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self._last = last.scaled(
            size,
            Qt.AspectRatioMode.IgnoreAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )

    def run(self) -> None:
        image = QImage(
            self._first.width(),
            self._first.height(),
            QImage.Format.Format_RGB32,
        )
        self.progress.emit(0)

        onePercent = image.width() / 100.0

        for x in range(image.width()):
            for y in range(image.height()):
                firstPixel = self._first.pixel(x, y)
                lastPixel = self._last.pixel(x, y)

                red = round(
                    (qRed(firstPixel) * self._firstWeight) + (qRed(lastPixel) * self._lastWeight)
                )
                green = round(
                    (qGreen(firstPixel) * self._firstWeight) + (qGreen(lastPixel) * self._lastWeight)
                )
                blue = round(
                    (qBlue(firstPixel) * self._firstWeight) + (qBlue(lastPixel) * self._lastWeight)
                )

                image.setPixel(x, y, qRgb(red, green, blue))

                if (y % 64) == 0 and self._stopped:
                    return None

            if self._stopped:
                return None

            self.progress.emit(round(x / onePercent))

        self.progress.emit(image.width())

        if self._stopped:
            return None

        self.saving.emit(self._filename)

        if self._stopped:
            return None

        self.saved.emit(image.save(self._filename), self._filename)

    @pyqtSlot()
    def stop(self) -> None:
        self._stopped = True
