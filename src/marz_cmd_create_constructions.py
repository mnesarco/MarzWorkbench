# -*- coding: utf-8 -*-
"""
Marz Workbench for FreeCAD 0.19+.
https://github.com/mnesarco/MarzWorkbench
"""

__author__       = "Frank D. Martinez. M."
__copyright__    = "Copyright 2020, Frank D. Martinez. M."
__license__      = "GPLv3"
__maintainer__   = "https://github.com/mnesarco"


import FreeCAD as App
import FreeCADGui as Gui
import marz_ui
import sys
import traceback

from marz_fretboard_feature import FretboardFeature
from marz_instrument_feature import MarzInstrument

class CmdCreateConstructionLines:
    "Command: Create construction lines"

    def GetResources(self):
        return {
            "MenuText": "Create construction lines",
            "ToolTip": "Create construction lines",
            "Pixmap": marz_ui.iconPath('create_constructions.svg')
        }

    def IsActive(self):
        return (
            App.ActiveDocument is not None 
            and App.ActiveDocument.getObject(MarzInstrument.NAME) is not None
        )

    def Activated(self):
        try:
            App.ActiveDocument.getObject(MarzInstrument.NAME).Proxy.createConstructionLines()
        except:
            marz_ui.Msg(traceback.format_exc())

Gui.addCommand('MarzCmdCreateConstructionLines', CmdCreateConstructionLines())
