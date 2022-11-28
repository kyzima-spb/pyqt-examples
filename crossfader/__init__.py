import sys

from PyQt6.QtWidgets import QApplication

from .MainWindow import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName(app.translate('main', 'Cross Fader'))

    window = MainWindow()
    window.resize(600, 600)
    window.show()

    return app.exec()
