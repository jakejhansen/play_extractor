# PyQt5 Video player
# !/usr/bin/env python

from PyQt5.QtCore import QDir, Qt, QUrl
from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtWidgets import *
from PyQt5.QtWidgets import QMainWindow, QWidget, QPushButton, QAction
from PyQt5.QtGui import *
from PyQt5.QtCore import QTimer
from PyQt5 import QtCore
import sys
import os
from collections import namedtuple

video_container = namedtuple('video', ['path', 'marker_begin', 'marker_end'], )


class List(QListWidget):
    def __init__(self, parent):
        super(List, self).__init__(parent)


    def keyPressEvent(self, event):
        self.parent().keyPressEvent(event)


class VideoWindow(QMainWindow):

    def __init__(self, parent=None):
        super(VideoWindow, self).__init__(parent)

        # Variables ########################
        self.marker_begin = None
        self.marker_end = None
        self.current_pos = 0

        # Stop playing when reaching marker end?
        self.stop_at_marker_end = False

        # Media list
        self.video_list = [video_container("/run/user/1000/doc/fced845e/iron5_3.mp4", "None", "None"),
                           video_container("/run/user/1000/doc/d3bd697e/thefuck.mp4", "None", "None")]

        # Which video are currently playing
        self.index = 0
        ###################################

        # PyQt
        self.setWindowTitle("PyQt Video Player Widget Example - pythonprogramminglanguage.com")

        self.mediaPlayer = QMediaPlayer(None, QMediaPlayer.VideoSurface)

        self.videoWidget = QVideoWidget()
        self.videoWidget.setMouseTracking(True)
        self.videoWidget.installEventFilter(self)

        self.playButton = QPushButton()
        self.playButton.setEnabled(False)
        self.playButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.playButton.clicked.connect(self.play)

        self.positionSlider = QSlider(Qt.Horizontal)
        self.positionSlider.setRange(0, 0)
        self.positionSlider.sliderMoved.connect(self.setPosition)

        self.errorLabel = QLabel()
        self.errorLabel.setSizePolicy(QSizePolicy.Preferred,
                                      QSizePolicy.Maximum)

        # Create new action
        openAction = QAction(QIcon('open.png'), '&Open', self)
        openAction.setShortcut('Ctrl+O')
        openAction.setStatusTip('Open movie')
        openAction.triggered.connect(self.openFile)

        # Create exit action
        exitAction = QAction(QIcon('exit.png'), '&Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Exit application')
        exitAction.triggered.connect(self.exitCall)

        # Create menu bar and add action
        menuBar = self.menuBar()
        fileMenu = menuBar.addMenu('&File')
        fileMenu.addAction(openAction)
        fileMenu.addAction(exitAction)

        # Create a widget for window contents
        wid = QWidget(self)
        self.setCentralWidget(wid)

        # Create layouts to place inside widget
        controlLayout = QHBoxLayout()
        controlLayout.setContentsMargins(0, 0, 0, 0)
        self.label = QLabel(self)
        controlLayout.addWidget(self.label)
        # controlLayout.addWidget(self.positionSlider)

        listlayout = QHBoxLayout()
        listlayout.setContentsMargins(0, 0, 0, 0)
        self.labellist = List(self)
        listlayout.addWidget(self.labellist)
        self.mImgList = self.scanAllImages("/home/jake/dev/play_extractor")
        for imgPath in self.mImgList:
            item = QListWidgetItem(imgPath)
            # item.setForeground(Qt.red)
            # item.setData(2, imgPath)
            # item.setText(imgPath.split("/")[-1])
            # item.setText("test")
            self.labellist.addItem(item)
        # self.labellist.item(0).setSelected(True)

        layout = QVBoxLayout()
        layout.addWidget(self.videoWidget)
        layout.addLayout(controlLayout)
        layout.addWidget(self.errorLabel)

        top = QHBoxLayout()
        top.setContentsMargins(0, 0, 0, 0)
        top.addLayout(listlayout)
        top.addLayout(layout)
        top.setStretchFactor(listlayout, 1)
        top.setStretchFactor(layout, 5)
        # Set widget to contain window contents
        wid.setLayout(top)

        self.mediaPlayer.setVideoOutput(self.videoWidget)
        self.mediaPlayer.stateChanged.connect(self.mediaStateChanged)
        self.mediaPlayer.positionChanged.connect(self.positionChanged)
        self.mediaPlayer.durationChanged.connect(self.durationChanged)
        self.mediaPlayer.error.connect(self.handleError)

        self.openDefault()

        self.qTimer = QTimer()
        # set interval to 1 s
        self.qTimer.setInterval(20)  # 1000 ms = 1 s
        # connect timeout signal to signal handler
        self.qTimer.timeout.connect(self.getSensorValue)
        # start timer
        self.qTimer.start()


    def scanAllImages(self, folderPath):
        extensions = ['.%s' % fmt.data().decode("ascii").lower() for fmt in QImageReader.supportedImageFormats()]
        images = []
        extensions = [".mp4"]

        for root, dirs, files in os.walk(folderPath):
            for file in files:
                if file.lower().endswith(tuple(extensions)):
                    relativePath = os.path.join(root, file)
                    path = str(os.path.abspath(relativePath))
                    images.append(path)
        return images


    def time_to_x(self, timepoint):
        return int(timepoint / self.mediaPlayer.duration() * self.videoWidget.width())


    def updateImage(self, position=0):
        # width = self.frameGeometry().width()
        # width = self.videoWidget.width()
        # height = self.frameGeometry().height()
        # width = self.videoWidget.geometry().width()
        width = self.label.width()
        pixmap = QPixmap(width, 50)
        pixmap.fill(Qt.gray)

        painter = QPainter()
        painter.begin(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(Qt.black, 1))
        markerwidth = 10
        markerwidth_begin_end = 10
        # Draw beginning and end markers

        try:
            if self.marker_begin:
                markerpos = self.time_to_x(self.marker_begin)
                if self.marker_end:
                    bar_width = self.time_to_x(self.marker_end) - markerpos
                elif markerpos < self.time_to_x(self.current_pos):
                    bar_width = self.time_to_x(self.current_pos) - markerpos
                else:
                    bar_width = 0
                painter.setBrush(QBrush(Qt.blue, Qt.SolidPattern))
                painter.drawRect(markerpos, 0, bar_width, 50)

                if self.marker_end:
                    if self.current_pos > self.marker_end:
                        painter.setBrush(QBrush(QColor(171, 255, 158), Qt.SolidPattern))
                        bar_width = self.time_to_x(self.current_pos) - self.time_to_x(self.marker_end)
                        painter.drawRect(self.time_to_x(self.marker_end), 0, bar_width, 50)

                    elif self.current_pos < self.marker_begin:
                        painter.setBrush(QBrush(QColor(171, 255, 158), Qt.SolidPattern))
                        bar_width = markerpos - self.time_to_x(self.current_pos)
                        painter.drawRect(self.time_to_x(self.current_pos), 0, bar_width, 50)

                    elif abs(self.current_pos - self.marker_begin) < abs(self.current_pos - self.marker_end):
                        painter.setBrush(QBrush(QColor(255, 101, 84), Qt.SolidPattern))
                        bar_width = self.time_to_x(self.current_pos) - self.time_to_x(self.marker_begin)
                        painter.drawRect(self.time_to_x(self.marker_begin), 0, bar_width, 50)

                    else:
                        painter.setBrush(QBrush(QColor(255, 101, 84), Qt.SolidPattern))
                        bar_width = self.time_to_x(self.marker_end) - self.time_to_x(self.current_pos)
                        painter.drawRect(self.time_to_x(self.current_pos), 0, bar_width, 50)

            for marker in [self.marker_begin, self.marker_end]:
                if marker != None:
                    painter.setBrush(QBrush(Qt.green, Qt.SolidPattern))
                    markerpos = int(marker / self.mediaPlayer.duration() * width)
                    painter.drawRect(min(markerpos, width - markerwidth_begin_end), 0, markerwidth_begin_end, 50)
        except:
            pass
        # Draw video playback marker
        painter.setBrush(QBrush(Qt.white, Qt.SolidPattern))
        painter.drawRect(min(position, width - markerwidth), 0, markerwidth, 50)
        painter.end()
        pixmap.scaled(width, 50)
        self.label.setMinimumSize(1, 50)
        self.label.setPixmap(pixmap)
        self.label.setScaledContents(True)


    def eventFilter(self, source, event):
        if event.type() == QtCore.QEvent.MouseMove:
            self.current_pos = int(event.x() / self.videoWidget.geometry().width() * self.mediaPlayer.duration())
            self.mediaPlayer.setPosition(self.current_pos)
            self.updateImage(event.x())
        return True


    def resizeEvent(self, event):
        QMainWindow.resizeEvent(self, event)
        # self.updateImage()


    def getSensorValue(self):
        position = self.mediaPlayer.position()
        duration = self.mediaPlayer.duration()
        if duration > 0:
            self.updateImage(int(position / self.mediaPlayer.duration() * self.videoWidget.geometry().width()))

        # Stop at marker end if flag is set
        if self.stop_at_marker_end and self.marker_end:
            if position >= self.marker_end:
                if self.mediaPlayer.state() == QMediaPlayer.PlayingState:
                    self.play()


    def openFile(self):
        fileName, _ = QFileDialog.getOpenFileName(self, "Open Movie",
                                                  QDir.homePath())
        print(fileName)
        if fileName != '':
            self.mediaPlayer.setMedia(
                QMediaContent(QUrl.fromLocalFile(fileName)))
            self.playButton.setEnabled(True)


    def openDefault(self):
        fileName = self.video_list[self.index].path
        self.mediaPlayer.setMedia(
            QMediaContent(QUrl.fromLocalFile(fileName)))
        self.playButton.setEnabled(True)
        self.mediaPlayer.play()
        self.mediaPlayer.pause()
        self.mediaPlayer.setPosition(self.current_pos)
        self.updateImage()


    def openDir(self):
        targetDirPath = "/home/jake/dev/play_extractor"
        # self.labelList = QListWidget()


    def exitCall(self):
        sys.exit(app.exec_())


    def play(self):
        if self.mediaPlayer.state() == QMediaPlayer.PlayingState:
            self.mediaPlayer.pause()
        else:
            self.mediaPlayer.play()


    def mediaStateChanged(self, state):
        if self.mediaPlayer.state() == QMediaPlayer.PlayingState:
            self.playButton.setIcon(
                self.style().standardIcon(QStyle.SP_MediaPause))
        else:
            self.playButton.setIcon(
                self.style().standardIcon(QStyle.SP_MediaPlay))


    def positionChanged(self, position):
        pass
        # self.positionSlider.setValue(position)


    def durationChanged(self, duration):
        self.positionSlider.setRange(0, duration)


    def setPosition(self, position):
        self.mediaPlayer.setPosition(position)


    def handleError(self):
        self.playButton.setEnabled(False)
        self.errorLabel.setText("Error: " + self.mediaPlayer.errorString())


    def index_next(self):
        self.index = (self.index + 1) % len(self.video_list)


    def index_prev(self):
        self.index = (self.index - 1) % len(self.video_list)


    def reset(self):
        self.marker_end = None
        self.marker_begin = None
        self.current_pos = 0


    def save(self):
        if self.marker_begin and self.marker_end:
            self.video_list[self.index] = video_container(self.video_list[self.index].path, self.marker_begin,
                                                          self.marker_end)


    def load(self):
        if self.video_list[self.index].marker_begin != "None" and self.video_list[self.index].marker_end != "None":
            self.marker_begin = self.video_list[self.index].marker_begin
            self.marker_end = self.video_list[self.index].marker_end
            self.current_pos = self.marker_begin
        else:
            self.reset()
        print("stop")


    def toggleFileList(self):
        if self.labellist.isHidden():
            self.labellist.show()
        else:
            self.labellist.hide()


    def keyPressEvent(self, e):
        key = e.key()
        print(key)
        self.stop_at_marker_end = False

        # play/pause
        if key == Qt.Key_Space:
            print(self.mediaPlayer.duration())
            self.play()


        # Play from marker begin
        elif key == Qt.Key_E and self.marker_begin != None:
            self.mediaPlayer.setPosition(self.marker_begin)
            if self.marker_end:
                self.stop_at_marker_end = True
            if self.mediaPlayer.state() != QMediaPlayer.PlayingState:
                self.play()

        # Add marker
        elif key == Qt.Key_W:
            if self.marker_begin == None:
                self.marker_begin = self.current_pos
            elif self.marker_end == None:
                if self.current_pos > self.marker_begin:
                    self.marker_end = self.current_pos
                else:
                    self.marker_begin = self.current_pos
            elif self.current_pos < self.marker_begin:
                self.marker_begin = self.current_pos
            elif self.current_pos > self.marker_end:
                self.marker_end = self.current_pos
            else:
                if abs(self.current_pos - self.marker_begin) > abs(self.current_pos - self.marker_end):
                    self.marker_end = self.current_pos
                else:
                    self.marker_begin = self.current_pos


        # Remove all markers
        elif key == Qt.Key_S:
            self.marker_end = None
            self.marker_begin = None

        # Time skipping
        elif key == Qt.Key_Left:
            self.current_pos -= 2000
            self.mediaPlayer.setPosition(self.current_pos)

        elif key == Qt.Key_Right:
            self.current_pos += 2000
            self.mediaPlayer.setPosition(self.current_pos)

        elif key == Qt.Key_D:
            self.save()
            self.labellist.item(self.index).setSelected(False)
            if self.marker_begin and self.marker_end:
                self.labellist.item(self.index).setForeground(Qt.green)
            self.index_next()
            self.reset()
            self.load()
            self.openDefault()
            self.labellist.item(self.index).setSelected(True)

        elif key == Qt.Key_A:
            self.save()
            self.index_prev()
            self.load()
            self.openDefault()

        elif key == Qt.Key_R:
            self.toggleFileList()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    player = VideoWindow()
    player.resize(1080, 700)
    player.show()
    sys.exit(app.exec_())
