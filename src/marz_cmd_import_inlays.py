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

class CmdImportFretInlays:
    "Import custom Fret Inlays from SVG Command"

    def GetResources(self):
        return {
            "MenuText": "Import fret inlays svg",
            "ToolTip": "Import fret inlays svg",
            "Pixmap": marz_ui.iconPath('import_fret_inlays.svg')
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
                App.ActiveDocument.getObject(MarzInstrument.NAME).Proxy.importInlays(name)
        except:
            marz_ui.Msg(traceback.format_exc())

Gui.addCommand('MarzCmdImportFretInlays', CmdImportFretInlays())
