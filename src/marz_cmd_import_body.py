# -*- coding: utf-8 -*-
"""
Marz Workbench for FreeCAD 0.19+.
https://github.com/mnesarco/MarzWorkbench
"""

__author__       = "Frank D. Martinez. M."
__copyright__    = "Copyright 2020, Frank D. Martinez. M."
__license__      = "GPLv3"
__maintainer__   = "https://github.com/mnesarco"


import sys
import traceback
import os

import FreeCAD as App
import FreeCADGui as Gui
import marz_ui
from marz_instrument_feature import MarzInstrument

class CmdImportBodyShape:
    "Import body shape from svg Command"

    def GetResources(self):
        return {
            "MenuText": "Import body shape svg",
            "ToolTip": "Import body shape svg",
            "Pixmap": marz_ui.iconPath('import_body_shape.svg')
        }

    def IsActive(self):
        return (
            App.ActiveDocument is not None 
            and App.ActiveDocument.getObject(MarzInstrument.NAME) is not None
        )

    def Activated(self):
        from PySide import QtGui
        try:
            name = QtGui.QFileDialog.getOpenFileName(QtGui.QApplication.activeWindow(), 'Select .svg file', '*.svg')[0]
            if name:
                App.ActiveDocument.getObject(MarzInstrument.NAME).Proxy.importBodyShape(name)
        except:
            marz_ui.Msg(traceback.format_exc())

Gui.addCommand('MarzCmdImportBodyShape', CmdImportBodyShape())
