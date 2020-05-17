# Author: Jacob Jon Hansen
# !/usr/bin/env python
import pickle
import numpy as np
import ffmpeg
from PyQt5.QtCore import QDir, Qt, QUrl
from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtWidgets import *
from PyQt5.QtWidgets import QMainWindow, QWidget, QPushButton, QAction
from PyQt5.QtGui import *
from PyQt5.QtCore import QTimer
from PyQt5 import QtCore
from pathlib import Path
import sys
import os
import time
import glob
from collections import namedtuple

video_container = namedtuple('video_container', ['path', 'marker_begin', 'marker_end', 'saved_markers'], )

class List(QListWidget):
    def __init__(self):
        QListWidget.__init__(self)
        #self.itemClicked.connect(self.test)
        #super(List, self).__init__(parent)


    def keyPressEvent(self, event):
        self.parent().keyPressEvent(event)

    def mousePressEvent(self, event):
        print("YO PRESSED")
        print(event.pos())
        self.parent().mousePressEvent(event)

    def itemClicked(self, event):
        print("YO ITEM WAS PRESSED")


class VideoWindow(QMainWindow):

    def __init__(self, parent=None):
        super(VideoWindow, self).__init__(parent)

        # Variables ########################
        self.marker_begin = None
        self.marker_end = None
        self.saved_markers = []
        self.current_pos = 0
        self.mouse_button_down = False

        # Stop playing when reaching marker end?
        self.stop_at_marker_end = False

        # Settings
        self.include_subdirs = False


        # Which video are currently playing
        self.index = 0
        ###################################

        # PyQt
        self.setWindowTitle("Play Extractor")


        self.mediaPlayer = QMediaPlayer(None, QMediaPlayer.VideoSurface)

        self.videoWidget = QVideoWidget()
        self.videoWidget.setMouseTracking(True)
        self.videoWidget.installEventFilter(self)

        self.errorLabel = QLabel()
        self.errorLabel.setSizePolicy(QSizePolicy.Preferred,
                                      QSizePolicy.Maximum)

        # Create new action
        openAction = QAction(QIcon('icons/file.png'), '&Open', self)
        openAction.setShortcut('Ctrl+O')
        openAction.setStatusTip('Open movie')
        openAction.triggered.connect(self.openFile)

        # Create new action
        openDirAction = QAction(QIcon('icons/folder.png'), '&OpenDir', self)
        openDirAction.setShortcut('Ctrl+Shift+O')
        openDirAction.setStatusTip('Open Directory')
        openDirAction.triggered.connect(self.openDir)

        exportAction = QAction(QIcon('icons/play.png'), '&Export', self)
        exportAction.setShortcut('Ctrl+E')
        exportAction.setStatusTip('Export Files')
        exportAction.triggered.connect(self.convertToMp4)

        # Create exit action
        exitAction = QAction(QIcon('icons/cancel.png'), '&Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Exit application')
        exitAction.triggered.connect(self.exitCall)

        # Create settings actions
        settingsAction = QAction(QIcon('icons/settings.png'), '&Settings', self)
        settingsAction.setShortcut('Ctrl+P')
        settingsAction.setStatusTip("Settings")
        settingsAction.triggered.connect(self.settings)

        # Create menu bar and add action
        menuBar = self.menuBar()
        fileMenu = menuBar.addMenu('&File')
        fileMenu.addAction(openAction)
        fileMenu.addAction(openDirAction)
        fileMenu.addAction(exportAction)
        fileMenu.addAction(settingsAction)
        fileMenu.addAction(exitAction)

        # Create a widget for window contents
        wid = QWidget(self)
        self.setCentralWidget(wid)


        # Create layouts to place inside widget
        controlLayout = QHBoxLayout()
        controlLayout.setContentsMargins(0, 0, 0, 0)
        self.label = QLabel(self)
        controlLayout.addWidget(self.label)

        #List
        listlayout = QHBoxLayout()
        listlayout.setContentsMargins(0, 0, 0, 0)
        self.labellist = List()
        self.labellist.mousePressEvent = self.selectVidFromList
        listlayout.addWidget(self.labellist)


        
        #if os.path.isfile(".last_session.pickle"):
        if False:
            self.video_list = pickle.load( open( ".last_session.pickle", "rb" ) )
            # Load videos into the the side list view
            for vid in self.video_list:
                imgPath = vid.path
                item = QListWidgetItem(imgPath.split("/")[-1].split(".")[0])
                self.labellist.addItem(item)

        else:
            #Open the play_extractor folder
            #self.loadVideos("/home/jake/dev/play_extractor")
            pass

        #self.labellist.item(0).setSelected(True)
        #self.labellist.itemClicked.connect(self.itemActivated)

        layout = QVBoxLayout()
        layout.addWidget(self.videoWidget)
        layout.addLayout(controlLayout)
        layout.setStretchFactor(self.videoWidget, 20)
        layout.setStretchFactor(controlLayout, 1)
        layout.addWidget(self.errorLabel)

        top = QHBoxLayout()
        top.setContentsMargins(0, 0, 10, 0)
        top.addLayout(listlayout)
        top.addLayout(layout)
        top.setStretchFactor(listlayout, 1)
        top.setStretchFactor(layout, 5)
        # Set widget to contain window contents
        wid.setLayout(top)

        self.mediaPlayer.setVideoOutput(self.videoWidget)
        #self.mediaPlayer.positionChanged.connect(self.positionChanged)
        #self.mediaPlayer.durationChanged.connect(self.durationChanged)
        self.mediaPlayer.error.connect(self.handleError)

        #self.loadVidIndex(self.index)

        self.qTimer = QTimer()
        # set interval to 1 s
        self.qTimer.setInterval(20)  # 1000 ms = 1 s
        # connect timeout signal to signal handler
        self.qTimer.timeout.connect(self.getSensorValue)
        # start timer
        self.qTimer.start()

    def selectVidFromList(self, event):
        itemat =  self.labellist.itemAt(event.pos())
        row = self.labellist.row(itemat)
        if row != -1: 
            self.loadVidIndex(row)
        

    def itemActivated(self, item):
        index = self.labellist.currentRow()
        self.loadVidIndex(index)

    def settings(self):
        raise NotImplementedError

    def loadVideos(self, path):
        self.mImgList = self.scanDir(path)
        self.video_list = []
        self.labellist.clear()
        for imgPath in self.mImgList:
            self.video_list.append(video_container(imgPath, "None", "None", []))
            item = QListWidgetItem(os.path.split(imgPath)[1])
            self.labellist.addItem(item)
        if(len(self.video_list) > 0):
            self.loadVidIndex(0)

    def scanAllDirs(self, folderPath):
        images = []
        extensions = [".mp4"]

        for root, dirs, files in os.walk(folderPath):
            for file in files:
                if file.lower().endswith(tuple(extensions)):
                    relativePath = os.path.join(root, file)
                    path = str(os.path.abspath(relativePath))
                    images.append(path)
        return images

    def scanDir(self, folderPath):
        files = os.path.join(folderPath, '*.mp4')
        files = glob.glob(files)
        print(files)
        return files

    def time_to_x(self, timepoint):
        return int(timepoint / self.mediaPlayer.duration() * self.videoWidget.width())

    def clipArea(self, marker_begin, position):
        # Clip the box so it doesn't overlap with previous clips
        if self.saved_markers:
            if position > marker_begin:
                beginning_markers = [x[0] for x in self.saved_markers]
                beginning_markers.append(position)
                beginning_markers = np.array(beginning_markers)
                beginning_markers = beginning_markers[beginning_markers > marker_begin]
                return(np.min(beginning_markers))
            else:
                ending_markers = np.array([x[1] for x in self.saved_markers].append(position))
                ending_markers = ending_markers[ending_markers < marker_begin]
                return(np.max(ending_markers))
        else:
            return position

    def updateImage(self, position=0):
        width = self.label.width()
        pixmap = QPixmap(width, 50)
        pixmap.fill(Qt.gray)

        painter = QPainter()
        painter.begin(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(Qt.black, 1))

        # Draw markers and bars
        markerwidth = 10    
        try:
            for saved_marker in self.saved_markers:
                sm_begin, sm_end = saved_marker
                bar_width = self.time_to_x(sm_end - sm_begin)
                painter.setBrush(QBrush(Qt.yellow, Qt.SolidPattern))
                painter.drawRect(self.time_to_x(sm_begin), 0, bar_width, 50)
            
            if self.marker_begin:
                markerpos = self.time_to_x(self.marker_begin)
                if self.marker_end:
                    bar_width = self.time_to_x(self.marker_end) - markerpos
                elif markerpos < self.time_to_x(self.current_pos):
                    bar_width = self.time_to_x(self.clipArea(self.marker_begin, self.current_pos)) - markerpos
                else:
                    bar_width = 0
                painter.setBrush(QBrush(Qt.blue, Qt.SolidPattern))
                painter.drawRect(markerpos, 0, bar_width, 50)

                if self.marker_end:
                    if self.current_pos > self.marker_end:
                        painter.setBrush(QBrush(QColor(171, 255, 158), Qt.SolidPattern))
                        bar_width = self.time_to_x(self.clipArea(self.marker_begin, self.current_pos) - self.marker_end)
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
                    painter.drawRect(min(markerpos, width - markerwidth), 0, markerwidth, 50)
        
        except Exception as e:
            print(e)

        # Draw video playback marker
        painter.setBrush(QBrush(Qt.white, Qt.SolidPattern))
        painter.drawRect(min(position, width - markerwidth), 0, markerwidth, 50)
        painter.end()
        pixmap.scaled(width, 50)
        self.label.setMinimumSize(1, 50)
        self.label.setPixmap(pixmap)
        self.label.setScaledContents(True)


    def eventFilter(self, source, event):
        if event.type() == QtCore.QEvent.MouseButtonPress:
            if event.button() == QtCore.Qt.LeftButton:
                self.mouse_button_down = True
                self.current_pos = int(event.x() / self.videoWidget.geometry().width() * self.mediaPlayer.duration())
                self.mediaPlayer.setPosition(self.current_pos)
                self.updateImage(event.x())
            elif event.button() == QtCore.Qt.RightButton:
                self.addMarker()
        elif event.type() == QtCore.QEvent.MouseButtonRelease:
            self.mouse_button_down = False
        elif event.type() == QtCore.QEvent.MouseMove and self.mouse_button_down:
            self.current_pos = int(event.x() / self.videoWidget.geometry().width() * self.mediaPlayer.duration())
            self.mediaPlayer.setPosition(self.current_pos)
            self.updateImage(event.x())


        # if event.type() == QtCore.QEvent.MouseMove:
        # elif event.type() == QtCore.QEvent.MouseButtonPress or event.type() == QtCore.QEvent.MouseButtonRelease:
        #     self.addMarker()
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


    def openDefault(self):
        fileName = self.video_list[self.index].path
        self.mediaPlayer.setMedia(
            QMediaContent(QUrl.fromLocalFile(fileName)))
        self.play()
        self.play()
        self.mediaPlayer.setPosition(self.current_pos)
        self.updateImage()


    def openDir(self):
        targetDirPath = (str(QFileDialog.getExistingDirectory(self, "Select Directory", ".")))
        self.loadVideos(targetDirPath)


    def exitCall(self):
        sys.exit(app.exec_())


    def play(self):
        if self.mediaPlayer.state() == QMediaPlayer.PlayingState:
            self.mediaPlayer.pause()
        else:
            self.mediaPlayer.play()


    def setPosition(self, position):
        self.mediaPlayer.setPosition(position)


    def handleError(self):
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
                                                          self.marker_end, self.saved_markers)

        #Save the video list to a file
        pickle.dump(self.video_list, open( ".last_session.pickle", "wb" ))

    def delete_marker(self):
        self.video_list[self.index] = self.video_list[self.index]._replace(marker_begin = "None", marker_end = "None")
        self.marker_end = None
        self.marker_begin = None


    def load(self):
        if self.video_list[self.index].marker_begin != "None" and self.video_list[self.index].marker_end != "None":
            print("loading")
            self.marker_begin = self.video_list[self.index].marker_begin
            self.marker_end = self.video_list[self.index].marker_end
            self.current_pos = self.marker_begin
            self.saved_markers = self.video_list[self.index].saved_markers
        else:
            self.reset()

    def nextVid(self):
        self.save()
        self.labellist.item(self.index).setSelected(False)
        if self.marker_begin and self.marker_end:
            self.labellist.item(self.index).setForeground(Qt.green)
        self.index_next()
        self.reset()
        self.load()
        self.openDefault()
        self.labellist.item(self.index).setSelected(True)


    def previousVid(self):
        self.save()
        self.labellist.item(self.index).setSelected(False)
        if self.marker_begin and self.marker_end:
            self.labellist.item(self.index).setForeground(Qt.green)
        self.index_prev()
        self.reset()
        self.load()
        self.openDefault()
        self.labellist.item(self.index).setSelected(True)


    def loadVidIndex(self, index):
        self.save()
        self.labellist.item(self.index).setSelected(False)
        if self.marker_begin and self.marker_end:
            self.labellist.item(self.index).setForeground(Qt.green)
        self.index = index
        self.reset()
        self.load()
        self.openDefault()
        self.labellist.item(self.index).setSelected(True)


    def toggleFileList(self):
        if self.labellist.isHidden():
            self.labellist.show()
        else:
            self.labellist.hide()

    def overlapsWithSavedClips(self, position):
        for saved_marker in self.saved_markers:
            if position > saved_marker[0] and position <= saved_marker[1]:
                return True
            if self.marker_begin != None:
                if self.marker_begin < saved_marker[0] and (position > saved_marker[0]):
                    return True 
                
        return False


    def convertToMp4(self):
        for video in self.video_list:
            if video.marker_begin != "None" and video.marker_end != "None":
                input_kwargs = {}
                start_time = video.marker_begin / 1000
                end_time = video.marker_end / 1000

                if start_time is not None:
                    input_kwargs['ss'] = start_time
                else:
                    start_time = 0.
                if end_time is not None:
                    input_kwargs['t'] = end_time - start_time

                output_path = os.path.split(video.path)[0] + "/output"
                Path(output_path).mkdir(parents=True, exist_ok=True)
                print(video.path)
                stream = ffmpeg.input(video.path, **input_kwargs)
                stream = ffmpeg.output(stream, output_path + '/{}.mp4'.format(os.path.split(video.path)[1]))
                ffmpeg.run(stream)
        

    def showShortcuts(self):
        MsgBox = QMessageBox()
        MsgBox.setText("<b>Shortcuts</b><br><br>"
                       "<b>mouse hover</b>: scrub <br>"
                       "<b>space</b>: play/pause <br>"
                       "<b>d</b>: next video <br>"
                       "<b>a</b>: previous video <br> "
                       "<b>w</b>: place marker <br>"
                       "<b>s</b>: delete selection <br>"
                       "<b>p</b>: play from first marker <br>")
        MsgBox.exec()
        #MsgBox.about(self, "Title", "Message")

    def addMarker(self):
        if not self.overlapsWithSavedClips(self.current_pos):
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

            if self.marker_begin and self.marker_end:
                self.save()


    def keyPressEvent(self, e):
        key = e.key()
        self.stop_at_marker_end = False

        # play/pause
        if key == Qt.Key_Space:
            self.play()
            print(self.mediaPlayer.PlayingState)


        # Play from marker begin
        elif key == Qt.Key_E and self.marker_begin != None:
            self.mediaPlayer.setPosition(self.marker_begin)
            if self.marker_end:
                self.stop_at_marker_end = True
            if self.mediaPlayer.state() != QMediaPlayer.PlayingState:
                self.play()

        # Add marker
        elif key == Qt.Key_W:
            self.addMarker()


        # Remove all markers
        elif key == Qt.Key_S:
            self.delete_marker()

        # elif key == Qt.Key_Q:
        #     if self.marker_begin != None and self.marker_end != None:
        #         self.saved_markers.append([self.marker_begin, self.marker_end])
        #     self.delete_marker()

        # Time skipping
        elif key == Qt.Key_Left:
            # Scrub right N miliseconds
            self.current_pos -= 30
            self.mediaPlayer.setPosition(self.current_pos)

        elif key == Qt.Key_Right:
            self.current_pos += 30
            self.mediaPlayer.setPosition(self.current_pos)

        elif key == Qt.Key_D:
            self.nextVid()

        elif key == Qt.Key_A:
            self.previousVid()

        elif key == Qt.Key_R:
            self.toggleFileList()

        elif key == Qt.Key_J:
            self.convertToMp4()

        elif key == Qt.Key_T:
            self.showShortcuts()



if __name__ == '__main__':
    import time
    app = QApplication(sys.argv)
    player = VideoWindow()
    player.resize(1080, 700)
    player.show()
    sys.exit(app.exec_())
