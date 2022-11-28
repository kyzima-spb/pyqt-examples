import enum
import typing as t
import weakref

from PyQt6.QtCore import (
    pyqtSlot,
    pyqtSignal,
    Qt,
    QDir,
    QFileInfo,
    QStandardPaths,
    QUrl,
)
from PyQt6.QtGui import (
    QDesktopServices,
    QImage,
    QImageReader,
    QPalette,
)
from PyQt6.QtWidgets import (
    QApplication,
    QDialogButtonBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from . import utils
from .CrossFader import CrossFader
from .StatusButtonBar import StatusButtonBar


STATUS_TIMEOUT = 1000 * 10
STOP_WAIT = 100


class StopState(enum.IntEnum):
    Stopping = enum.auto()
    Terminating = enum.auto()


class MainWindow(QMainWindow):
    def __init__(self, parent: t.Optional[QWidget] = None) -> None:
        super().__init__(parent)

        self._progressBarForFilename: t.Dict[str, QProgressBar] = {}
        self._progressLabels: t.List[QLabel] = []
        self._crossFaders: t.List[CrossFader] = []
        self._canceled = False

        self.createWidgets()
        self.createLayout()
        self.createConnections()

        self.firstButton.setFocus()
        self.statusBar.showMessage('Ready', STATUS_TIMEOUT)
        self.setWindowTitle(QApplication.applicationName())

    def createWidgets(self) -> None:
        self.firstButton = QPushButton('First Image:', self)
        self.firstLabel = QLabel(self)
        self.firstLabel.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Sunken)
        self.lastButton = QPushButton('Last Image:', self)
        self.lastLabel = QLabel(self)
        self.lastLabel.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Sunken)
        self.baseNameLabel = QLabel('Base Name:', self)
        self.baseNameEdit = QLineEdit('Image-', self)
        self.baseNameLabel.setBuddy(self.baseNameEdit)
        self.numberLabel = QLabel('Number:', self)
        self.numberSpinBox = QSpinBox(self)
        self.numberLabel.setBuddy(self.numberSpinBox)
        self.numberSpinBox.setRange(1, 14)
        self.numberSpinBox.setValue(5)
        self.numberSpinBox.setAlignment(
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight
        )

        self.progressWidget = QWidget(self)
        self.progressLayout = QGridLayout(self.progressWidget)
        self.scrollArea = QScrollArea(self)
        self.scrollArea.setBackgroundRole(QPalette.ColorRole.Dark)
        self.scrollArea.setWidget(self.progressWidget)
        self.scrollArea.setWidgetResizable(True)

        self.generateOrCancelButton = QPushButton('G&enerate', self)
        self.generateOrCancelButton.setEnabled(False)
        self.generateOrCancelButton.setDefault(True)
        self.quitButton = QPushButton('Quit')

    def createLayout(self) -> None:
        self.row1Layout = QHBoxLayout()
        self.row1Layout.addWidget(self.firstButton)
        self.row1Layout.addWidget(self.firstLabel, 1)
        self.row2Layout = QHBoxLayout()
        self.row2Layout.addWidget(self.lastButton)
        self.row2Layout.addWidget(self.lastLabel, 1)
        self.row3Layout = QHBoxLayout()
        self.row3Layout.addWidget(self.baseNameLabel)
        self.row3Layout.addWidget(self.baseNameEdit, 1)
        self.row3Layout.addWidget(self.numberLabel)
        self.row3Layout.addWidget(self.numberSpinBox)

        self.statusBar = StatusButtonBar(self)
        self.statusBar.buttonBox().addButton(
            self.generateOrCancelButton,
            QDialogButtonBox.ButtonRole.ActionRole
        )
        self.statusBar.buttonBox().addButton(
            self.quitButton,
            QDialogButtonBox.ButtonRole.AcceptRole
        )

        widget = QWidget(self)

        self.layout = QVBoxLayout(widget)
        self.layout.addLayout(self.row1Layout)
        self.layout.addLayout(self.row2Layout)
        self.layout.addLayout(self.row3Layout)
        self.layout.addWidget(self.scrollArea, 1)
        self.layout.addWidget(self.statusBar)

        self.setCentralWidget(widget)

    def createConnections(self) -> None:
        self.firstButton.clicked.connect(self.setFirstImage)
        self.lastButton.clicked.connect(self.setLastImage)
        self.generateOrCancelButton.clicked.connect(self.generateOrCancelImages)
        self.quitButton.clicked.connect(self.quit)

    @pyqtSlot()
    def setFirstImage(self) -> None:
        self.setImageFile(self.firstLabel, 'first')
        self.lastButton.setFocus()

    @pyqtSlot()
    def setLastImage(self) -> None:
        self.setImageFile(self.lastLabel, 'last')
        self.baseNameEdit.setFocus()

    @pyqtSlot(object, str)
    def setImageFile(self, targetLabel: QLabel, which: str) -> None:
        picturesLocations = QStandardPaths.standardLocations(
            QStandardPaths.StandardLocation.PicturesLocation
        )

        if picturesLocations:
            directory = picturesLocations[0]
        else:
            directory = QDir.homePath()

        if which == 'first' and self.firstLabel.text():
            directory = QFileInfo(self.firstLabel.text()).path()
        elif which == 'last':
            if self.lastLabel.text():
                directory = QFileInfo(self.lastLabel.text()).path()
            elif self.firstLabel.text():
                directory = QFileInfo(self.firstLabel.text()).path()

        filename, _ = QFileDialog.getOpenFileName(
            self,
            f'Choose the {which} image',
            directory,
            utils.filenameFilter('Images', QImageReader.supportedImageFormats()),
        )
        targetLabel.setText(QDir.toNativeSeparators(filename))
        self.updateUi()

    @pyqtSlot()
    def generateOrCancelImages(self):
        if self.generateOrCancelButton.text() == 'G&enerate':
            self.generateOrCancelButton.setEnabled(False)
            self.statusBar.showMessage('Generating...')
            self._canceled = False
            self.cleanUp()
            firstImage = QImage(self.firstLabel.text())
            lastImage = QImage(self.lastLabel.text())
            for i in range(self.numberSpinBox.value()):
                self.createAndRunACrossFader(i, firstImage, lastImage)
            self.generateOrCancelButton.setText('Canc&el')
        else:
            self._canceled = True
            self.cleanUp()
            self.generateOrCancelButton.setText('G&enerate')
        self.updateUi()

    def createAndRunACrossFader(
        self,
        number: int,
        firstImage: QImage,
        lastImage: QImage,
    ) -> None:
        filename = '{}{:02d}.png'.format(self.baseNameEdit.text(), number + 1)

        progressLabel = QLabel(filename, self.progressWidget)
        self._progressLabels.append(progressLabel)

        progressBar = QProgressBar(self.progressWidget)
        progressBar.setRange(0, 100)
        self._progressBarForFilename[filename] = progressBar

        layout = t.cast(QGridLayout, self.progressWidget.layout())
        layout.addWidget(progressLabel, number, 0)
        layout.addWidget(progressBar, number, 1)

        firstWeight = (number + 1) / (self.numberSpinBox.value() + 1)
        secondWeight = 1.0 - firstWeight

        crossFader = CrossFader(
            filename, firstImage, firstWeight, lastImage, secondWeight, self
        )
        crossFader.progress.connect(progressBar.setValue)
        crossFader.saving.connect(self.saving)
        crossFader.saved.connect(self.saved)
        crossFader.finished.connect(self.finished)
        self._crossFaders.append(crossFader)
        crossFader.start()

    @pyqtSlot(str)
    def saving(self, filename: str):
        self.statusBar.showMessage(f'Saving {filename!r}', STATUS_TIMEOUT)
        if filename in self._progressBarForFilename:
            progressBar = self._progressBarForFilename[filename]
            progressBar.setRange(0, 0)

    @pyqtSlot(bool, str)
    def saved(self, saved: bool, filename: str):
        message = 'Saved {!r}' if saved else 'Failed to save {!r}'
        self.statusBar.showMessage(message.format(filename), STATUS_TIMEOUT)
        if filename in self._progressBarForFilename:
            progressBar = self._progressBarForFilename[filename]
            progressBar.setRange(0, 1)
            progressBar.setValue(int(saved))
            progressBar.setEnabled(False)

    @pyqtSlot()
    def finished(self) -> None:
        for crossFader in self._crossFaders:
            if crossFader and not crossFader.isFinished():
                return None

        self.generateOrCancelButton.setText('G&enerate')
        if self._canceled:
            self.statusBar.showMessage('Canceled', STATUS_TIMEOUT)
        else:
            self.statusBar.showMessage('Finished')
            if self.statusBar.checkBox().isChecked():
                QDesktopServices.openUrl(
                    QUrl.fromLocalFile(self.firstLabel.text())
                )

    @pyqtSlot()
    def quit(self) -> None:
        self.cleanUp(StopState.Terminating)
        self.close()

    @pyqtSlot()
    def updateUi(self) -> None:
        self.generateOrCancelButton.setEnabled(bool(
            self.firstLabel.text() and self.lastLabel.text()
        ))

    def cleanUp(self, stopState: StopState = StopState.Stopping) -> None:
        for crossFader in self._crossFaders:
            crossFader.stop()
            crossFader.wait()
            crossFader.deleteLater()
        self._crossFaders.clear()

        if stopState is StopState.Terminating:
            return None

        for progressBar in self._progressBarForFilename.values():
            if progressBar:
                progressBar.deleteLater()
        self._progressBarForFilename.clear()

        for progressLabel in self._progressLabels:
            if progressLabel:
                progressLabel.deleteLater()
        self._progressLabels.clear()
