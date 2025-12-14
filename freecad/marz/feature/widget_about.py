# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileNotice: Part of the Marz addon.

################################################################################
#                                                                              #
#   Copyright (c) 2020 Frank David Martínez Muñoz <mnesarco at gmail.com>      #
#                                                                              #
#   This program is free software: you can redistribute it and / or            #
#   modify it under the terms of the GNU General Public License as             #
#   published by the Free Software Foundation, either version 3 of             #
#   the License, or (at your option) any later version.                        #
#                                                                              #
#   This program is distributed in the hope that it will be useful,            #
#   but WITHOUT ANY WARRANTY; without even the implied warranty of             #
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.                       #
#                                                                              #
#   See the GNU General Public License for more details.                       #
#                                                                              #
#   You should have received a copy of the GNU General Public License          #
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.      #
#                                                                              #
################################################################################

from freecad.marz import __author__, __version__, __copyright__
from freecad.marz.extension import paths
from freecad.marz.extension.fc import Gui
from freecad.marz.extension.qt import QtGui, QtCore


class MarzAboutWindow(QtGui.QDialog):

    def __init__(self, frame=True, timeout=False):
        super().__init__(Gui.getMainWindow())
        self.frame = frame
        self.timeout = timeout
        self.initUI()

    def initUI(self):

        # Window
        try:
            sg = QtGui.QDesktopWidget().screenGeometry()
        except Exception:
            sg = QtGui.QGuiApplication.primaryScreen().availableGeometry()
        screenWidth = sg.width()
        screenHeight = sg.height()
        height = 350
        width = height * 1.61803398875
        self.setGeometry((screenWidth-width)/2, (screenHeight-height)/2, width, height)
        self.setWindowTitle(f"FreeCAD :: Marz Workbench {__version__}")
        if not self.frame:
            self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.setFixedSize(self.size())

        # Layout
        layout = QtGui.QStackedLayout(self)
        layout.setAlignment(QtCore.Qt.AlignBottom)
        self.setLayout(layout)

        # Content
        content = QtGui.QLabel(self)
        content.setTextInteractionFlags(QtCore.Qt.TextBrowserInteraction)
        content.setOpenExternalLinks(True)
        content.setText(f"""<p>
            A FreeCAD Workbench for Guitar design. Version {__version__}
            <br/><a href="https://github.com/mnesarco/MarzWorkbench/" style="color: #0088AA;">https://github.com/mnesarco/MarzWorkbench</a>
            <br/>Author: {__author__}
            <br/>{__copyright__}
            <br />All Rights Reserved.
            </p>
        """)
        content.setAlignment(QtCore.Qt.AlignBottom | QtCore.Qt.AlignCenter)
        backgroundImage = paths.graphicsPath('logo.svg').replace('\\', '/') # Fix for windows paths
        content.setStyleSheet(f"""
            color: #eeeeee;
            font-size: 12px;
            background-color: #101010;
            background: url("{backgroundImage}") no-repeat center top fixed;
            padding: 260px 10px 10px 10px;
        """)
        layout.addWidget(content)

        # Timer
        if self.timeout:
            QtCore.QTimer.singleShot(self.timeout, self.close)

        self.show()

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.close()

    @classmethod
    def execute(cls, frame=True, timeout=None):
        MarzAboutWindow(frame, timeout).show()
