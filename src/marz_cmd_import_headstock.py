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
from FreeCAD import Vector
import marz_ui
from marz_instrument_feature import MarzInstrument
import marz_utils
from marz_import_svg import extractCustomShape

class CmdImportHeadstockShape:
    "Import body shape from svg Command"

    def GetResources(self):
        return {
            "MenuText": "Import headstock shape svg",
            "ToolTip": "Import headstock shape svg",
            "Pixmap": marz_ui.iconPath('import_headstock_shape.svg')
        }

    def IsActive(self):
        return (
            App.ActiveDocument is not None 
            and App.ActiveDocument.getObject(MarzInstrument.NAME) is not None
        )

    def Activated(self):
        from PySide import QtGui
        try:
            name = QtGui.QFileDialog.getOpenFileName(QtGui.QApplication.activeWindow(),'Select .svg file','*.svg')[0]
            if name:
                extractCustomShape(name, 'Marz_Headstock')
        except:
            marz_ui.Msg(traceback.format_exc())

Gui.addCommand('MarzCmdImportHeadstockShape', CmdImportHeadstockShape())
