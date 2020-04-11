# -*- coding: utf-8 -*-
"""
Marz Workbench for FreeCAD 0.19+.
https://github.com/mnesarco/MarzWorkbench
"""

__author__       = "Frank D. Martinez. M."
__copyright__    = "Copyright 2020, Frank D. Martinez. M."
__license__      = "GPLv3"
__maintainer__   = "https://github.com/mnesarco"


import os
import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore, QtGui
from marz_threading import RunInUIThread
import marz_freecad as fc
 
MARZ_VERSION       = "0.0.10-alpha"
MARZ_WINDOW_LABEL  = f"FreeCAD :: Marz Workbench {MARZ_VERSION}"
MARZ_REPOSITORY    = "https://github.com/mnesarco/MarzWorkbench/"

MARZ_DIR = os.path.dirname(__file__)
MARZ_RESOURCES_PATH = os.path.join(MARZ_DIR, 'Resources')
MARZ_ICONS_PATH = os.path.join(MARZ_RESOURCES_PATH, 'icons')
MARZ_GRAPHICS_PATH = os.path.join(MARZ_RESOURCES_PATH, 'graphics')

@RunInUIThread
def Msg(text):
    App.Console.PrintMessage(f"[MARZ] {text}\n")

@RunInUIThread
def Log(text):
    App.Console.PrintLog(f"[MARZ] {text}\n")

def StartProgress(msg, n = 0):
    bar = App.Base.ProgressIndicator()
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
def featureToBody(feature, name = None):
    body = App.activeDocument().addObject('PartDesign::Body', name or getBodyName(feature.Label))

    Gui.activateView('Gui::View3DInventor', True)
    Gui.activeView().setActiveObject('pdbody', body)
    Gui.Selection.clearSelection()
    Gui.Selection.addSelection(body)

    if fc.isVersion19():
        feature.adjustRelativeLinks(body)
        body.ViewObject.dropObject(feature,None,'',[])
    elif fc.isVersion18():
        body.BaseFeature = feature
        
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

@RunInUIThread
def createPartBody(shape, name, label, fitView = False):
    part = App.ActiveDocument.addObject("Part::Feature", name)
    part.Label = label
    part.Shape = shape
    featureToBody(part)
    if fitView: viewIsometricFit()

@RunInUIThread
def updatePartShape(part, shape):
    part.Shape = shape

@RunInUIThread
def recomputeActiveDocument(fitView = False):
    App.ActiveDocument.recompute()
    if fitView: viewIsometricFit()

@RunInUIThread
def updateDraftPoints(draft, points):
    draft.Points = points

def findDraftByLabel(label):
    r = App.ActiveDocument.getObjectsByLabel(label)
    if r: return r[0]

def color(hex):
    """
    Color tuple from HEX RGB String

    Args:
        hex (string): hex code. ie FF0000

    Returns:
        color (color) : ie (1, 0, 0)
    """
    return (int(hex[:2],16)/256, int(hex[2:4],16)/256, int(hex[4:],16)/256)

