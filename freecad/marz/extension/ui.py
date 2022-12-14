# -*- coding: utf-8 -*-
# +---------------------------------------------------------------------------+
# |  Copyright (c) 2020 Frank Martinez <mnesarco at gmail.com>                |
# |                                                                           |
# |  This file is part of Marz Workbench.                                     |
# |                                                                           |
# |  Marz Workbench is free software: you can redistribute it and/or modify   |
# |  it under the terms of the GNU General Public License as published by     |
# |  the Free Software Foundation, either version 3 of the License, or        |
# |  (at your option) any later version.                                      |
# |                                                                           |
# |  Marz Workbench is distributed in the hope that it will be useful,                |
# |  but WITHOUT ANY WARRANTY; without even the implied warranty of           |
# |  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the            |
# |  GNU General Public License for more details.                             |
# |                                                                           |
# |  You should have received a copy of the GNU General Public License        |
# |  along with Marz Workbench.  If not, see <https://www.gnu.org/licenses/>. |
# +---------------------------------------------------------------------------+

import os

from freecad.marz import __version__
from freecad.marz.extension import App, Gui, QtCore, QtGui
from freecad.marz.extension.threading import RunInUIThread

MARZ_WINDOW_LABEL = f"FreeCAD :: Marz Workbench {__version__}"
MARZ_REPOSITORY = "https://github.com/mnesarco/MarzWorkbench/"

MARZ_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
MARZ_RESOURCES_PATH = os.path.join(MARZ_DIR, 'Resources')
MARZ_ICONS_PATH = os.path.join(MARZ_RESOURCES_PATH, 'icons')
MARZ_GRAPHICS_PATH = os.path.join(MARZ_RESOURCES_PATH, 'graphics')

UIGroup_Parts = ('Marz_Group_Parts', 'Instrument Parts')
UIGroup_Imports = ('Marz_Group_Imports', 'Instrument Imports')
UIGroup_Tmp = ('Marz_Group_Tmp', 'tmp')
UIGroup_XLines = ('Marz_Group_Construction', 'Instrument Reference Constructions')

# Ugly workaround to FreeCAD bug on MacOS:
# forum: https://forum.freecadweb.org/viewtopic.php?f=10&t=53713
# issue: https://github.com/FreeCAD/FreeCAD_Conda/issues/26
class MacOSProgressIndicatorWorkaround:
    def __init__(*args, **kwargs):
        pass
    def start(*args, **kwargs):
        pass
    def stop(*args, **kwargs):
        pass

@RunInUIThread
def Msg(text):
    App.Console.PrintMessage(f"[MARZ] {text}\n")


@RunInUIThread
def Log(text):
    App.Console.PrintLog(f"[MARZ] {text}\n")


def StartProgress(msg, n = 0):
    try:
        bar = App.Base.ProgressIndicator()
    except:
        bar = MacOSProgressIndicatorWorkaround()
    bar.start(msg,n)
    return bar


def iconPath(name):
    return os.path.join(MARZ_ICONS_PATH, name)


def graphicsPath(name):
    return os.path.join(MARZ_GRAPHICS_PATH, name)


def resourcePath(name):
    return os.path.join(MARZ_RESOURCES_PATH, name)


def errorDialog(msg, deferred = False):
    if deferred:
        runDeferred(lambda: QtGui.QMessageBox.warning(None, MARZ_WINDOW_LABEL, msg))
    else:
        QtGui.QMessageBox.warning(None, MARZ_WINDOW_LABEL, msg)


def infoDialog(msg, deferred = False):
    if deferred:
        runDeferred(lambda: QtGui.QMessageBox.information(None, MARZ_WINDOW_LABEL, msg))
    else:
        QtGui.QMessageBox.warning(None, MARZ_WINDOW_LABEL, msg)


def confirmDialog(msg):
    r = QtGui.QMessageBox.question(None, MARZ_WINDOW_LABEL, msg,
        QtGui.QMessageBox.Yes | QtGui.QMessageBox.No, QtGui.QMessageBox.Yes)
    return r is QtGui.QMessageBox.StandardButton.Yes


@RunInUIThread
def viewIsometricFit():
    Gui.activeDocument().activeView().viewIsometric()
    Gui.SendMsgToActiveView("ViewFit")


def getBodyName(featureLabel):
    return featureLabel + 'Body'


def getBodyByFeatureName(name):
    feature = App.ActiveDocument.getObject(name)
    if feature is not None:
        return App.ActiveDocument.getObject(getBodyName(feature.Label))
    return None


@RunInUIThread
def runDeferred(block, delay=0):
    QtCore.QTimer.singleShot(delay, block)


@RunInUIThread
def setCheckableActionState(name, state):
    """ Update Checkable Command State (Dirty hack) """
    def fn():
        action = Gui.getMainWindow().findChild(QtGui.QAction, name)
        if action:
            action.blockSignals(True)
            action.setChecked(state)
            action.blockSignals(False)       
    runDeferred(fn)


def getUIGroup(gid = UIGroup_Parts):
    group = App.ActiveDocument.getObject(gid[0])
    if group is None:
        group = App.ActiveDocument.addObject("App::DocumentObjectGroup", gid[0])
        group.Label = gid[1]
    return group


@RunInUIThread
def createPartBody(shape, name, label, fitView = False):
    part = App.ActiveDocument.addObject("Part::Feature", name)
    part.Label = label
    part.Shape = shape
    getUIGroup(UIGroup_Parts).addObject(part)
    if fitView: viewIsometricFit()


@RunInUIThread
def deletePart(part):
    App.ActiveDocument.removeObject(part.Name)


@RunInUIThread
def addOrUpdatePart(shape, name, label=None, visibility=True, group=UIGroup_Parts):
    obj = App.ActiveDocument.getObject(name)
    if obj is None:
        obj = App.ActiveDocument.addObject("Part::Feature", name)
        obj.Label = label or name
        obj.ViewObject.Visibility = visibility
        getUIGroup(group).addObject(obj)
    obj.Shape = shape


@RunInUIThread
def updatePartShape(part, shape):
    part.Shape = shape


@RunInUIThread
def updateDraftPoints(draft, points):
    draft.Points = points


def findDraftByLabel(label):
    r = App.ActiveDocument.getObjectsByLabel(label)
    if r:
        return r[0]


def color(hex_code):
    """
    Color tuple from HEX RGB String

    Args:
        hex_code (string): hex code. ie FF0000

    Returns:
        color (color) : ie (1, 0, 0)
    """
    return int(hex_code[:2], 16) / 256, int(hex_code[2:4], 16) / 256, int(hex_code[4:], 16) / 256

